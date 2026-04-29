"""Flex-style layout containers: Row, Col, Spacer, Grid.

These components do not emit anything to Google Slides themselves —
they only instruct the layout engine on how to divide the canvas. By
the time the compiler runs, their descendants have absolute bounds and
the containers can be discarded.
"""

from __future__ import annotations

from typing import ClassVar, Literal

from slidebox.components.base import ContainerComponent, LeafComponent
from slidebox.units import Length

Align = Literal["start", "center", "end", "stretch"]
Justify = Literal["start", "center", "end", "between", "around", "evenly"]

PaddingSpec = Length | tuple[Length, Length] | tuple[Length, Length, Length, Length] | None


class _FlexContainer(ContainerComponent):
    """Shared base for Row / Col."""

    gap: Length = 0
    padding: PaddingSpec = None
    align: Align | None = None
    justify: Justify | None = None


class Row(_FlexContainer):
    """Horizontal flex container — lays children out left-to-right."""

    kind: ClassVar[str] = "row"


class Col(_FlexContainer):
    """Vertical flex container — lays children out top-to-bottom."""

    kind: ClassVar[str] = "col"


class Spacer(LeafComponent):
    """Consumes layout space without emitting anything to the deck.

    Without a fixed size it takes one `flex=1` share of the parent.
    """

    kind: ClassVar[str] = "spacer"


class Grid(ContainerComponent):
    """Fixed-column grid — children flow left-to-right, top-to-bottom."""

    kind: ClassVar[str] = "grid"

    columns: int = 2
    gap: Length = 0
    padding: PaddingSpec = None
