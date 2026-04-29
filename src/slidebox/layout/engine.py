"""LayoutEngine — walks the component tree and assigns `.bounds`.

Algorithm:
    1. Each Slide starts with the canvas as its available bounds.
    2. For a container (Row / Col / Shape / Kpi), subtract its padding
       to get the content bounds.
    3. Call the flex solver with children's fixed sizes / weights.
    4. Walk children, passing each its slice of the content bounds, and
       recurse.

The engine is deliberately the only place that touches bounds, so
downstream stages (compiler, updater) can trust every component to
have concrete EMU coordinates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from slidebox.components.base import Component, ContainerComponent
from slidebox.components.kpi import Kpi
from slidebox.components.kpi_grid import (
    GRID_GAP_EMU,
    PREFERRED_CARD_HEIGHT_EMU,
    KpiGrid,
    row_split,
)
from slidebox.components.layout import Col, Grid, Row, _FlexContainer
from slidebox.components.shape import Shape
from slidebox.components.slide import Slide
from slidebox.geometry import Bounds
from slidebox.layout.constraints import normalise_padding
from slidebox.layout.flex import FlexChild, solve_flex

if TYPE_CHECKING:
    from slidebox.presentation import Presentation
    from slidebox.theme import Theme


class LayoutEngine:
    """Assigns absolute EMU bounds to every component in the tree."""

    def __init__(self, canvas: Bounds, theme: Theme) -> None:
        self._canvas = canvas
        self._theme = theme

    # ── public ────────────────────────────────────────────────────────
    def resolve(self, deck: Presentation) -> None:
        for slide in deck.children:
            slide.bounds = self._canvas
            self._layout_slide(slide)

    # ── slides ────────────────────────────────────────────────────────
    def _layout_slide(self, slide: Slide) -> None:
        content = self._apply_padding(self._canvas, slide.padding)
        self._layout_children(slide.children, content, axis="y")

    # ── containers ────────────────────────────────────────────────────
    def _layout_component(self, comp: Component, bounds: Bounds) -> None:
        comp.bounds = bounds
        if isinstance(comp, Row):
            self._layout_flex(comp, bounds, axis="x")
        elif isinstance(comp, Col):
            self._layout_flex(comp, bounds, axis="y")
        elif isinstance(comp, Shape):
            # A Shape occupies its assigned bounds; its children inherit
            # the same region. (The only sanctioned child is a Col/Text.)
            content = bounds
            self._layout_children(comp.children, content, axis="y")
        elif isinstance(comp, Kpi):
            self._layout_children(comp.children, bounds, axis="y")
        elif isinstance(comp, KpiGrid):
            self._layout_kpi_grid(comp, bounds)
        elif isinstance(comp, Grid):
            self._layout_grid(comp, bounds)
        elif isinstance(comp, ContainerComponent):
            self._layout_children(comp.children, bounds, axis="y")

    def _layout_flex(self, container: _FlexContainer, bounds: Bounds, axis: str) -> None:
        content = self._apply_padding(bounds, container.padding)
        self._layout_children(container.children, content, axis=axis, gap=container.gap)

    def _layout_kpi_grid(self, grid: KpiGrid, bounds: Bounds) -> None:
        """Auto-distribute 1-6 Kpi children across 1 or 2 rows.

        Each card gets `PREFERRED_CARD_HEIGHT_EMU` when the grid has
        room; otherwise the height shrinks to fit. Cards are anchored
        to the top — leftover space falls out the bottom.
        """
        rows = row_split(len(grid.children))
        if not rows:
            return

        row_gap = GRID_GAP_EMU
        col_gap = GRID_GAP_EMU
        max_allowed = (bounds.h - row_gap * (len(rows) - 1)) // len(rows)
        row_h = min(PREFERRED_CARD_HEIGHT_EMU, max_allowed)

        idx = 0
        for ri, card_count in enumerate(rows):
            row_y = bounds.y + ri * (row_h + row_gap)
            card_w = (bounds.w - col_gap * (card_count - 1)) // card_count
            for ci in range(card_count):
                child = grid.children[idx]
                idx += 1
                card_x = bounds.x + ci * (card_w + col_gap)
                self._layout_component(child, Bounds(card_x, row_y, card_w, row_h))

    def _layout_grid(self, grid: Grid, bounds: Bounds) -> None:
        content = self._apply_padding(bounds, grid.padding)
        cols = max(1, grid.columns)
        children = grid.children
        col_w = (content.w - grid.gap * (cols - 1)) // cols
        rows = (len(children) + cols - 1) // cols
        row_h = (content.h - grid.gap * (rows - 1)) // max(1, rows) if rows else content.h

        for idx, child in enumerate(children):
            r, c = divmod(idx, cols)
            x = content.x + c * (col_w + grid.gap)
            y = content.y + r * (row_h + grid.gap)
            self._layout_component(child, Bounds(x, y, col_w, row_h))

    def _layout_children(
        self,
        children: list[Component],
        bounds: Bounds,
        *,
        axis: str,
        gap: int = 0,
    ) -> None:
        if not children:
            return

        main = bounds.w if axis == "x" else bounds.h
        flex_children = [self._as_flex_child(c, axis) for c in children]
        sizes = solve_flex(main, flex_children, gap=gap)

        cursor = bounds.x if axis == "x" else bounds.y
        for child, size in zip(children, sizes, strict=True):
            if axis == "x":
                sub = Bounds(cursor, bounds.y, size, bounds.h)
            else:
                sub = Bounds(bounds.x, cursor, bounds.w, size)
            self._layout_component(child, sub)
            cursor += size + gap

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _as_flex_child(comp: Component, axis: str) -> FlexChild:
        fixed_main = comp.width if axis == "x" else comp.height
        if fixed_main is not None:
            return FlexChild(fixed=int(fixed_main), flex=0)
        return FlexChild(fixed=None, flex=comp.flex if comp.flex is not None else 1)

    @staticmethod
    def _apply_padding(bounds: Bounds, padding: object) -> Bounds:
        top, right, bottom, left = normalise_padding(padding)
        return bounds.inset(top=top, right=right, bottom=bottom, left=left)
