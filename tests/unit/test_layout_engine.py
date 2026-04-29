from __future__ import annotations

from slidebox import Col, Kpi, Presentation, Row, Slide, Spacer, Text, Title
from slidebox.geometry import Bounds
from slidebox.layout.engine import LayoutEngine
from slidebox.theme import themes
from slidebox.units import DEFAULT_CANVAS_H_EMU, DEFAULT_CANVAS_W_EMU


def _resolve(deck: Presentation) -> LayoutEngine:
    engine = LayoutEngine(
        Bounds(0, 0, DEFAULT_CANVAS_W_EMU, DEFAULT_CANVAS_H_EMU),
        deck.theme,
    )
    engine.resolve(deck)
    return engine


def test_slide_gets_canvas_bounds() -> None:
    with Presentation(theme=themes.default()) as deck, Slide():
        Text("hi")
    _resolve(deck)
    assert deck.children[0].bounds == Bounds(0, 0, DEFAULT_CANVAS_W_EMU, DEFAULT_CANVAS_H_EMU)


def test_row_splits_width_evenly() -> None:
    with Presentation(theme=themes.default()) as deck, Slide(), Row() as row:
        Text("a")
        Text("b")
        Text("c")
    _resolve(deck)

    bounds = [c.bounds for c in row.children]
    assert all(b is not None for b in bounds)
    assert sum(b.w for b in bounds) == DEFAULT_CANVAS_W_EMU
    assert {b.y for b in bounds} == {0}
    assert {b.h for b in bounds} == {DEFAULT_CANVAS_H_EMU}


def test_col_splits_height_evenly() -> None:
    with Presentation(theme=themes.default()) as deck, Slide(), Col() as col:
        Text("a")
        Text("b")
    _resolve(deck)

    a, b = col.children
    assert a.bounds.y == 0
    assert b.bounds.y == a.bounds.h
    assert a.bounds.w == DEFAULT_CANVAS_W_EMU
    assert a.bounds.h + b.bounds.h == DEFAULT_CANVAS_H_EMU


def test_padding_insets_children() -> None:
    with Presentation(theme=themes.default()) as deck, Slide(), Col(padding=100) as col:
        Text("a")
    _resolve(deck)

    child = col.children[0]
    assert child.bounds.x == 100
    assert child.bounds.y == 100
    assert child.bounds.w == DEFAULT_CANVAS_W_EMU - 200
    assert child.bounds.h == DEFAULT_CANVAS_H_EMU - 200


def test_gap_shrinks_children() -> None:
    with Presentation(theme=themes.default()) as deck, Slide(), Row(gap=50) as row:
        Text("a")
        Text("b")
    _resolve(deck)

    a, b = row.children
    assert b.bounds.x == a.bounds.w + 50
    assert a.bounds.w + b.bounds.w == DEFAULT_CANVAS_W_EMU - 50


def test_spacer_absorbs_leftover_space() -> None:
    with Presentation(theme=themes.default()) as deck, Slide(), Row() as row:
        a = Text("a")  # flex=1 (leaf default via engine)
        Spacer(width=200)
        b = Text("b")
    _resolve(deck)
    spacer = row.children[1]
    assert spacer.bounds.w == 200
    assert a.bounds.w + 200 + b.bounds.w == DEFAULT_CANVAS_W_EMU


def test_nested_layout_kpi_row() -> None:
    with Presentation(theme=themes.default()) as deck, Slide(), Col(padding=48, gap=24):
        Title("Hi")
        with Row(gap=16) as row:
            Kpi("a", "1")
            Kpi("b", "2")
            Kpi("c", "3")
    _resolve(deck)

    # Three KPIs share the content row minus 2 gaps.
    kpis = row.children
    widths = [k.bounds.w for k in kpis]
    assert len(set(widths)) <= 2  # at most 1-EMU rounding difference
    # Every descendant must have bounds by now.
    for node in deck.children[0].walk():
        assert node.bounds is not None, node
