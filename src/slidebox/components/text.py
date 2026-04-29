"""Text components.

`Text` is the single primitive for glyphs on a slide. `Title`,
`Subtitle`, and `Heading` are thin subclasses that set a default
`style` — the theme resolves the style name to concrete font size,
weight, and colour.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from slidebox.components.base import LeafComponent
from slidebox.units import Length

TextStyle = Literal["h1", "h2", "h3", "body", "caption", "subtitle"]
TextAlign = Literal["start", "center", "end", "justify"]


class Text(LeafComponent):
    """A block of text that fills its container.

    Args:
        content: The string to display.
        style: Named style key looked up in the active theme.
        color: Overrides the theme colour. Hex string like "#111".
        bg: Shape background fill behind the text.
        size: Font size override, in points (EMU accepted).
        font: Font family override.
        bold, italic, underline: Toggle corresponding text style.
        align: Paragraph alignment.
        shrink_on_overflow: Map to Google's `SHRINK_ON_OVERFLOW` TextAutoFit
            so long strings reduce font size rather than clipping.
    """

    kind: ClassVar[str] = "text"

    content: str
    style: TextStyle = "body"
    color: str | None = None
    bg: str | None = Field(default=None, alias="background")
    size: Length | None = None
    font: str | None = Field(default=None, alias="font_family")
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    align: TextAlign | None = None
    shrink_on_overflow: bool = False

    def __init__(self, content: str = "", /, **kwargs: object) -> None:
        super().__init__(content=content, **kwargs)


class Title(Text):
    """Shortcut for `Text(style='h1')`."""

    kind: ClassVar[str] = "title"
    style: TextStyle = "h1"


class Subtitle(Text):
    kind: ClassVar[str] = "subtitle"
    style: TextStyle = "subtitle"


class Heading(Text):
    """Shortcut for `Text(style='h2')`."""

    kind: ClassVar[str] = "heading"
    style: TextStyle = "h2"
