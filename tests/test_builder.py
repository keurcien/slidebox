"""Builder API tests."""

from __future__ import annotations

import pytest

from slidebox import Deck
from slidebox.builder import card_object_id, slide_object_id
from slidebox.grid import cell_to_emu


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


def test_hybrid_grid_plus_absolute_y_resolves_to_bbox() -> None:
    # col/span set the x/w from the grid; an explicit y overrides only y.
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s", grid="fine")
        .header("Hi", col=7, span=(5, 1), y=100000, object_id="h")
    ).build()
    card = deck.slides[0].cards[0]
    gx, _gy, gw, gh = cell_to_emu(7, 5, 1, 1, res="fine")
    assert card.bbox is not None
    assert (card.bbox.x, card.bbox.w, card.bbox.h) == (gx, gw, gh)
    assert card.bbox.y == 100000  # only y was overridden


def test_pure_grid_still_uses_cells() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .header("Hi", col=1, row=1, span=(8, 2), object_id="h")
    ).build()
    card = deck.slides[0].cards[0]
    assert card.bbox is None
    assert (card.col_start, card.col_span) == (1, 8)


def test_body_line_spacing_passthrough() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .body("★ ★ ★ ★ ★", col=1, row=1, span=(4, 1), line_spacing=1.0, object_id="r")
    ).build()
    assert deck.slides[0].cards[0].line_spacing == 1.0


def test_body_accepts_bare_string() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .body("One paragraph.", col=1, row=1, span=(6, 2))
    ).build()
    assert deck.slides[0].cards[0].paragraphs == ["One paragraph."]


def test_image_path_and_url_aliases_map_to_source_url() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .image(path="/tmp/photo.jpg", col=1, row=1, span=(4, 4), object_id="i")
    ).build()
    assert deck.slides[0].cards[0].source_url == "/tmp/photo.jpg"


def test_image_rejects_multiple_sources() -> None:
    sb = Deck.new(title="T", object_id="t").slide(object_id="s")
    with pytest.raises(ValueError):
        sb.image(path="/tmp/a.jpg", url="https://x/y.jpg", col=1, row=1, span=(4, 4))


def test_min_height_returns_emu_that_fits() -> None:
    from slidebox import BrandTheme, measure_text
    from slidebox.measure import SLIDES_BODY_LINE_SPACING

    theme = BrandTheme(serif_family="Lora", sans_family="Inter")
    sb = Deck.new(title="T", object_id="t").slide(object_id="s")
    text = "Un texte de body assez long pour occuper plusieurs lignes une fois enroulé."
    width = 3_000_000
    h = sb.min_height(text, card="body", size_pt=10, width_emu=width, theme=theme)
    assert isinstance(h, int) and h > 0
    r = measure_text(
        text, family="Inter", size_pt=10, width_emu=width, height_emu=h,
        line_spacing=SLIDES_BODY_LINE_SPACING,
    )
    assert r.fits
