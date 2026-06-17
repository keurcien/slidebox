# Authoring decks that fit — a guide for AI agents

This explains how to write a slidebox layout that renders correctly in Google
Slides, how to verify it at compile time, and how to iterate until every text
box fits. Read it before generating a deck.

## The one thing to internalize

**Google Slides does not shrink text to fit a box.** slidebox bakes a fixed
font size into every text frame, and Slides renders it at that size. If the
text is taller than its container, it **spills past the bottom edge** (and
visually collides with whatever is below). If a single word is wider than the
box, Slides **breaks it character-by-character** at the right edge — it never
spills sideways, it just uses more lines (which can then overflow the bottom).

So the layout contract is: **you choose the container, the font, and the size;
you are responsible for making the text fit.** Nothing rescues you at render
time. The fit checker is how you find out whether you got it right.

The workflow is a loop:

1. **Author** the layout — place containers, pick fonts/sizes with fit in mind.
2. **Compile-check** — `save(deck, ..., check=True)` (default) or `report_fit(deck)` prints every overflow.
3. **Iterate** — fix each reported box (grow it, shorten the text, or shrink the size) and re-check until the report says `OK`.

## How text is laid out (the model)

The fit checker replicates Slides to within ~1–4%:

- **Line height** `= font_size × natural_ratio × line_spacing`, where
  `natural_ratio` is the font's own ascent+descent (read from the file):
  **Lora ≈ 1.28, Inter ≈ 1.21, Roboto ≈ 1.17**. It is *not* a flat 1.2.
- **`line_spacing`** is the Slides multiplier. slidebox renders **body text at
  1.6** and headers/eyebrows/subtitles at **1.0** (single). So a 13pt body line
  occupies ≈ `13 × 1.21 × 1.6 ≈ 25pt`, not 13pt.
- **Wrapping** is greedy by word: a word that doesn't fit the rest of a line
  moves whole to the next line. A word wider than the *entire* line is broken at
  the right edge into character chunks (each chunk costs a line).
- **Insets**: Slides reserves ~0.1" left/right and ~0.05" top/bottom inside
  every text box. Usable width/height is the box minus these.
- **Capacity** = `floor(usable_height / line_height)` whole lines. A partial
  remaining line does not count.

## Step 1 — author the layout

### Fonts come from the theme, not the card

Card type owns typography; you set the *families* on the `BrandTheme`:

```python
from slidebox import BrandTheme, RGB
THEME = BrandTheme(serif_family="Lora", sans_family="Inter")  # bundled, zero setup
```

| Card | Font family | Weight | Line spacing |
|------|-------------|--------|--------------|
| `header` | `serif_family` | bold | 1.0 |
| `subtitle` | `sans_family` | regular | 1.0 |
| `eyebrow` | `serif_family` (italic) or `sans_family` (`variant="sans"`) | — | 1.0 |
| `body` | `sans_family` | regular (`**bold**` inline) | **1.6** (override per card) |
| `kpi` value/label | `sans_family` | — | 1.0 |

A single paragraph can be passed as a bare string — `body("One paragraph.")`
is the same as `body(["One paragraph."])`; use the list form for multiple
paragraphs. Body copy defaults to a loose **1.6** line spacing; for a
decorative single line (e.g. a `"★ ★ ★ ★ ★"` rating) pass
`line_spacing=1.0` so it doesn't inflate the box height.

**Lora, Inter and Roboto ship with the package** and are measured automatically
— no font files required. For any other family, pass `fonts={"Family": "/path.ttf"}`
to `save` / `to_google_slides` / `fit_report`, or it can't be measured (and is
reported as `missing-font`).

### Sizing: pin `size_pt` to control fit

- If you set **`size_pt`**, the text renders at exactly that size — this is what
  you want when you're reasoning about fit (the size you check is the size that
  renders).
- If you **omit `size_pt`**, the renderer auto-shrinks the text down (to a 7pt
  floor) to fit the box. Convenient, but it can produce tiny text; prefer an
  explicit `size_pt` and a box sized for it.

### Containers: grid, absolute EMU, or a mix

- **Grid** (preferred): `col`, `row`, `span=(cols, rows)` on a 12×8 grid.
- **Absolute**: `x`, `y`, `w`, `h` in **EMU** (914400 per inch, 12700 per point).
- **Hybrid**: combine them — pass grid args *and* one or more of `x/y/w/h`,
  and each absolute coordinate overrides the grid value for that axis. Place
  horizontally on the grid and fine-tune vertically (or vice versa):
  `header("…", col=7, span=(5, 1), y=100000)` takes x/w/h from the grid and
  only y from the absolute value. (Resolves to a single absolute box.)

Size the container for the text it must hold. Rough check while authoring:
a body box needs `lines × size_pt × natural_ratio × 1.6` points of height plus
insets, where `lines ≈ usable_width ÷ (avg_char_width)`. Don't eyeball it —
use the measurement tool (Step 2) or just build and run the compile-check.

To compute the height directly, the builder offers `min_height`, which applies
the right family and line-spacing for a card kind and returns EMU you can pass
to `h=`:

```python
b = Deck.new(title="…").slide()
h = b.min_height("Mon texte de body…", card="body", size_pt=10,
                 width_emu=3_000_000, theme=THEME)
b.body("Mon texte de body…", x=…, y=…, w=3_000_000, h=h, size_pt=10)
```

## Step 2 — predict fit before rendering (optional, precise)

`measure_text` answers "does this string fit this box?" without building a deck.
Use it when you are computing a custom box, or to choose a size up front.

