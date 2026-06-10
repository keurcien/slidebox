"""Sanity checks: the public API surface is present."""

from __future__ import annotations

import slidebox


def test_public_api_exports() -> None:
    for name in (
        "Deck",
        "Slide",
        "BrandTheme",
        "render",
        "save",
        "to_google_slides",
        "GoogleSlides",
    ):
        assert hasattr(slidebox, name), name
