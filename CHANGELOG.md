# Changelog

## [Unreleased]

Pre-1.0; the public API may still change.

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
