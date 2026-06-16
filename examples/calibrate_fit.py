"""Empirical calibration of measure_text() against real Google Slides.

Builds one slide per font (Lora / Inter / Roboto). Each slide has six body
boxes of IDENTICAL size but graduated text length, drawn over a visible
outlined rectangle so any overflow past the box edge is obvious. Every text
card pins an explicit ``size_pt`` (so slidebox does NOT auto-shrink) and the
box uses the renderer's default insets — i.e. exactly what measure_text
assumes.

Each box is tagged (L1..L6 / I1..I6 / R1..R6); the script prints what
measure_text predicts for each tag. Upload, eyeball which boxes actually
overflow in Slides, and compare to the predictions to calibrate the model.

    uv run examples/calibrate_fit.py            # predict + write /tmp pptx
    uv run examples/calibrate_fit.py --upload   # + upload to Google Slides
"""

from __future__ import annotations

import argparse

from slidebox import RGB, BrandTheme, Deck, measure_text, save, to_google_slides
from slidebox.measure import SLIDES_BODY_LINE_SPACING

CREAM = RGB(0xFF, 0xF9, 0xED)
CARD_FILL = "#F1E4CD"
DARK = "#0B1115"
NUDE = "#D1AE9B"

SIZE_PT = 13.0
# Body cards render at 1.6 line spacing (render._BODY_LINE_HEIGHT), so predict
# with the same multiplier.
LINE_SPACING = SLIDES_BODY_LINE_SPACING
FONTS = ("Lora", "Inter", "Roboto")

# Box geometry (absolute EMU). Short boxes (capacity ~2 lines at 1.6 spacing)
# so the 3rd line spills visibly past the outline.
BOX_W = 3_500_000
BOX_H = 820_000
COL_X = (560_000, 5_084_000)
ROW_Y = (1_000_000, 2_330_000, 3_660_000)

# A word pool to grow texts to a target line count.
_POOL = ["Lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore", "magna", "aliqua", "enim", "ad", "minim", "veniam", "quis", "nostrud", "exercitation", "ullamco", "laboris", "nisi", "aliquip", "ex", "ea", "commodo"]

# A single unbreakable token, far wider than the box (width-overflow case).
_LONG_WORD = "Pseudopneumonoultramicroscopicsilicovolcanoconiosisextraordinarius"

# A very tall probe box, to count a text's raw (uncapped) line count.
_TALL = 5_000_000


def _raw_lines(text: str, font: str) -> int:
    return measure_text(
        text, family=font, size_pt=SIZE_PT, width_emu=BOX_W, height_emu=_TALL
    ).lines_needed


def _text_for_lines(font: str, target: int) -> str:
    """Grow words from the pool until the text wraps to exactly `target` lines."""
    words: list[str] = []
    i = 0
    while _raw_lines(" ".join(words) or "x", font) < target:
        words.append(_POOL[i % len(_POOL)])
        i += 1
    return " ".join(words)


def _cases(font: str) -> list[tuple[str, str]]:
    """(tag, text) pairs: graduated around the box's ~2-line capacity (1.6 sp)."""
    p = font[0]
    return [
        (f"{p}1", _text_for_lines(font, 1)),   # 1 line — fits
        (f"{p}2", _text_for_lines(font, 2)),   # 2 lines — ~at capacity
        (f"{p}3", _text_for_lines(font, 3)),   # 3 lines — just over
        (f"{p}4", _text_for_lines(font, 4)),   # 4 lines — over
        (f"{p}5", _LONG_WORD),                 # long word -> char-broken, spans lines
        (f"{p}6", _text_for_lines(font, 6)),   # way over
    ]


def build_deck(font: str) -> Deck:
    theme_id = font.lower()
    b = Deck.new(title=f"Fit calibration — {font}", object_id=f"calib_{theme_id}")
    sb = b.slide(bg="beige", label=f"calib {theme_id}", object_id=f"s_{theme_id}")
    sb = sb.eyebrow(
        f"CALIBRATION — {font} — body {SIZE_PT:g}pt — box holds ~2 lines",
        variant="sans", size_pt=12, color=DARK,
        x=560_000, y=360_000, w=8_200_000, h=400_000, object_id=f"{theme_id}_hdr",
    )
    for n, (tag, text) in enumerate(_cases(font)):
        x = COL_X[n % 2]
        y = ROW_Y[n // 2]
        sb = sb.panel(
            shape="rectangle", fill=CARD_FILL, outline=DARK, outline_pt=1.0,
            x=x, y=y, w=BOX_W, h=BOX_H, object_id=f"{tag}_box",
        ).body(
            [f"{tag}  {text}"], tone="default", size_pt=SIZE_PT,
            x=x, y=y, w=BOX_W, h=BOX_H, object_id=f"{tag}_txt",
        )
    return sb.build()


def predict(font: str) -> None:
    print(f"\n=== {font} (body {SIZE_PT:g}pt, box {BOX_W}x{BOX_H} EMU) ===")
    print(f"{'tag':4} {'verdict':16} {'lines':>5}/{'cap':<3} {'note'}")
    for tag, text in _cases(font):
        r = measure_text(
            f"{tag}  {text}", family=font, size_pt=SIZE_PT,
            width_emu=BOX_W, height_emu=BOX_H,
            line_spacing=LINE_SPACING, safety_lines=0.0,  # raw geometry
        )
        flag = "FIT " if r.fits else "OVER"
        print(f"{tag:4} {r.verdict:16} {r.lines_needed:>5}/{r.lines_available:<3} "
              f"{flag} {r.detail}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibrate measure_text vs Slides.")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--output-prefix", default="/tmp/calib_")
    args = ap.parse_args()

    for font in FONTS:
        deck = build_deck(font)
        theme = BrandTheme(serif_family=font, sans_family=font, beige=CREAM)
        predict(font)
        path = save(deck, f"{args.output_prefix}{font.lower()}.pptx", theme=theme)
        print(f"saved -> {path}")
        if args.upload:
            g = to_google_slides(deck, name=f"Fit calibration — {font}", theme=theme)
            print(f"UPLOADED {font}: {g.url}")


if __name__ == "__main__":
    main()
