"""fit_report() — real-font overflow measurement.

The missing-font paths need no font files and always run. The measuring
paths need a scalable TTF; we locate one or skip (e.g. on minimal CI).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from slidebox import BrandTheme, Deck, fit_report, missing_families, report_fit
from slidebox.fit import Overflow, format_fit

_TTF_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def _ttf() -> str | None:
    for p in _TTF_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def _deck(card_fn) -> Deck:
    sb = Deck.new(title="t", object_id="t").slide(bg="white", object_id="s")
    return card_fn(sb).build()


def test_missing_family_is_reported_without_font_files() -> None:
    deck = _deck(lambda sb: sb.header("Hi there", col=1, row=1, span=(8, 2)))
    fams = missing_families(deck, {})  # provide nothing
    assert fams  # the serif family the header uses is missing
    issues = fit_report(deck, {})
    assert any(o.kind == "missing-font" for o in issues)


def test_clean_deck_has_no_overflow() -> None:
    ttf = _ttf()
    if ttf is None:
        pytest.skip("no scalable TTF available to measure with")
    fonts = {"Sangbleu Republic": ttf, "Maison Neue": ttf}
    deck = _deck(
        lambda sb: sb.header("A quiet quarter.", size="h1", col=1, row=1, span=(10, 2))
        .subtitle("A short, comfortable subtitle.", col=1, row=4, span=(8, 1))
    )
    issues = [o for o in fit_report(deck, fonts) if o.kind != "missing-font"]
    assert issues == []


def test_height_overflow_is_detected() -> None:
    ttf = _ttf()
    if ttf is None:
        pytest.skip("no scalable TTF available to measure with")
    fonts = {"Sangbleu Republic": ttf, "Maison Neue": ttf}
    # A paragraph far too long for a 1x1 cell — even floored at the min size
    # it cannot fit, so the checker must flag a height overflow.
    long_text = "This is a very long paragraph that cannot possibly fit. " * 8
    deck = _deck(
        lambda sb: sb.body([long_text], col=1, row=1, span=(1, 1), object_id="tiny")
    )
    issues = fit_report(deck, fonts)
    assert any(o.kind == "height" and o.shape_name == "tiny" for o in issues)


def test_overflow_is_a_dataclass_with_location() -> None:
    o = Overflow(2, "hero", "height", "too tall", "Hello")
    assert (o.slide_index, o.shape_name, o.kind) == (2, "hero", "height")


# --- bundled-default fit check (no font files needed: Lora/Inter/Roboto ship) --

_LORA_INTER = BrandTheme(serif_family="Lora", sans_family="Inter")


def _overflowing_deck() -> Deck:
    return (
        Deck.new(title="t", object_id="t")
        .slide(bg="white", object_id="s")
        .header("A fine title.", size_pt=20, col=1, row=1, span=(10, 2),
                object_id="ok_title")
        .body(["A very long paragraph that cannot possibly fit a one-cell box "
               "no matter how we slice it, so it must overflow. " * 2],
              size_pt=18, col=1, row=4, span=(2, 1), object_id="too_long")
        .build()
    )


def test_fit_report_uses_bundled_fonts_without_font_files() -> None:
    # No `fonts=` argument: Lora/Inter are measured from the bundled TTFs.
    issues = fit_report(_overflowing_deck(), theme=_LORA_INTER)
    assert any(o.kind == "height" and o.shape_name == "too_long" for o in issues)
    assert not any(o.kind == "missing-font" for o in issues)


def test_format_fit_is_actionable_and_names_the_shape() -> None:
    assert "OK" in format_fit([])
    issues = fit_report(_overflowing_deck(), theme=_LORA_INTER)
    text = format_fit(issues)
    assert "too_long" in text and "shorten" in text


def test_report_fit_prints_and_returns(capsys: pytest.CaptureFixture[str]) -> None:
    issues = report_fit(_overflowing_deck(), theme=_LORA_INTER)
    err = capsys.readouterr().err
    assert "overflow" in err and "too_long" in err
    assert issues  # also returned for programmatic use
