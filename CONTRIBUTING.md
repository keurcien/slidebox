# Contributing to slidebox

Thanks for helping. Slidebox is MIT-licensed and welcomes PRs.

## Local setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest -q                    # full suite (~80 tests, <1s)
ruff check src tests
mypy src
```

## Running examples

Examples require Google credentials. Either:

- Export `SLIDEBOX_SA_JSON` pointing to a service-account key, then run directly.
- Set up [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc) (`gcloud auth application-default login`) and leave the env var unset.

```bash
python examples/hello_world.py
```

## Project layout

- `src/slidebox/components/` — one file per component. Add new components here; export from `__init__.py`.
- `src/slidebox/layout/` — pure geometry solver, no IO.
- `src/slidebox/compile/` — turns a resolved tree into batchUpdate requests.
- `src/slidebox/client/` — the only module that talks to Google.
- `src/slidebox/update/` — Updater fluent API.
- `tests/unit/` — fast, hermetic.
- `tests/integration/` — mock client, exercises full flows.
- `tests/e2e/` — opt-in with real credentials.

## Pull-request checklist

- [ ] Every new public name is exported from `slidebox/__init__.py`.
- [ ] New components carry a `kind` `ClassVar` and a docstring with an example.
- [ ] Tests added under `tests/unit` (fast) + `tests/integration` when the client flow is affected.
- [ ] Ruff + mypy clean.
- [ ] CHANGELOG updated under `## [Unreleased]`.

## Design principles

- **Token-efficient authoring**. Short names, positional first args, sensible defaults. A three-KPI deck should fit in 15 lines.
- **Pure compilation**. No component method should do IO. The client is the only layer that talks to Google.
- **Deterministic IDs**. The same tree compiles to the same object IDs every time. This is what makes Updater safe.
- **Escape hatches**. Every component carries a `raw=` kwarg for edge cases the library hasn't modelled.
