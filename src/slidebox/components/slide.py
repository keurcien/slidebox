"""Slide — the page-level container.

Every slide has its own coordinate space (the canvas). Direct children
laid out inside a Slide are positioned relative to the canvas
origin (top-left).
"""

from __future__ import annotations

from typing import ClassVar, Literal

from slidebox.components.base import ContainerComponent
from slidebox.units import Length

SlideLayout = Literal[
    "BLANK",
    "TITLE",
    "TITLE_AND_BODY",
    "SECTION_HEADER",
    "TITLE_AND_TWO_COLUMNS",
]


class Slide(ContainerComponent):
    """One page in the presentation.

    Args:
        layout: Google-provided layout preset. Defaults to "BLANK", which
            gives us full control over positioning.
        background: Optional hex colour for the slide background.
        padding: Space between slide edge and its direct children (EMU).
    """

    kind: ClassVar[str] = "slide"

    layout: SlideLayout = "BLANK"
    background: str | None = None
    padding: Length | tuple[Length, ...] | None = None
