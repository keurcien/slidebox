"""Read and normalise a live Google Slides presentation.

Google's `presentations.get` returns a deeply nested dict. We flatten
the bits we actually need — per-element `objectId`, type, bounds, and
alt-text — so the Updater can make O(1) lookups.

Every `LiveDeck` instance records when it was fetched. Structural
changes (replace-element) always re-fetch immediately before dispatch
so user edits in the Slides UI don't get stomped.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from slidebox.geometry import Bounds

if TYPE_CHECKING:
    from slidebox.client.slides_client import SlidesClient


@dataclass
class LiveElement:
    object_id: str
    kind: str  # 'shape' | 'image' | 'video' | 'table' | 'line' | 'group'
    bounds: Bounds | None
    alt_title: str | None
    alt_description: str | None
    page_object_id: str | None


@dataclass
class LiveDeck:
    presentation_id: str
    fetched_at: float
    elements: dict[str, LiveElement] = field(default_factory=dict)
    slide_ids: list[str] = field(default_factory=list)

    def element(self, object_id: str) -> LiveElement | None:
        return self.elements.get(object_id)

    def element_bounds(self, object_id: str) -> Bounds | None:
        el = self.elements.get(object_id)
        return el.bounds if el else None

    def element_kind(self, object_id: str) -> str | None:
        el = self.elements.get(object_id)
        return el.kind if el else None


def fetch_presentation(client: SlidesClient, presentation_id: str) -> LiveDeck:
    raw = client.get_presentation(presentation_id)
    deck = LiveDeck(presentation_id=presentation_id, fetched_at=time.time())

    for page in raw.get("slides", []):
        slide_id = page.get("objectId")
        if slide_id:
            deck.slide_ids.append(slide_id)
        for element in page.get("pageElements", []):
            _ingest_element(element, slide_id, deck)
    return deck


def _ingest_element(element: dict[str, Any], slide_id: str | None, deck: LiveDeck) -> None:
    oid = element.get("objectId")
    if not oid:
        return

    kind = _detect_kind(element)
    bounds = _extract_bounds(element)
    title = element.get("title")
    description = element.get("description")

    deck.elements[oid] = LiveElement(
        object_id=oid,
        kind=kind,
        bounds=bounds,
        alt_title=title,
        alt_description=description,
        page_object_id=slide_id,
    )

    # Recurse into groups.
    for child in element.get("elementGroup", {}).get("children", []) or []:
        _ingest_element(child, slide_id, deck)


def _detect_kind(element: dict[str, Any]) -> str:
    for k in ("shape", "image", "video", "table", "line", "sheetsChart", "wordArt", "elementGroup"):
        if k in element:
            return k
    return "unknown"


def _extract_bounds(element: dict[str, Any]) -> Bounds | None:
    size = element.get("size") or {}
    transform = element.get("transform") or {}
    try:
        w = int(size["width"]["magnitude"])
        h = int(size["height"]["magnitude"])
    except (KeyError, TypeError, ValueError):
        return None

    # Size is reported in the unit Google chose (usually EMU); transform
    # contains scaleX/scaleY + translateX/translateY. We take the product
    # of size × scale to get effective bounds, and ignore any shear.
    scale_x = float(transform.get("scaleX", 1.0))
    scale_y = float(transform.get("scaleY", 1.0))
    tx = int(transform.get("translateX", 0))
    ty = int(transform.get("translateY", 0))
    return Bounds(x=tx, y=ty, w=int(w * scale_x), h=int(h * scale_y))
