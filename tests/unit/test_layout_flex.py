from __future__ import annotations

import pytest

from slidebox.errors import LayoutError
from slidebox.layout.flex import FlexChild, solve_flex


def test_empty_children() -> None:
    assert solve_flex(1000, []) == []


def test_single_flex_child_takes_all() -> None:
    assert solve_flex(1000, [FlexChild(None, 1)]) == [1000]


def test_three_equal_flex_children() -> None:
    result = solve_flex(900, [FlexChild(None, 1), FlexChild(None, 1), FlexChild(None, 1)])
    assert sum(result) == 900
    assert max(result) - min(result) <= 1  # rounding smoothed


def test_fixed_plus_flex() -> None:
    result = solve_flex(
        1000,
        [FlexChild(fixed=200, flex=0), FlexChild(fixed=None, flex=1)],
    )
    assert result == [200, 800]


def test_gap_is_subtracted_before_distribution() -> None:
    result = solve_flex(1000, [FlexChild(None, 1), FlexChild(None, 1)], gap=100)
    assert sum(result) == 900


def test_weighted_flex() -> None:
    result = solve_flex(900, [FlexChild(None, 2), FlexChild(None, 1)])
    assert sum(result) == 900
    assert result[0] == 600 and result[1] == 300


def test_gap_exceeds_space() -> None:
    with pytest.raises(LayoutError):
        solve_flex(100, [FlexChild(None, 1), FlexChild(None, 1)], gap=200)


def test_fixed_exceeds_space() -> None:
    with pytest.raises(LayoutError):
        solve_flex(100, [FlexChild(fixed=500, flex=0)])
