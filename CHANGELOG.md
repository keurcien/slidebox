# Changelog

## [Unreleased]

### Added
- Initial public API: `Presentation`, `Slide`, `Row`, `Col`, `Text`, `Title`, `Image`, `Shape`, `Kpi`, `Spacer`, `Updater`.
- Deterministic object IDs that round-trip between create and update flows.
- `themes.default()`, `themes.dark()`, `themes.minimal()` presets.
- Dual auth: managed helpers (service account, OAuth, ADC) + pass-through `Credentials`.
