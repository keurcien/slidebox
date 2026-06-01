"""render() — python-pptx output tests.

Inspect the rendered Presentation: shape counts, names (object ids),
background fills.
"""

from __future__ import annotations

from pptx.util import Emu

from slidebox import BrandTheme, Deck, render
from slidebox.types import SLIDE_H_EMU, SLIDE_W_EMU


def _shape_names(slide) -> list[str]:
    return [s.name for s in slide.shapes]


def test_deck_renders_one_slide_per_slide() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(bg="beige", object_id="s1")
        .header("a", col=1, row=1, span=(8, 2))
        .slide(bg="black", object_id="s2")
        .header("b", col=1, row=1, span=(8, 2))
    ).build()
    prs = render(deck)
    assert len(prs.slides) == 2
    assert prs.slide_width == Emu(SLIDE_W_EMU)
    assert prs.slide_height == Emu(SLIDE_H_EMU)


def test_kpi_emits_frame_and_named_parts() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .kpi(label="GMV", value="4,2", unit="M€", delta="+24%", delta_dir="up",
             col=1, row=1, span=(10, 5), object_id="hero_kpi")
    ).build()
    names = _shape_names(render(deck).slides[0])
    for suffix in ("__frame", "__label", "__value", "__delta"):
        assert f"hero_kpi{suffix}" in names


def test_object_id_becomes_shape_name() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .header("a", col=1, row=1, span=(8, 2), object_id="cover_title")
    ).build()
    assert "cover_title" in _shape_names(render(deck).slides[0])


def test_image_placeholder_draws_a_shape() -> None:
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(object_id="s")
        .image(placeholder_tone="nude", col=1, row=1, span=(6, 4),
               object_id="img")
    ).build()
    assert "img" in _shape_names(render(deck).slides[0])


def test_custom_theme_sets_background() -> None:
    from slidebox.types import RGB

    custom = BrandTheme(beige=RGB(1, 2, 3))
    deck = (
        Deck.new(title="T", object_id="t")
        .slide(bg="beige", object_id="s")
        .header("a", col=1, row=1, span=(8, 2))
    ).build()
    slide = render(deck, theme=custom).slides[0]
    fill = slide.background.fill
    assert (fill.fore_color.rgb[0], fill.fore_color.rgb[1], fill.fore_color.rgb[2]) == (1, 2, 3)
