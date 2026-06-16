"""Predict whether text fits a Google Slides container — *before* rendering.

Where :func:`slidebox.fit.fit_report` walks a *rendered* deck and flags boxes
that overflow, this module answers the same question one box at a time, at
compile time, without building a ``Deck`` or touching python-pptx:

    >>> from slidebox.measure import measure_text, EMU_PER_INCH
    >>> r = measure_text(
    ...     "Le marché lifestyle est complètement saturé aujourd'hui.",
    ...     family="Lora", size_pt=18,
    ...     width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2,
    ... )
    >>> r.fits
    False
    >>> r.verdict
    'overflows-height'
    >>> r.recommended_min_height_emu      # grow the box to this to fit as-is
    969264
    >>> r.recommended_max_chars           # ...or trim the text to ~this many chars
    23

It measures with the *real* glyph advances of Lora, Inter and Roboto — the
three families are bundled with the package (``slidebox/fonts/*.ttf``), so the
tool works offline with zero setup. Any other family can be measured by passing
``fonts={"My Family": "/path/to.ttf"}`` (same mapping :func:`render` accepts);
unknown families fall back to a conservative ~0.6em-per-glyph estimate.

The model replicates how Slides lays out a text box: subtract the box insets,
greedy word-wrap each paragraph to the usable width, then compare the stacked
line height against the usable height. It cannot reproduce Slides' renderer to
the pixel (kerning, hyphenation, autofit), so leave a small margin — but with
true metrics it reliably catches overflow and quantifies the fix.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from slidebox.render import Fonts, _FontBook

# Measures the rendered width of `text` at `size_pt`, in points.
Measure = Callable[[str, float], float]

EMU_PER_PT = 12700
EMU_PER_INCH = 914400

# Google Slides' default text-box insets: 0.1" left/right, 0.05" top/bottom.
_DEFAULT_INSET_LR_EMU = 91440  # per side
_DEFAULT_INSET_TB_EMU = 45720  # per side
# Slides' "line spacing" is a multiplier on the font's *natural* line height
# (its ascent+descent). 1.0 == "single"; the line height itself is read per
# font, not assumed — so this default models a single-spaced box. Calibrated
# against real Google Slides: rendered line pitch == size x natural_ratio x
# this multiplier, to within ~1%.
_DEFAULT_LINE_SPACING = 1.0
_FALLBACK_LINE_RATIO = 1.2  # natural line height / em when no font file is given
_RATIO_REF_PT = 1000.0  # size at which we sample font metrics for the ratio
_GLYPH_EM = 0.6  # fallback advance per glyph when no font file is available
# A little bottom headroom so a box reported as "fits" still fits in Slides
# once its real wrapping/rounding are applied. Kept small: flooring the line
# count already drops any partial line, and the metric-based line height is
# itself ~1-4% conservative, so only a light extra cushion is warranted.
# (A larger reserve, e.g. 0.25, would wrongly reject content that fits.)
_DEFAULT_SAFETY_LINES = 0.1

#: Line-spacing multipliers slidebox's renderer applies, by card kind. Pass the
#: matching one to :func:`measure_text` when predicting a specific card.
SLIDES_BODY_LINE_SPACING = 1.6  # render._BODY_LINE_HEIGHT
SLIDES_DEFAULT_LINE_SPACING = 1.0  # headers/eyebrows/etc. leave spacing unset

#: Families bundled with the package and measurable with no setup.
BUNDLED_FAMILIES = ("Lora", "Inter", "Roboto")

VERDICT_FITS = "fits"
VERDICT_HEIGHT = "overflows-height"
VERDICT_WIDTH = "overflows-width"


def bundled_fonts() -> Fonts:
    """The :data:`BUNDLED_FAMILIES` mapped to their packaged TTF variants.

    Pass the result (or merge it) into :func:`measure_text`, :func:`render`,
    :func:`fit_report`, ``save`` or ``to_google_slides``.
    """
    from importlib.resources import files

    root = files("slidebox") / "fonts"
    out: Fonts = {}
    for fam in BUNDLED_FAMILIES:
        out[fam] = {
            "regular": str(root / f"{fam}-Regular.ttf"),
            "bold": str(root / f"{fam}-Bold.ttf"),
            "italic": str(root / f"{fam}-Italic.ttf"),
            "bold_italic": str(root / f"{fam}-BoldItalic.ttf"),
        }
    return out


@dataclass(frozen=True)
class FitResult:
    """The outcome of fitting one block of text into one container.

    Truthy when the text fits, so callers can write ``if measure_text(...):``.
    """

    fits: bool
    verdict: str  # VERDICT_FITS | VERDICT_HEIGHT | VERDICT_WIDTH
    lines_needed: int  # lines the wrapped text actually occupies
    lines_available: int  # whole lines the box can stack at this size
    line_height_pt: float  # per-line vertical advance (font metrics x spacing)
    text_height_pt: float  # height the wrapped text occupies
    box_height_pt: float  # usable height (box minus top/bottom insets)
    usable_width_pt: float  # usable width (box minus left/right insets)
    widest_word_pt: float  # widest single (whole, unbroken) word
    measured: bool  # True if a real font file was used (else estimated)
    detail: str  # human-readable summary

    # --- recommendations (how to make it fit) -----------------------------
    recommended_min_height_emu: int  # grow the box height to >= this to fit
    recommended_min_width_emu: int | None  # widen the box to >= this (width case)
    recommended_max_chars: int | None  # OR trim text to ~this many chars
    recommended_size_pt: float | None  # OR shrink the font to this size

    def __bool__(self) -> bool:
        return self.fits


def _measurer(
    family: str, bold: bool, italic: bool, fonts: Fonts | None
) -> tuple[Measure, bool, float]:
    """Return ``(measure(text, size_pt) -> width_pt, used_real_font, line_ratio)``.

    ``line_ratio`` is the font's natural line height as a fraction of the em
    (ascent+descent), i.e. the height of one "single-spaced" line. It is read
    from the actual font (it differs per family: Lora ~1.29, Inter ~1.22,
    Roboto ~1.18) and falls back to :data:`_FALLBACK_LINE_RATIO` when no file
    is available.
    """
    book = _FontBook(fonts) if fonts else None
    ref = book.pil_font(family, bold, italic, _RATIO_REF_PT) if book else None
    if book is not None and ref is not None:
        ascent, descent = ref.getmetrics()
        line_ratio = (ascent + descent) / _RATIO_REF_PT

        def measure(text: str, size_pt: float) -> float:
            fnt = book.pil_font(family, bold, italic, size_pt)
            assert fnt is not None
            return float(fnt.getlength(text))

        return measure, True, line_ratio

    def estimate(text: str, size_pt: float) -> float:
        return len(text) * _GLYPH_EM * size_pt

    return estimate, False, _FALLBACK_LINE_RATIO


def _wrap(
    words: list[str], usable_w_pt: float, measure: Measure, size_pt: float
) -> tuple[list[str], bool]:
    """Wrap ``words`` to ``usable_w_pt`` the way Google Slides does.

    Greedy by word: a word that doesn't fit the rest of the current line moves
    whole to the next line. A word that is wider than the *entire* line is then
    broken character-by-character at the right edge (Slides never lets a word
    spill past the edge) — so an over-long word costs extra lines, not width.

    Returns ``(lines, glyph_too_wide)``. ``glyph_too_wide`` is True only in the
    degenerate case where a single character is wider than the line.
    """
    space = measure(" ", size_pt)
    lines: list[str] = []
    cur = ""
    cur_w = 0.0
    glyph_too_wide = False
    for word in words:
        w = measure(word, size_pt)
        if cur and cur_w + space + w <= usable_w_pt:
            cur, cur_w = f"{cur} {word}", cur_w + space + w
            continue
        if cur:  # word won't join this line — close it and start fresh
            lines.append(cur)
            cur, cur_w = "", 0.0
        if w <= usable_w_pt:
            cur, cur_w = word, w
            continue
        # Word is wider than a whole line: break it at the right edge.
        for ch in word:
            cw = measure(ch, size_pt)
            if cur and cur_w + cw > usable_w_pt:
                lines.append(cur)
                cur, cur_w = "", 0.0
            if not cur and cw > usable_w_pt:
                glyph_too_wide = True  # a single glyph won't fit the box
            cur, cur_w = cur + ch, cur_w + cw
    lines.append(cur)
    return lines, glyph_too_wide


def measure_text(
    text: str | list[str],
    *,
    family: str,
    size_pt: float,
    width_emu: int,
    height_emu: int,
    bold: bool = False,
    italic: bool = False,
    line_spacing: float = _DEFAULT_LINE_SPACING,
    fonts: Fonts | None = None,
    inset_lr_emu: int = _DEFAULT_INSET_LR_EMU,
    inset_tb_emu: int = _DEFAULT_INSET_TB_EMU,
    safety_lines: float = _DEFAULT_SAFETY_LINES,
    min_size_pt: float = 6.0,
) -> FitResult:
    """Predict how ``text`` fits a ``width_emu`` x ``height_emu`` container.

    ``text`` may be a single string or a list of paragraphs (each wraps and
    stacks independently). ``family`` is measured with the bundled metrics for
    :data:`BUNDLED_FAMILIES`; for any other family pass ``fonts={family: path}``
    or it is estimated. Dimensions are in EMU (914400 per inch) to match the
    rest of slidebox; multiply points by :data:`EMU_PER_PT` if you have points.

    ``line_spacing`` is the Slides "line spacing" multiplier (1.0 == single);
    the single-line height itself is read from the font's own metrics, so the
    multiplier means the same thing it does in the Slides UI. slidebox renders
    body text at :data:`SLIDES_BODY_LINE_SPACING` (1.6) and headers/eyebrows at
    :data:`SLIDES_DEFAULT_LINE_SPACING` (1.0) — pass the one that matches the
    card you are predicting.

    ``safety_lines`` reserves that many lines of bottom headroom before judging
    the fit, so a "fits" verdict survives Slides' slightly different wrapping
    and rounding. Set it to 0 to measure the raw geometry.

    Returns a :class:`FitResult` whose ``verdict`` is one of ``fits``,
    ``overflows-height`` (too many lines for the height) or ``overflows-width``
    (the degenerate case where a single character is wider than the box).
    An over-long *word* is not a width overflow: Slides breaks it at the right
    edge, so it just costs extra lines and shows up as a height overflow.
    """
    if fonts is None and family in BUNDLED_FAMILIES:
        fonts = bundled_fonts()
    paragraphs = [text] if isinstance(text, str) else list(text)
    measure, measured, line_ratio = _measurer(family, bold, italic, fonts)

    usable_w_pt = (width_emu - 2 * inset_lr_emu) / EMU_PER_PT
    line_h_pt = size_pt * line_ratio * line_spacing
    # Reserve a little bottom headroom (in points) so a "fits" verdict holds up
    # under Slides' real wrapping/rounding.
    safety_pt = max(0.0, safety_lines) * line_h_pt
    usable_h_pt = (height_emu - 2 * inset_tb_emu) / EMU_PER_PT - safety_pt
    # Whole lines the box can stack at this size (at least 0).
    lines_available = max(0, int(usable_h_pt // line_h_pt)) if line_h_pt > 0 else 0

    if usable_w_pt <= 0 or usable_h_pt <= 0:
        return FitResult(
            fits=False, verdict=VERDICT_HEIGHT, lines_needed=0,
            lines_available=0, line_height_pt=line_h_pt, text_height_pt=0.0,
            box_height_pt=max(0.0, usable_h_pt),
            usable_width_pt=max(0.0, usable_w_pt), widest_word_pt=0.0,
            measured=measured, detail="container has no usable area after insets",
            recommended_min_height_emu=height_emu, recommended_min_width_emu=None,
            recommended_max_chars=0, recommended_size_pt=None,
        )

    # Wrap every paragraph (breaking over-long words at the edge, like Slides);
    # collect the line count and the widest single word (informational).
    wrapped: list[list[str]] = []
    widest_word_pt = 0.0
    glyph_too_wide = False
    lines_needed = 0
    for para in paragraphs:
        words = para.split()
        for word in words:
            widest_word_pt = max(widest_word_pt, measure(word, size_pt))
        lines, ctw = _wrap(words, usable_w_pt, measure, size_pt)
        glyph_too_wide = glyph_too_wide or ctw
        wrapped.append(lines)
        lines_needed += len(lines)

    text_height_pt = lines_needed * line_h_pt

    height_overflow = lines_needed > lines_available
    fits = not glyph_too_wide and not height_overflow

    if fits:
        verdict, detail = VERDICT_FITS, (
            f"{lines_needed} line(s) fit in {lines_available} available"
        )
    elif glyph_too_wide:
        verdict = VERDICT_WIDTH
        detail = (
            f"a single character is wider than the {usable_w_pt:.0f}pt line; "
            "the box is too narrow for even one glyph"
        )
    else:
        verdict = VERDICT_HEIGHT
        detail = (
            f"{lines_needed} line(s) need {text_height_pt:.0f}pt > "
            f"{usable_h_pt:.0f}pt box ({lines_available} line(s) fit)"
        )

    # --- recommendations ---------------------------------------------------
    # 1) Grow the box height: hold the wrapped text plus the safety headroom.
    recommended_min_height_emu = (
        round((text_height_pt + safety_pt) * EMU_PER_PT) + 2 * inset_tb_emu
    )

    # 1b) Widen the box: only for the degenerate width case — make the box at
    #     least as wide as the widest single glyph (plus insets).
    recommended_min_width_emu: int | None = None
    if glyph_too_wide:
        widest_char = max(
            (measure(ch, size_pt) for para in paragraphs for ch in para),
            default=0.0,
        )
        recommended_min_width_emu = round(widest_char * EMU_PER_PT) + 2 * inset_lr_emu

    # 2) Trim the text: how many characters fit in the available lines at the
    #    current size. None when it already fits or no line can hold a glyph.
    recommended_max_chars: int | None = None
    if not fits and lines_available >= 1 and not glyph_too_wide:
        kept = 0
        for lines in wrapped:
            if lines_available <= 0:
                break
            for line in lines:
                if lines_available <= 0:
                    break
                kept += len(line) + 1  # +1 for the space/newline to the next line
                lines_available -= 1
        recommended_max_chars = max(0, kept - 1)
        lines_available = max(0, int(usable_h_pt // line_h_pt))  # restore for caller

    # 3) Shrink the font: largest whole size <= current that fits the box.
    recommended_size_pt: float | None = None
    if not fits:
        recommended_size_pt = _largest_fitting_size(
            paragraphs, usable_w_pt, usable_h_pt, size_pt,
            line_ratio=line_ratio, line_spacing=line_spacing,
            measure=measure, min_size_pt=min_size_pt,
        )

    return FitResult(
        fits=fits, verdict=verdict, lines_needed=lines_needed,
        lines_available=lines_available, line_height_pt=line_h_pt,
        text_height_pt=text_height_pt,
        box_height_pt=usable_h_pt, usable_width_pt=usable_w_pt,
        widest_word_pt=widest_word_pt, measured=measured, detail=detail,
        recommended_min_height_emu=recommended_min_height_emu,
        recommended_min_width_emu=recommended_min_width_emu,
        recommended_max_chars=recommended_max_chars,
        recommended_size_pt=recommended_size_pt,
    )


def _largest_fitting_size(
    paragraphs: list[str],
    usable_w_pt: float,
    usable_h_pt: float,
    nominal_pt: float,
    *,
    line_ratio: float,
    line_spacing: float,
    measure: Measure,
    min_size_pt: float,
) -> float | None:
    """Largest whole point size <= ``nominal`` at which the text fits, or None."""
    size = float(int(nominal_pt))
    while size >= min_size_pt:
        line_h = size * line_ratio * line_spacing
        available = int(usable_h_pt // line_h) if line_h > 0 else 0
        needed = 0
        too_wide = False
        for para in paragraphs:
            lines, ctw = _wrap(para.split(), usable_w_pt, measure, size)
            too_wide = too_wide or ctw
            needed += len(lines)
        if not too_wide and needed <= available:
            return size
        size -= 1.0
    return None


__all__ = [
    "BUNDLED_FAMILIES",
    "EMU_PER_INCH",
    "EMU_PER_PT",
    "SLIDES_BODY_LINE_SPACING",
    "SLIDES_DEFAULT_LINE_SPACING",
    "VERDICT_FITS",
    "VERDICT_HEIGHT",
    "VERDICT_WIDTH",
    "FitResult",
    "bundled_fonts",
    "measure_text",
]
