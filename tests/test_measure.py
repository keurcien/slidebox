"""measure_text() — pre-render fit prediction with the bundled fonts.

Lora/Inter/Roboto ship with the package, so these tests need no system fonts
and always run (unlike test_fit.py, which depends on a system TTF).
"""

from __future__ import annotations

import pytest

from slidebox import BUNDLED_FAMILIES, FitResult, bundled_fonts, measure_text
from slidebox.measure import (
    EMU_PER_INCH,
    VERDICT_FITS,
    VERDICT_HEIGHT,
    VERDICT_WIDTH,
)


def test_bundled_fonts_resolve_to_existing_files() -> None:
    from pathlib import Path

    fonts = bundled_fonts()
    assert set(fonts) == set(BUNDLED_FAMILIES)
    for variants in fonts.values():
        assert isinstance(variants, dict)
        for path in variants.values():
            assert Path(path).is_file()


@pytest.mark.parametrize("family", BUNDLED_FAMILIES)
def test_short_text_fits_and_uses_real_metrics(family: str) -> None:
    r = measure_text(
        "A quiet quarter.",
        family=family, size_pt=14,
        width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2,
    )
    assert r.fits is True
    assert bool(r) is True  # FitResult is truthy when it fits
    assert r.verdict == VERDICT_FITS
    assert r.measured is True  # bundled family -> real font, not estimate
    assert r.recommended_max_chars is None
    assert r.recommended_size_pt is None


def test_height_overflow_is_detected_with_recommendations() -> None:
    long = "Le marché lifestyle est complètement saturé aujourd'hui et rien ne change."
    # safety_lines=0 to exercise the raw recommendation geometry (the safety
    # reserve is covered separately).
    r = measure_text(
        long, family="Lora", size_pt=18,
        width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2, safety_lines=0.0,
    )
    assert r.fits is False
    assert r.verdict == VERDICT_HEIGHT
    assert r.lines_needed > r.lines_available
    # Growing the box to the recommended height must actually make it fit.
    grown = measure_text(
        long, family="Lora", size_pt=18,
        width_emu=3 * EMU_PER_INCH, height_emu=r.recommended_min_height_emu,
        safety_lines=0.0,
    )
    assert grown.fits is True
    # Shrinking to the recommended size must also make it fit the original box.
    assert r.recommended_size_pt is not None
    shrunk = measure_text(
        long, family="Lora", size_pt=r.recommended_size_pt,
        width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2, safety_lines=0.0,
    )
    assert shrunk.fits is True
    # Trimming to the recommended char count must fit too.
    assert r.recommended_max_chars is not None and r.recommended_max_chars > 0
    trimmed = measure_text(
        long[: r.recommended_max_chars], family="Lora", size_pt=18,
        width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2, safety_lines=0.0,
    )
    assert trimmed.fits is True


def test_over_long_word_breaks_into_lines_not_width_overflow() -> None:
    # Slides char-breaks an over-long word at the edge, so in a narrow+short
    # box it becomes a HEIGHT overflow (many broken lines), never width.
    r = measure_text(
        "Supercalifragilisticexpialidocious",
        family="Inter", size_pt=40, safety_lines=0.0,
        width_emu=EMU_PER_INCH, height_emu=EMU_PER_INCH,
    )
    assert r.fits is False
    assert r.verdict == VERDICT_HEIGHT  # broken into lines, not a width overflow
    assert r.lines_needed > 1  # the single word spans several broken lines
    assert r.recommended_min_width_emu is None  # widening isn't the fix here


def test_over_long_word_fits_when_box_is_tall_enough() -> None:
    # Same word, narrow but tall box: the broken lines all fit -> FITS.
    r = measure_text(
        "Supercalifragilisticexpialidocious",
        family="Inter", size_pt=20, safety_lines=0.0,
        width_emu=EMU_PER_INCH, height_emu=3 * EMU_PER_INCH,
    )
    assert r.fits is True
    assert r.lines_needed > 1


def test_single_glyph_wider_than_box_is_width_overflow() -> None:
    # Degenerate: 40pt text in a box barely wider than the insets -> even one
    # glyph can't fit, so it's a genuine width overflow.
    r = measure_text(
        "WWWW", family="Inter", size_pt=40, safety_lines=0.0,
        width_emu=2 * 91440 + 20_000, height_emu=3 * EMU_PER_INCH,
    )
    assert r.verdict == VERDICT_WIDTH
    assert r.recommended_min_width_emu is not None and r.recommended_min_width_emu > 0


def test_line_height_is_per_font_from_real_metrics() -> None:
    # "single" spacing == the font's natural line height, which differs per
    # family (Lora is the tallest, Roboto the shortest).
    def ratio(family: str) -> float:
        r = measure_text(
            "x", family=family, size_pt=100,
            width_emu=10 * EMU_PER_INCH, height_emu=10 * EMU_PER_INCH,
        )
        return r.line_height_pt / 100

    assert ratio("Lora") > ratio("Inter") > ratio("Roboto")
    assert 1.1 < ratio("Roboto") < 1.35  # sane envelope, not the flat 1.2


def test_line_spacing_multiplier_scales_height() -> None:
    base = measure_text(
        "x", family="Inter", size_pt=20, line_spacing=1.0,
        width_emu=5 * EMU_PER_INCH, height_emu=5 * EMU_PER_INCH,
    )
    loose = measure_text(
        "x", family="Inter", size_pt=20, line_spacing=1.5,
        width_emu=5 * EMU_PER_INCH, height_emu=5 * EMU_PER_INCH,
    )
    assert loose.line_height_pt == pytest.approx(base.line_height_pt * 1.5)


def test_paragraph_list_stacks_independently() -> None:
    paras = ["First line here.", "Second line here.", "Third line here."]
    # A box tall enough for ~2 lines at 24pt cannot hold three paragraphs.
    r = measure_text(
        paras, family="Roboto", size_pt=24,
        width_emu=5 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2,
    )
    assert r.lines_needed >= 3
    assert r.fits is False
    assert r.verdict == VERDICT_HEIGHT


def test_safety_lines_reserves_bottom_headroom() -> None:
    # A box that exactly holds 3 lines with no safety should report fewer
    # available lines (and flag a borderline 3-line text) once safety is on.
    kw = dict(family="Inter", size_pt=14, width_emu=4 * EMU_PER_INCH)
    # Height chosen to hold ~3 lines raw but only ~2 with a half-line reserve.
    raw = measure_text("x", height_emu=760_000, safety_lines=0.0, **kw)
    safe = measure_text("x", height_emu=760_000, safety_lines=0.5, **kw)
    assert safe.lines_available < raw.lines_available
    # The reserve only shrinks the usable height; line pitch is unchanged.
    assert safe.line_height_pt == raw.line_height_pt


def test_unknown_family_falls_back_to_estimate() -> None:
    r = measure_text(
        "Hello there", family="Totally Made Up", size_pt=14,
        width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2,
    )
    assert r.measured is False  # estimated, not measured
    assert isinstance(r, FitResult)


def test_zero_area_box_reports_overflow() -> None:
    r = measure_text(
        "x", family="Inter", size_pt=12,
        width_emu=1000, height_emu=1000,  # smaller than the insets
    )
    assert r.fits is False
    assert r.usable_width_pt <= 0 or r.box_height_pt <= 0
