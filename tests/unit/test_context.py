from __future__ import annotations

import threading

import pytest

from slidebox import Col, Kpi, Presentation, Row, Slide, Text, Title, defer, insert
from slidebox.components.base import ContainerComponent
from slidebox.errors import ValidationError


def test_nested_context_wires_parent_child() -> None:
    with Presentation() as deck, Slide() as slide, Row() as row:
        Text("a")
        Text("b")

    assert deck.children == [slide]
    assert slide.children == [row]
    assert [c.content for c in row.children] == ["a", "b"]  # type: ignore[attr-defined]


def test_components_outside_context_have_no_parent() -> None:
    orphan = Text("stray")
    assert orphan.content == "stray"


def test_id_validation_rejects_bad_strings() -> None:
    with pytest.raises(ValidationError):
        Text("x", id="1starts-with-digit")
    with pytest.raises(ValidationError):
        Text("x", id="has spaces")
    with pytest.raises(ValidationError):
        Text("x", id="abc")  # < 5 chars


def test_id_accepts_hyphen_and_underscore() -> None:
    Text("x", id="valid_id-123")  # does not raise


def test_defer_detaches_then_insert_reattaches() -> None:
    with Col() as outer:
        with defer():
            card = Row()
            with card:
                Text("inside")
        # card was built but not attached to outer
        assert card not in outer.children
        insert(card)

    assert card in outer.children
    assert len(card.children) == 1


def test_insert_outside_context_raises() -> None:
    stray = Text("x")
    with pytest.raises(RuntimeError):
        insert(stray)


def test_threads_build_independent_trees() -> None:
    """Two threads building decks concurrently must not interleave."""
    results: dict[int, list[str]] = {}

    def build(idx: int, label: str) -> None:
        with Presentation() as deck, Slide():
            Text(label, id=f"text_{idx:03d}")
        results[idx] = [c.id for slide in deck.children for c in slide.children]  # type: ignore[misc]

    t1 = threading.Thread(target=build, args=(1, "a"))
    t2 = threading.Thread(target=build, args=(2, "b"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results[1] == ["text_001"]
    assert results[2] == ["text_002"]


def test_kpi_builds_composite_children() -> None:
    with Presentation() as deck, Slide():
        Kpi("Revenue", "$4.2M", trend="+12%", id="kpi_rev")

    kpi = deck.children[0].children[0]
    assert isinstance(kpi, ContainerComponent)
    # Kpi -> Shape (card) -> Col -> [label, Spacer, value, trend]
    card = kpi.children[0]
    assert isinstance(card, ContainerComponent)
    col = card.children[0]
    assert isinstance(col, ContainerComponent)
    assert len(col.children) == 4


def test_to_json_round_trips() -> None:
    with Presentation(title="X") as deck, Slide(id="slide_x"):
        Title("Hi", id="text_t")

    payload = deck.to_json()
    assert '"id": "text_t"' in payload
    assert '"Hi"' in payload


def test_walk_yields_full_tree() -> None:
    with Presentation(), Slide(id="slide_x") as slide, Row() as row:
        Text("a")

    nodes = list(slide.walk())
    assert slide in nodes
    assert row in nodes
    assert any(getattr(n, "content", None) == "a" for n in nodes)
