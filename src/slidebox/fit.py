"""Measure whether rendered text actually fits its box, using real fonts.

The renderer sizes text with a conservative width estimate (≈0.6em per
glyph). That prevents gross overflow but can't know the true metrics of a
specific typeface. Give this module the font *files* and it measures the
exact width of every run with Pillow, wraps it into each box, and reports:

- **height overflow** — the wrapped text is taller than its box, so it
  would spill onto the card below.
- **width overflow** — a single unbreakable word is wider than the line,
  so it breaks mid-word (the "CRM" → "CR/M" case).

It walks the *rendered* `pptx.Presentation` (shape names = object ids), so
it verifies what slidebox truly produced, not a reimplementation of it.
Fonts only need to exist as files here — they need not be installed.

    from slidebox import fit_report
    fonts = {
        "Sangbleu Republic": {
            "regular": "fonts/SangBleu-Regular.otf",
            "bold": "fonts/SangBleu-Bold.otf",
            "italic": "fonts/SangBleu-Italic.otf",
        },
        "Maison Neue": "fonts/MaisonNeue-Book.otf",  # single file is fine
    }
    for o in fit_report(deck, fonts):
        print(o.slide_index, o.shape_name, o.kind, o.detail)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from slidebox.render import Fonts, _FontBook, render
from slidebox.schema import Deck
from slidebox.theme import BrandTheme

# python-pptx default text-box insets (EMU): 0.1" L/R, 0.05" T/B.
_DEFAULT_INSET_LR = 91440
_DEFAULT_INSET_TB = 45720
_EMU_PER_PT = 12700


@dataclass(frozen=True)
class Overflow:
    """One text box whose content does not fit its box."""

    slide_index: int  # 1-based
    shape_name: str  # the card's object_id
    kind: str  # "height" | "width" | "missing-font"
    detail: str
    text: str  # excerpt of the offending text


@dataclass
class _Token:
    text: str
    font: Any  # PIL ImageFont
    size_pt: float


def _line_spacing(para: Any) -> float:
    """The paragraph's line-spacing *multiplier* (1.0 == single).

    The font's natural single-line height is applied separately, so an unset
    spacing means single (1.0), not a 1.2 fudge.
    """
    ls = para.line_spacing
    if ls is None:
        return 1.0
    if isinstance(ls, (int, float)):
        return float(ls)
    # A Length (absolute) line spacing expressed in pt — approximated as a
    # multiple of the paragraph's nominal size by the caller; treat as 1.0.
    return 1.0


def _natural_ratio(font: Any) -> float:
    """Font's natural line height (ascent+descent) as a fraction of its size."""
    ascent, descent = font.getmetrics()
    size = max(1, getattr(font, "size", 0) or 1)
    return float((ascent + descent) / size)


def _wrap_lines(tokens: list[_Token], usable_w_pt: float) -> tuple[int, bool]:
    """Greedy word-wrap, breaking over-long words at the edge as Slides does.

    Returns ``(line_count, glyph_too_wide)``. ``glyph_too_wide`` is True only
    when a single character is wider than the line (box too narrow for a glyph).
    """
    if not tokens:
        return 1, False
    space = tokens[0].font.getlength(" ")
    lines = 1
    cur = 0.0
    glyph_too_wide = False
    for tok in tokens:
        w = tok.font.getlength(tok.text)
        if cur > 0 and cur + space + w <= usable_w_pt:
            cur += space + w
            continue
        if cur > 0:  # word won't join this line — wrap to a fresh one
            lines += 1
            cur = 0.0
        if w <= usable_w_pt:
            cur = w
            continue
        # Word is wider than a whole line: break it character by character.
        for ch in tok.text:
            cw = tok.font.getlength(ch)
            if cur > 0 and cur + cw > usable_w_pt:
                lines += 1
                cur = 0.0
            if cur == 0 and cw > usable_w_pt:
                glyph_too_wide = True
            cur += cw
    return lines, glyph_too_wide


def _merged_fonts(fonts: Fonts | None) -> Fonts:
    """Bundled Lora/Inter/Roboto plus any caller-supplied families (override)."""
    from slidebox.measure import bundled_fonts

    merged = bundled_fonts()
    if fonts:
        merged.update(fonts)
    return merged


def fit_report(
    deck: Deck,
    fonts: Fonts | None = None,
    *,
    theme: BrandTheme | None = None,
) -> list[Overflow]:
    """Render `deck` and report every text box that doesn't fit its box.

    `fonts` maps a family name (as used by the theme, e.g. "Maison Neue") to
    either a single font-file path or a dict of variant paths with keys
    `regular` / `bold` / `italic` / `bold_italic`. Lora, Inter and Roboto are
    measured from the bundled files automatically, so `fonts` is only needed
    for other families.
    """
    merged = _merged_fonts(fonts)
    # Render with the same fonts so we measure the renderer's actual output.
    prs = render(deck, theme=theme, fonts=merged)
    return overflows(prs, merged)


