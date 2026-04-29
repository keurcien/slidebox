"""Typed builders for Google Slides API batchUpdate requests.

Each function returns the exact dict shape Google expects. Keeping the
construction in one place gives us:
  - A single point to validate inputs before a round trip.
  - A place to apply the `raw=` escape hatch (deep-merged into the
    appropriate sub-structure).
  - A cleaner `Compiler` that reads like an intent, not like API plumbing.
"""

from __future__ import annotations

from typing import Any

from slidebox.geometry import Bounds


def create_slide(object_id: str, *, insertion_index: int, layout: str = "BLANK") -> dict[str, Any]:
    return {
        "createSlide": {
            "objectId": object_id,
            "insertionIndex": insertion_index,
            "slideLayoutReference": {"predefinedLayout": layout},
        }
    }


def create_shape(
    object_id: str,
    *,
    page_id: str,
    shape_type: str,
    bounds: Bounds,
) -> dict[str, Any]:
    return {
        "createShape": {
            "objectId": object_id,
            "shapeType": shape_type,
            "elementProperties": {
                "pageObjectId": page_id,
                **bounds.to_api_transform(),
            },
        }
    }


def create_image(object_id: str, *, page_id: str, url: str, bounds: Bounds) -> dict[str, Any]:
    return {
        "createImage": {
            "objectId": object_id,
            "url": url,
            "elementProperties": {
                "pageObjectId": page_id,
                **bounds.to_api_transform(),
            },
        }
    }


def insert_text(object_id: str, text: str, *, insertion_index: int = 0) -> dict[str, Any]:
    return {
        "insertText": {
            "objectId": object_id,
            "text": text,
            "insertionIndex": insertion_index,
        }
    }


def update_text_style(
    object_id: str,
    *,
    style: dict[str, Any],
    fields: str,
    text_range: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = {
        "objectId": object_id,
        "style": style,
        "fields": fields,
        "textRange": text_range or {"type": "ALL"},
    }
    return {"updateTextStyle": body}


def update_paragraph_style(
    object_id: str,
    *,
    style: dict[str, Any],
    fields: str,
) -> dict[str, Any]:
    return {
        "updateParagraphStyle": {
            "objectId": object_id,
            "style": style,
            "fields": fields,
            "textRange": {"type": "ALL"},
        }
    }


def update_shape_properties(
    object_id: str,
    *,
    properties: dict[str, Any],
    fields: str,
) -> dict[str, Any]:
    return {
        "updateShapeProperties": {
            "objectId": object_id,
            "shapeProperties": properties,
            "fields": fields,
        }
    }


def update_page_properties(
    object_id: str,
    *,
    properties: dict[str, Any],
    fields: str,
) -> dict[str, Any]:
    return {
        "updatePageProperties": {
            "objectId": object_id,
            "pageProperties": properties,
            "fields": fields,
        }
    }


def update_alt_text(
    object_id: str, *, title: str | None = None, description: str | None = None
) -> dict[str, Any]:
    return {
        "updatePageElementAltText": {
            "objectId": object_id,
            "title": title or "",
            "description": description or "",
        }
    }


def delete_object(object_id: str) -> dict[str, Any]:
    return {"deleteObject": {"objectId": object_id}}


def delete_text(object_id: str) -> dict[str, Any]:
    return {
        "deleteText": {
            "objectId": object_id,
            "textRange": {"type": "ALL"},
        }
    }


def replace_image(object_id: str, url: str) -> dict[str, Any]:
    return {
        "replaceImage": {
            "imageObjectId": object_id,
            "url": url,
            "imageReplaceMethod": "CENTER_INSIDE",
        }
    }


# ── colour helpers ────────────────────────────────────────────────────

def hex_to_rgb(value: str) -> dict[str, float]:
    """Convert '#rrggbb' (or 'rrggbb') to Google's OpaqueColor RGB dict."""
    s = value.lstrip("#")
    if len(s) != 6:
        raise ValueError(f"invalid hex colour: {value!r}")
    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return {"red": r / 255.0, "green": g / 255.0, "blue": b / 255.0}


def solid_fill(hex_color: str) -> dict[str, Any]:
    """Return a `SolidFill` payload for shape/page backgrounds."""
    return {
        "solidFill": {
            "color": {"rgbColor": hex_to_rgb(hex_color)},
            "alpha": 1,
        }
    }
