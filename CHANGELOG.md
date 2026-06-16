# Changelog

## [Unreleased]

Pre-1.0; the public API may still change.

### Added (0.1.0.dev1) — compile-time fit checking

- **Bundled fonts**: Lora, Inter and Roboto (regular/bold/italic/bold-italic)
  ship with the package and are measured automatically — no font files needed.
  `bundled_fonts()` / `BUNDLED_FAMILIES` expose them.
- **`measure_text(...) -> FitResult`**: predict whether a string fits a
  container *before* rendering, with actionable recommendations
  (`recommended_min_height_emu`, `recommended_max_chars`, `recommended_size_pt`).
- **Calibrated line-fit model** (validated against real Google Slides): line
  height = `size × font-natural-ratio × line_spacing`; body renders at 1.6
  spacing. Over-long words are **broken character-by-character** at the edge
  (no horizontal spill), matching Slides. `fit_report` no longer under-counts
  height. A small `safety_lines` reserve (default 0.1) guards the boundary.
- **Compile-time report**: `save()` and `to_google_slides()` print a fit report
  to stderr by default (`check=True`), naming each overflowing box and the fix.
  New `report_fit`, `format_fit`, `overflows`; `fit_report` / `missing_families`
  now take `fonts` optionally (bundled families resolve automatically).
- Added `pillow` as a dependency (real-font measurement).
- See `docs/authoring-decks.md` and `examples/calibrate_fit.py`.

### Summary

slidebox builds standardised, on-brand decks from a declarative,
LLM-friendly builder. A typed `Deck` (Pydantic) is placed on a 12 × 8
grid, rendered to an in-memory `pptx.Presentation` via python-pptx, and
either saved as `.pptx` (`save`) or uploaded to Drive and converted to
native Google Slides (`to_google_slides`, in memory — no temp file).

- **Card types**: `header`, `subtitle`, `eyebrow`, `body`, `kpi`,
  `image`, `logo`. Card type drives typography and colour (`BrandTheme`);
  the user never sets fonts or sizes.
- **Text fitting**: the renderer sizes each text box to fit, from real
  font metrics when font files are supplied (`render(deck, fonts=…)`),
  else a conservative estimate. `fit_report(deck, fonts)` verifies, with
  Pillow, that nothing overflows (height) or breaks mid-word (width).
- **Charts**: embed matplotlib (or any) figures as images via
  `image(source_url=…)`; see `examples/kpi_report.py`.
- **Update in place**: `to_google_slides(deck, file_id=…)` replaces an
  existing file's content, keeping the same URL.
- `object_id` is set as each rendered shape's name.

### Auth

Application Default Credentials by default (Drive scope); a
`CredentialsProvider` protocol lets an OAuth app supply a token.
