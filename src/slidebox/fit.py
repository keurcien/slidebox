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
_DEFAULT_LINE_SPACING = 1.2


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
    ls = para.line_spacing
    if ls is None:
        return _DEFAULT_LINE_SPACING
    if isinstance(ls, (int, float)):
        return float(ls)
    # A Length (absolute) line spacing expressed in pt — approximated as a
    # multiple of the paragraph's nominal size by the caller; treat as 1.0.
    return 1.0


def _wrap_lines(tokens: list[_Token], usable_w_pt: float) -> tuple[int, float]:
    """Greedy word-wrap. Returns (line_count, widest_single_word_pt)."""
    lines = 1
    cur = 0.0
    space = tokens[0].font.getlength(" ") if tokens else 0.0
    widest_word = 0.0
    for tok in tokens:
        w = tok.font.getlength(tok.text)
        widest_word = max(widest_word, w)
        add = w if cur == 0 else space + w
        if cur + add <= usable_w_pt or cur == 0:
            cur += add
        else:
            lines += 1
            cur = w
    return lines, widest_word


def fit_report(
    deck: Deck,
    fonts: Fonts,
    *,
    theme: BrandTheme | None = None,
) -> list[Overflow]:
    """Render `deck` and report every text box that doesn't fit its box.

    `fonts` maps a family name (as used by the theme, e.g. "Maison Neue") to
    either a single font-file path or a dict of variant paths with keys
    `regular` / `bold` / `italic` / `bold_italic`.
    """
    book = _FontBook(fonts)
    # Render with the same fonts so we measure the renderer's actual output.
    prs = render(deck, theme=theme, fonts=fonts)
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
                for run in runs:
                    size_pt = run.font.size.pt if run.font.size is not None else 12.0
                    max_size = max(max_size, size_pt)
                    fnt = book.pil_font(
                        run.font.name or "", bool(run.font.bold),
                        bool(run.font.italic), size_pt,
                    )
                    if fnt is None:
                        missing_here = True
                        continue
                    for word in run.text.split(" "):
                        if word:
                            tokens.append(_Token(word, fnt, size_pt))
                if missing_here or not tokens:
                    continue
                lines, widest_word = _wrap_lines(tokens, usable_w)
                total_h += lines * max_size * _line_spacing(para)
                if widest_word > usable_w:
                    issues.append(Overflow(
                        si, name, "width",
                        f"word {widest_word:.0f}pt wide > line {usable_w:.0f}pt "
                        "(breaks mid-word)",
                        para.text[:60],
                    ))

            if missing_here:
                issues.append(Overflow(
                    si, name, "missing-font",
                    "no font file provided for a run's family; not measured",
                    tf.text[:60],
                ))
            elif total_h > usable_h:
                issues.append(Overflow(
                    si, name, "height",
                    f"text {total_h:.0f}pt tall > box {usable_h:.0f}pt",
                    tf.text[:60],
                ))

    return issues


def missing_families(deck: Deck, fonts: Fonts, *, theme: BrandTheme | None = None) -> set[str]:
    """Families the deck uses for which no font file was provided."""
    book = _FontBook(fonts)
    prs = render(deck, theme=theme, fonts=fonts)
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


__all__ = ["Fonts", "Overflow", "fit_report", "missing_families"]
