"""Encode component metadata into Google Slides' alt-text field.

Google's alt-text `title` and `description` fields round-trip through
the UI and survive manual user edits. We encode slidebox-origin data
there so `Updater` (or any future tool) can identify elements by their
semantic origin, not just by position.

Format:
    <alt text>   ->  slidebox:v1:<type>:<base64-json>

If metadata would push past Google's 4KB limit, we drop the payload
but keep the `slidebox:v1:<type>` marker so the element is still
identifiable.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

log = logging.getLogger(__name__)

_MAX_BYTES = 4000  # Google's documented limit on element alt text
_PREFIX = "slidebox:v1"


def encode_metadata(component_type: str, metadata: dict[str, Any] | None) -> str:
    """Return a compact identity string suitable for the alt-text field."""
    if not metadata:
        return f"{_PREFIX}:{component_type}:"
    try:
        payload = json.dumps(metadata, separators=(",", ":"), sort_keys=True)
        encoded = base64.urlsafe_b64encode(payload.encode()).decode()
    except (TypeError, ValueError) as exc:
        log.warning("dropping unserialisable metadata for %s: %s", component_type, exc)
        return f"{_PREFIX}:{component_type}:"

    marker = f"{_PREFIX}:{component_type}:{encoded}"
    if len(marker.encode()) > _MAX_BYTES:
        log.warning(
            "metadata for %s is %d bytes (> %d); dropping payload, keeping marker",
            component_type,
            len(marker.encode()),
            _MAX_BYTES,
        )
        return f"{_PREFIX}:{component_type}:"
    return marker


def decode_metadata(alt_text: str | None) -> tuple[str, dict[str, Any]] | None:
    """Inverse of `encode_metadata`. Returns (type, metadata) or None."""
    if not alt_text or not alt_text.startswith(_PREFIX + ":"):
        return None
    parts = alt_text.split(":", 3)
    if len(parts) < 4:
        return None
    component_type = parts[2]
    encoded = parts[3]
    if not encoded:
        return component_type, {}
    try:
        decoded = base64.urlsafe_b64decode(encoded).decode()
        meta = json.loads(decoded)
        return component_type, meta
    except (ValueError, json.JSONDecodeError):
        return component_type, {}