```python
from slidebox import measure_text
from slidebox.measure import SLIDES_BODY_LINE_SPACING, EMU_PER_INCH

r = measure_text(
    "Les consommateurs sont submergés, les marques peinent à se démarquer.",
    family="Inter", size_pt=13,
    width_emu=3 * EMU_PER_INCH, height_emu=EMU_PER_INCH // 2,
    line_spacing=SLIDES_BODY_LINE_SPACING,   # 1.6 for body cards; 1.0 for headers
)
r.fits                        # False
r.verdict                     # "overflows-height"
r.detail                      # human-readable
r.recommended_min_height_emu  # grow the box to this to fit as-is
r.recommended_max_chars       # ...or trim the text to ~this many characters
r.recommended_size_pt         # ...or drop the font to this size
```

Notes:
- **Pass the matching `line_spacing`** (1.6 for body, 1.0 otherwise) or the
  height prediction will be wrong.
- `safety_lines` (default **0.1**) reserves a little bottom headroom so a
  "fits" verdict holds up in real Slides; pass `safety_lines=0` for raw geometry.
- Verdicts: `fits`, `overflows-height` (too many lines), `overflows-width`
  (degenerate: a single glyph is wider than the box).

## Step 3 — check at compile time

`save()` and `to_google_slides()` print a fit report to **stderr by default**
(`check=True`). This is the primary feedback signal:

```python
from slidebox import save
save(deck, "out.pptx", theme=THEME)     # also prints the report
```

```
fit check: 1 text box(es) overflow:
  slide  1  constat_body          height  text 80pt tall > box 57pt — grow the box height by ~23pt or shorten the text
```

Read each line as: **slide number · shape `object_id` · kind · what to do.**
Clean decks print `fit check: OK — every text box fits its container.`

To check without writing/uploading, call `report_fit` (prints + returns) or
`fit_report` (returns only):

```python
from slidebox import report_fit, fit_report
issues = report_fit(deck, theme=THEME)   # prints, returns list[Overflow]
issues = fit_report(deck, theme=THEME)   # silent, returns list[Overflow]
```

Each `Overflow` has `.slide_index`, `.shape_name` (the card's `object_id`),
`.kind` (`"height" | "width" | "missing-font"`), `.detail`, and `.text`.
**Always give every card an explicit `object_id`** so the report can name it.

Pass `check=False` to silence the report. To **fail hard** on overflow instead
of just printing — so a broken deck is never written or uploaded — pass
`strict=True`:

```python
save(deck, "out.pptx", theme=THEME, strict=True)   # raises SlideboxFitError
to_google_slides(deck, theme=THEME, strict=True)    # raises before uploading
```

`fit_report` / `report_fit` return a `FitReport` (a list of `Overflow` with
extras): `report.ok` is `True` when nothing overflows, and
`report.raise_if_overflow()` raises `SlideboxFitError` (whose `.issues` carries
the overflows) — convenient in CI:

```python
fit_report(deck, theme=THEME).raise_if_overflow()
```

## Step 4 — iterate

Loop until the report is clean. Pick a fix by `kind`:

| Kind | Meaning | Fixes (in order of preference) |
|------|---------|--------------------------------|
| `height` | Text needs more lines than the box holds | 1. Grow the box (more rows / bigger `h`) to `recommended_min_height_emu`. 2. Shorten the text. 3. Lower `size_pt`. |
| `width` | A single glyph is wider than the box | Widen the box (more cols / bigger `w`), or lower `size_pt`. (Rare.) |
| `missing-font` | The family has no measurable font file | Theme it to Lora/Inter/Roboto, or pass `fonts={family: path}`. |

A concrete iteration loop:

```python
def build() -> Deck: ...   # your layout

deck = build()
issues = report_fit(deck, theme=THEME)
# Read issues by .shape_name, adjust that card's span/size/text in build(),
# rebuild, and re-check. Repeat until issues == [].
while issues:
    # ...edit build() based on the reported shapes/kinds...
    deck = build()
    issues = report_fit(deck, theme=THEME)
```

Guidance when fixing:
- **Prefer growing the container** when the slide has room — it preserves the
  intended size and tone. Use `recommended_min_height_emu` as the target.
- **Shorten copy** when the box position/size is fixed by the design.
- **Lower `size_pt`** last; large drops look off-brand. `recommended_size_pt`
  tells you the largest size that fits the current box.
- After any change, **re-run the check** — fixes can push neighbouring content.

## Reference

- **Units**: `EMU_PER_INCH = 914400`, `EMU_PER_PT = 12700`. Slide canvas is
  9 144 000 × 5 143 500 EMU (16:9).
- **Bundled families**: `BUNDLED_FAMILIES = ("Lora", "Inter", "Roboto")` —
  `bundled_fonts()` returns the family→file mapping if you need it explicitly.
- **Spacing constants**: `SLIDES_BODY_LINE_SPACING = 1.6`,
  `SLIDES_DEFAULT_LINE_SPACING = 1.0`.
- **Key APIs**: `measure_text`, `FitResult`, `report_fit`, `fit_report`,
  `format_fit`, `overflows`, `FitReport`, `SlideboxFitError`,
  `save(check=…, strict=…)`, `to_google_slides(check=…, strict=…)`,
  `SlideBuilder.min_height(...)`.
- **Images**: `image(path=…)` / `image(url=…)` / `image(drive_file_id=…)`;
  `crop="cover"` (center-crop to box ratio) or `crop="contain"` (letterbox).

See `examples/calibrate_fit.py` for the calibration harness that validated this
model against real Google Slides.
