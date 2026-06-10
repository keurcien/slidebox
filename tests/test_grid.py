"""Grid math tests."""

from __future__ import annotations

import pytest

from slidebox.grid import (
    EMU_PER_DESIGN_PT_X,
    EMU_PER_DESIGN_PT_Y,
    GUTTER_PT,
    cell_to_emu,
    cells_overlap,
    grid_dims,
    in_bounds,
)
from slidebox.schema import HeaderCard
from slidebox.types import SLIDE_H_EMU, SLIDE_W_EMU


def test_grid_dims() -> None:
    assert grid_dims("coarse") == (6, 4)
    assert grid_dims("standard") == (12, 6)
    assert grid_dims("fine") == (12, 8)


def test_cell_to_emu_top_left_at_fine() -> None:
    # The default fine (12x8) grid must produce positive heights for a
    # 1x1 cell; this regression catches the spec/EMU scale bug.
    x, y, w, h = cell_to_emu(1, 1, 1, 1, res="fine")
    assert x == int(GUTTER_PT * EMU_PER_DESIGN_PT_X)
    assert y == int(GUTTER_PT * EMU_PER_DESIGN_PT_Y)
    assert w > 0 and h > 0


def test_cell_to_emu_full_span_fits_inside_gutter() -> None:
    cols, rows = grid_dims("fine")
    x, y, w, h = cell_to_emu(1, cols, 1, rows, res="fine")
    expected_x_end = SLIDE_W_EMU - int(GUTTER_PT * EMU_PER_DESIGN_PT_X)
    expected_y_end = SLIDE_H_EMU - int(GUTTER_PT * EMU_PER_DESIGN_PT_Y)
    # Allow a few EMU of rounding slack from the per-axis truncation.
    assert x + w == pytest.approx(expected_x_end, abs=cols)
    assert y + h == pytest.approx(expected_y_end, abs=rows)


def test_cells_overlap() -> None:
    a = HeaderCard(
        object_id="a", col_start=1, col_span=6, row_start=1, row_span=3, text="A"
    )
    b = HeaderCard(
        object_id="b", col_start=4, col_span=4, row_start=2, row_span=3, text="B"
    )
    c = HeaderCard(
        object_id="c", col_start=7, col_span=4, row_start=1, row_span=3, text="C"
    )
    assert cells_overlap(a, b)
    assert not cells_overlap(a, c)


def test_in_bounds() -> None:
    assert in_bounds(1, 12, 1, 8, "fine")
    assert not in_bounds(1, 13, 1, 8, "fine")
    assert not in_bounds(1, 12, 1, 9, "fine")
    assert in_bounds(1, 6, 1, 4, "coarse")
    assert not in_bounds(2, 6, 1, 4, "coarse")  # spills past col 6
