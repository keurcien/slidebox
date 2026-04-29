from __future__ import annotations

import pytest

from slidebox import Kpi, KpiGrid, Presentation, Slide
from slidebox.components.kpi_grid import row_split
from slidebox.errors import LayoutError
from slidebox.geometry import Bounds
from slidebox.layout.engine import LayoutEngine
from slidebox.units import DEFAULT_CANVAS_H_EMU, DEFAULT_CANVAS_W_EMU


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, []),
        (1, [1]),
        (2, [2]),
        (3, [3]),
        (4, [2, 2]),
        (5, [3, 2]),
        (6, [3, 3]),
    ],
)
def test_row_split_distribution(n: int, expected: list[int]) -> None:
    assert row_split(n) == expected


def test_row_split_rejects_over_six() -> None:
    with pytest.raises(LayoutError):
        row_split(7)


def _resolve(deck: Presentation) -> None:
    LayoutEngine(
        Bounds(0, 0, DEFAULT_CANVAS_W_EMU, DEFAULT_CANVAS_H_EMU),
        deck.theme,
    ).resolve(deck)


def test_three_kpis_get_equal_width() -> None:
    with Presentation() as deck, Slide(), KpiGrid() as grid:
        Kpi("a", "1")
        Kpi("b", "2")
        Kpi("c", "3")
    _resolve(deck)

    widths = [k.bounds.w for k in grid.children]
    assert len(set(widths)) <= 2  # rounding may leave ±1 EMU


def test_four_kpis_split_into_two_rows() -> None:
    with Presentation() as deck, Slide(), KpiGrid() as grid:
        for i in range(4):
            Kpi(f"m{i}", str(i))
    _resolve(deck)

    cards = grid.children
    ys = [c.bounds.y for c in cards]
    # Two distinct y-coordinates — two rows.
    assert len(set(ys)) == 2
    # Top row has 2 cards, bottom row has 2 cards.
    top_y = min(ys)
    bottom_y = max(ys)
    assert sum(1 for y in ys if y == top_y) == 2
    assert sum(1 for y in ys if y == bottom_y) == 2


def test_six_kpis_split_three_and_three() -> None:
    with Presentation() as deck, Slide(), KpiGrid() as grid:
        for i in range(6):
            Kpi(f"m{i}", str(i))
    _resolve(deck)

    cards = grid.children
    ys = {c.bounds.y for c in cards}
    assert len(ys) == 2
    top_y = min(ys)
    bottom_y = max(ys)
    assert sum(1 for c in cards if c.bounds.y == top_y) == 3
    assert sum(1 for c in cards if c.bounds.y == bottom_y) == 3


def test_empty_grid_does_not_crash() -> None:
    with Presentation() as deck, Slide():
        KpiGrid()
    _resolve(deck)  # must not raise
