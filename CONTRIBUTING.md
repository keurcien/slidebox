# Contributing to slidebox

Thanks for helping. Slidebox is MIT-licensed and welcomes PRs.

## Local setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest -q                    # full suite (<1s)
ruff check src tests
mypy src
```

## Project layout

- `src/slidebox/schema.py` — Pydantic models (`Deck` / `Slide` / `Card`),
  the source of truth. All validation lives here.
- `src/slidebox/builder.py` — the chained builder (`Deck.new().slide()…`).
- `src/slidebox/grid.py` — 12 × 8 cell → EMU translation, overlap/bounds.
- `src/slidebox/theme.py` — `BrandTheme` colour/font tokens.
- `src/slidebox/render.py` — turns a `Deck` into a python-pptx
  `Presentation` (the translation boundary; no IO).
- `src/slidebox/drive.py` — `save()` / `to_google_slides()`; the only
  module that does IO (disk + Drive).
- `src/slidebox/fit.py` — measure, with real font files, whether text fits.
- `src/slidebox/types.py` — `RGB`, EMU constants.
- `tests/` — flat: `test_schema.py`, `test_grid.py`, `test_builder.py`,
  `test_render.py`, `test_fit.py`, `test_smoke.py`.

Card types: `header`, `subtitle`, `eyebrow`, `body`, `kpi`, `image`,
`logo`. The runnable example is `examples/kpi_report.py`.

## Checking that text fits (real fonts)

The renderer sizes text with a conservative width estimate. To verify
fit *exactly* for a specific typeface, give `fit_report` the font files —
it measures every rendered run with Pillow and flags overflow:

```python
from slidebox import fit_report
fonts = {
    "Sangbleu Republic": {"regular": "fonts/SB-Regular.otf",
                          "bold": "fonts/SB-Bold.otf",
                          "italic": "fonts/SB-Italic.otf"},
    "Maison Neue": "fonts/MaisonNeue-Book.otf",   # one file is fine
}
for o in fit_report(deck, fonts):
    print(o.slide_index, o.shape_name, o.kind, o.detail)  # "height" | "width"
```

`kind="height"` = text taller than its box (spills onto the next card);
`kind="width"` = a single word wider than the line (breaks mid-word).
Font files only need to exist here — they need not be installed. Use
`missing_families(deck, fonts)` to list families you still need to supply.
`examples/kpi_report.py --check` runs this over the example deck.

## Adding a card type

1. Add a Pydantic model in `schema.py` and register it in the `Card` union.
2. Add a builder method in `builder.py`.
3. Add an `_emit_*` in `render.py` and register it in `_EMITTERS`.
4. Add a test in `test_render.py`.

## Pull-request checklist

- [ ] Every new public name is exported from `slidebox/__init__.py`.
- [ ] Tests added/updated under `tests/` (`test_render.py` for new cards).
- [ ] Ruff + mypy clean.
- [ ] CHANGELOG updated under `## [Unreleased]`.

## Design principles

- **LLM-friendly authoring**. Short names, sensible defaults, a fixed
  card vocabulary. A three-KPI deck should fit in a dozen lines.
- **Pure rendering**. `render()` is a pure function of the `Deck` and
  does no IO; only `drive.py` touches disk or the network.
- **Deterministic decks**. The same source builds the same `Deck` and its
  canonical JSON every time — this is what makes refresh-in-place safe.
- **The schema is the contract**. Validate at model-build time; fail fast
  and loud on overlaps, out-of-bounds spans, and duplicate ids.
