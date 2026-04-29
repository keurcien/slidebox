"""Shape component — a coloured rectangle, ellipse, or arrow.

Shapes carry their own background fill and stroke. To draw a shape with
text inside, nest a `Text` inside a `Shape` using a context manager —
the layout engine positions the text relative to the shape.

Shapes can be fixed-size (`width=` / `height=` in EMU or a unit string)
to participate predictably in a flex row/column.
"""

from __future__ import annotations

from enum import Enum
from typing import ClassVar

from slidebox.components.base import ContainerComponent


class ShapeType(str, Enum):
    """Subset of Google's 141 shape types — only the ones people actually use."""

    RECTANGLE = "RECTANGLE"
    ROUND_RECTANGLE = "ROUND_RECTANGLE"
    ELLIPSE = "ELLIPSE"
    TRIANGLE = "TRIANGLE"
    RIGHT_TRIANGLE = "RIGHT_TRIANGLE"
    DIAMOND = "DIAMOND"
    ARROW = "RIGHT_ARROW"
    STAR = "STAR_5"
    CLOUD = "CLOUD"
    TEXT_BOX = "TEXT_BOX"


class Shape(ContainerComponent):
    """A filled, bordered shape. May contain a nested `Text` or layout.

    Args:
        shape_type: Any ShapeType (string also accepted for forward-compat).
        fill: Background colour hex, e.g. "#ffce3e". None = no fill.
        stroke: Border colour hex. None = no border.
        stroke_width: Border thickness in points.
        corner_radius: For ROUND_RECTANGLE, the rounded-corner radius in pt.
        width: Optional fixed width (EMU or '12pt'). Makes the Shape
            a fixed-size flex child.
        height: Optional fixed height (EMU or '12pt').
        flex: Flex weight when Shape is inside a Row/Col and no
            fixed width/height is set.
    """

    kind: ClassVar[str] = "shape"

    shape_type: ShapeType | str = ShapeType.RECTANGLE
    fill: str | None = None
    stroke: str | None = None
    stroke_width: float | None = None
    corner_radius: float | None = None
