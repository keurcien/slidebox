"""Builder API tests."""

from __future__ import annotations

from slidebox import Deck
from slidebox.builder import card_object_id, slide_object_id


def test_chained_builder_returns_typed_deck() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(bg="black", label="01 cover")
        .header("A title.", size="display", col=1, row=4, span=(7, 3))
        .subtitle("subtitle here.", col=1, row=7, span=(6, 1))
    ).build()
    assert deck.title == "T"
    assert len(deck.slides) == 1
    s = deck.slides[0]
    assert s.background == "black"
    assert s.label == "01 cover"
    assert [c.type for c in s.cards] == ["header", "subtitle"]


def test_span_int_shorthand_means_one_row() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide()
        .subtitle("foo", col=1, row=1, span=6)
    ).build()
    f = deck.slides[0].cards[0]
    assert (f.col_span, f.row_span) == (6, 1)


def test_autogen_ids_are_deterministic() -> None:
    d1 = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s1")
        .header("a", col=1, row=1, span=(8, 2))
        .header("b", col=1, row=4, span=(8, 2))
    ).build()
    d2 = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s1")
        .header("a", col=1, row=1, span=(8, 2))
        .header("b", col=1, row=4, span=(8, 2))
    ).build()
    ids1 = [c.object_id for c in d1.slides[0].cards]
    ids2 = [c.object_id for c in d2.slides[0].cards]
    assert ids1 == ids2
    assert ids1 == ["s1.header.1", "s1.header.2"]


def test_explicit_object_id_preserved() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s1")
        .kpi(value="4,2", unit="M€", col=1, row=1, span=(10, 5), object_id="hero")
    ).build()
    assert deck.slides[0].cards[0].object_id == "hero"


def test_multiple_slides_chain() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(bg="white", object_id="s1")
        .header("one", col=1, row=1, span=(8, 2))
        .slide(bg="beige", object_id="s2")
        .header("two", col=1, row=1, span=(8, 2))
    ).build()
    assert [s.object_id for s in deck.slides] == ["s1", "s2"]


def test_id_helpers_are_pure() -> None:
    assert slide_object_id("d", 3) == "d_slide_03"
    assert card_object_id("s1", "kpi", 4) == "s1.kpi.4"
