# slidebox

Grid-based, on-brand decks from Python. A declarative, LLM-friendly
builder compiles a typed deck to **PowerPoint (.pptx)** via python-pptx,
and converts to **native Google Slides** on upload to Drive.

```python
from slidebox import Deck, save, to_google_slides

deck = (
    Deck.new(title="Q1 KPIs")
    .slide(bg="beige")
        .header("A quiet quarter.", size="display", col=1, row=2, span=(10, 2))
        .kpi(label="Revenue",   value="4,2", unit="M€", delta="+12%",
             delta_dir="up", size="md", col=1, row=5, span=(4, 3), object_id="k_rev")
        .kpi(label="Users",     value="58",  unit="K",  delta="+8%",
             delta_dir="up", size="md", col=5, row=5, span=(4, 3), object_id="k_users")
        .kpi(label="Retention", value="94",  unit="%",  delta="+2 pts",
             delta_dir="up", size="md", col=9, row=5, span=(4, 3), object_id="k_ret")
).build()

save(deck, "q1.pptx")                       # local PowerPoint
g = to_google_slides(deck, name="Q1 KPIs")  # native Google Slides on Drive
print(g.url)
```

Refresh the same deck next quarter — same URL, only the numbers change:

```python
to_google_slides(build_with_fresh_data(), file_id=g.id)   # updates in place
```

## Install

```bash
pip install slidebox
```

Pulls `python-pptx` (rendering) and `google-api-python-client` + `google-auth`
(Drive upload).

## How it works

- **Builder** — chain `.slide()` and card methods: `header`, `subtitle`,
  `eyebrow`, `body`, `kpi`, `image`, `logo`. `col` / `row` / `span` place
  each card on a 12 × 8 grid. Card type drives typography and colour — you
  never set fonts or sizes.
- **Schema** — the builder produces a typed, validated Pydantic `Deck`
  (the source of truth): no overlapping cards, no out-of-bounds spans,
  no duplicate ids.
- **Render** — `render(deck)` draws the deck into an in-memory
  `pptx.Presentation`, sizing text to fit each box. `save()` writes a
  `.pptx`; `to_google_slides()` uploads (in memory, no temp file) and
  converts to Google Slides.
- **Charts** — embed matplotlib (or any) figures as images via
  `image(source_url=…)`. See `examples/kpi_report.py`.

The runnable example is **`examples/kpi_report.py`** — a 6-slide weekly
report with KPI cards and matplotlib charts on fake data.

## Auth

`to_google_slides()` uses Application Default Credentials by default:

```bash
gcloud auth application-default login \
    --scopes=https://www.googleapis.com/auth/drive
```

A `CredentialsProvider` protocol lets an OAuth web app supply a token.

## Why slidebox

- **LLM-friendly authoring** — short, declarative builder; sensible
  defaults; a fixed card vocabulary.
- **On-brand by construction** — themes map every colour and font; card
  type owns typography, and text auto-fits its box (`fit_report` verifies).
- **Two outputs, one deck** — offline `.pptx` or native Google Slides.
- **Refreshable** — deterministic render + update-in-place keeps a deck
  at one stable link, quarter after quarter.

## Status

Pre-1.0. API may change. See [CHANGELOG.md](CHANGELOG.md).

## License

MIT.
