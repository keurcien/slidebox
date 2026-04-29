"""slidebox — declarative Google Slides generator.

    from slidebox import Presentation, Slide, Title, Text

    with Presentation(title="Hello") as deck:
        with Slide():
            Title("Hello world")
            Text("A tiny deck.")

    deck.push()
"""

from __future__ import annotations

from slidebox._version import __version__
from slidebox.components.image import Image
from slidebox.components.kpi import Kpi
from slidebox.components.kpi_grid import KpiGrid
from slidebox.components.layout import Col, Grid, Row, Spacer
from slidebox.components.shape import Shape, ShapeType
from slidebox.components.slide import Slide
from slidebox.components.text import Heading, Subtitle, Text, Title
from slidebox.context import defer, insert
from slidebox.errors import (
    AuthError,
    CompileError,
    LayoutError,
    QuotaExceededError,
    SlideboxError,
    StaleStateError,
    ValidationError,
)
from slidebox.geometry import Bounds
from slidebox.presentation import Presentation
from slidebox.theme import KpiTheme, TextStyleDef, Theme, themes
from slidebox.units import emu, inches, percent, pt, px

__all__ = [
    "AuthError",
    "Bounds",
    "Col",
    "CompileError",
    "Grid",
    "Heading",
    "Image",
    "Kpi",
    "KpiGrid",
    "KpiTheme",
    "LayoutError",
    "Presentation",
    "QuotaExceededError",
    "Row",
    "Shape",
    "ShapeType",
    "Slide",
    "SlideboxError",
    "Spacer",
    "StaleStateError",
    "Subtitle",
    "Text",
    "TextStyleDef",
    "Theme",
    "Title",
    "ValidationError",
    "__version__",
    "defer",
    "emu",
    "inches",
    "insert",
    "percent",
    "pt",
    "px",
    "themes",
]


def __getattr__(name: str) -> object:
    """Lazily expose `Updater` without forcing client imports at package load."""
    if name == "Updater":
        from slidebox.update.updater import Updater

        return Updater
    raise AttributeError(f"module 'slidebox' has no attribute {name!r}")
