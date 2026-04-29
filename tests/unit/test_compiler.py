from __future__ import annotations

import pytest

from slidebox import Col, Image, Kpi, Presentation, Row, Slide, Text, Title
from slidebox.compile.compiler import Compiler
from slidebox.geometry import Bounds
from slidebox.layout.engine import LayoutEngine
from slidebox.units import DEFAULT_CANVAS_H_EMU, DEFAULT_CANVAS_W_EMU


def _layout(deck: Presentation) -> None:
    LayoutEngine(
        Bounds(0, 0, DEFAULT_CANVAS_W_EMU, DEFAULT_CANVAS_H_EMU),
        deck.theme,
    ).resolve(deck)


def test_hello_world_compiles() -> None:
    with Presentation(title="Hello") as deck, Slide(id="slide_hello"):
        Title("Hello world", id="text_title")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)

    kinds = [next(iter(r)) for r in plan.requests]
    assert kinds[0] == "createSlide"
    assert "createShape" in kinds  # the text box
    assert "insertText" in kinds
    assert "updateTextStyle" in kinds


def test_slide_created_before_elements() -> None:
    with Presentation() as deck, Slide(id="slide_a"):
        Title("a", id="text_1")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    slide_idx = next(i for i, r in enumerate(plan.requests) if "createSlide" in r)
    text_idx = next(i for i, r in enumerate(plan.requests) if "insertText" in r)
    assert slide_idx < text_idx


def test_shape_created_before_its_text_is_inserted() -> None:
    with Presentation() as deck, Slide(id="slide_a"):
        Text("hi", id="text_1")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    shape_req = next(
        r for r in plan.requests if "createShape" in r and r["createShape"]["objectId"] == "text_1"
    )
    text_req = next(
        r for r in plan.requests if "insertText" in r and r["insertText"]["objectId"] == "text_1"
    )
    assert plan.requests.index(shape_req) < plan.requests.index(text_req)


def test_insert_text_precedes_update_style() -> None:
    with Presentation() as deck, Slide():
        Title("a", id="text_1")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    t_idx = next(
        i
        for i, r in enumerate(plan.requests)
        if "insertText" in r and r["insertText"]["objectId"] == "text_1"
    )
    s_idx = next(
        i
        for i, r in enumerate(plan.requests)
        if "updateTextStyle" in r and r["updateTextStyle"]["objectId"] == "text_1"
    )
    assert t_idx < s_idx


def test_alt_text_applied_per_element() -> None:
    with Presentation() as deck, Slide(id="slide_a"):
        Text("hi", id="text_1", metadata={"source": "test"})
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    alt_reqs = [r for r in plan.requests if "updatePageElementAltText" in r]
    assert any(r["updatePageElementAltText"]["objectId"] == "text_1" for r in alt_reqs)
    for r in alt_reqs:
        if r["updatePageElementAltText"]["objectId"] == "text_1":
            assert "slidebox:v1:Text" in r["updatePageElementAltText"]["title"]


def test_image_emits_createImage() -> None:
    with Presentation() as deck, Slide(id="slide_a"):
        Image("https://example.com/img.png", id="image_1")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    create_imgs = [r for r in plan.requests if "createImage" in r]
    assert len(create_imgs) == 1
    assert create_imgs[0]["createImage"]["objectId"] == "image_1"


def test_kpi_emits_card_and_three_texts() -> None:
    with Presentation() as deck, Slide(id="slide_a"):
        Kpi("Revenue", "$4M", trend="+12%", id="kpi_one")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    shapes = [r for r in plan.requests if "createShape" in r]
    inserts = [r for r in plan.requests if "insertText" in r]
    # Card bg + 3 text boxes (label/value/trend) = 4 shapes, no accent bar.
    assert len(shapes) == 4
    assert len(inserts) == 3
    shape_ids = {r["createShape"]["objectId"] for r in shapes}
    assert {"kpi_one", "kpi_one_label", "kpi_one_value", "kpi_one_trend"} <= shape_ids


def test_layout_containers_emit_nothing() -> None:
    with Presentation() as deck, Slide(id="slide_a"), Col(padding=20), Row(gap=10):
        Text("a", id="text_a")
    _layout(deck)
    plan = Compiler(deck.theme).compile(deck)
    for r in plan.requests:
        for body in r.values():
            if isinstance(body, dict) and "objectId" in body:
                assert "row" not in body["objectId"].lower()
                assert "col" not in body["objectId"].lower()


def test_missing_bounds_raises() -> None:
    with Presentation() as deck, Slide(id="slide_a"):
        Text("hi", id="text_1")
    # Deliberately skip layout.
    with pytest.raises(Exception):
        Compiler(deck.theme).compile(deck)