def overflows(prs: Any, fonts: Fonts | None = None) -> list[Overflow]:
    """Report every text box in an already-rendered Presentation that overflows.

    Use this when you have the `pptx.Presentation` in hand (e.g. inside
    `save` / `to_google_slides`) and want to avoid rendering twice.
    """
    book = _FontBook(_merged_fonts(fonts))
    issues: list[Overflow] = []

    for si, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            tf = shape.text_frame
            name = shape.name
            ml = tf.margin_left if tf.margin_left is not None else _DEFAULT_INSET_LR
            mr = tf.margin_right if tf.margin_right is not None else _DEFAULT_INSET_LR
            mt = tf.margin_top if tf.margin_top is not None else _DEFAULT_INSET_TB
            mb = tf.margin_bottom if tf.margin_bottom is not None else _DEFAULT_INSET_TB
            usable_w = (shape.width - ml - mr) / _EMU_PER_PT
            usable_h = (shape.height - mt - mb) / _EMU_PER_PT
            if usable_w <= 0 or usable_h <= 0:
                continue

            total_h = 0.0
            missing_here = False
            for para in tf.paragraphs:
                runs = [r for r in para.runs if r.text]
                if not runs:
                    continue
                tokens: list[_Token] = []
                max_size = 0.0
                max_font: Any = None
                for run in runs:
                    size_pt = run.font.size.pt if run.font.size is not None else 12.0
                    fnt = book.pil_font(
                        run.font.name or "", bool(run.font.bold),
                        bool(run.font.italic), size_pt,
                    )
                    if fnt is None:
                        missing_here = True
                        continue
                    if size_pt >= max_size:
                        max_size, max_font = size_pt, fnt
                    for word in run.text.split(" "):
                        if word:
                            tokens.append(_Token(word, fnt, size_pt))
                if missing_here or not tokens or max_font is None:
                    continue
                lines, glyph_too_wide = _wrap_lines(tokens, usable_w)
                # Line pitch == size x font's natural ratio x spacing multiplier,
                # matching how Slides actually lays the paragraph out.
                line_h = max_size * _natural_ratio(max_font) * _line_spacing(para)
                total_h += lines * line_h
                if glyph_too_wide:
                    issues.append(Overflow(
                        si, name, "width",
                        f"a single glyph is wider than the {usable_w:.0f}pt line "
                        "(box too narrow for one character)",
                        para.text[:60],
                    ))

            if missing_here:
                issues.append(Overflow(
                    si, name, "missing-font",
                    "no font file provided for a run's family; not measured",
                    tf.text[:60],
                ))
            elif total_h > usable_h:
                over = total_h - usable_h
                issues.append(Overflow(
                    si, name, "height",
                    f"text {total_h:.0f}pt tall > box {usable_h:.0f}pt — grow the "
                    f"box height by ~{over:.0f}pt or shorten the text",
                    tf.text[:60],
                ))

    return issues


def format_fit(issues: list[Overflow]) -> str:
    """A compact, console-ready summary of a fit report."""
    if not issues:
        return "fit check: OK — every text box fits its container."
    lines = [f"fit check: {len(issues)} text box(es) overflow:"]
    for o in issues:
        lines.append(
            f"  slide {o.slide_index:>2}  {o.shape_name:<22} {o.kind:<7} {o.detail}"
        )
    return "\n".join(lines)


def report_fit(
    deck: Deck,
    fonts: Fonts | None = None,
    *,
    theme: BrandTheme | None = None,
    file: Any = None,
) -> list[Overflow]:
    """Run `fit_report` and print a console-ready summary (to stderr by default).

    Returns the issues so callers can also act on them programmatically.
    """
    import sys

    issues = fit_report(deck, fonts, theme=theme)
    print(format_fit(issues), file=file if file is not None else sys.stderr)
    return issues


def missing_families(
    deck: Deck, fonts: Fonts | None = None, *, theme: BrandTheme | None = None
) -> set[str]:
    """Families the deck uses for which no font file is available (incl. bundled)."""
    merged = _merged_fonts(fonts)
    book = _FontBook(merged)
    prs = render(deck, theme=theme, fonts=merged)
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.text and run.font.name:
                        book.path(run.font.name, bool(run.font.bold),
                                  bool(run.font.italic))
    return set(book.missing)


__all__ = [
    "Fonts",
    "Overflow",
    "fit_report",
    "format_fit",
    "missing_families",
    "overflows",
    "report_fit",
]
