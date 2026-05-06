# slidebox

Declarative Google Slides generator. Write decks with context managers, push to Google, patch later without rebuilding.

```python
from slidebox import Presentation, Slide, Row, Title, Kpi

with Presentation(title="Q1 KPIs") as deck:
    with Slide():
        Title("Q1 Performance")
        with Row(gap=16):
            Kpi("Revenue",   "$4.2M", trend="+12%", id="k_rev")
            Kpi("Users",     "58K",   trend="+8%",  id="k_users")
            Kpi("Retention", "94%",   trend="+2%",  id="k_ret")

deck.push()                                    # creates the deck
```

Later, patch a single value without rebuilding:

```python
from slidebox import Updater

Updater(deck.presentation_id) \
    .replace_text("k_rev", "$4.8M") \
    .apply()
```

## Install

```bash
pip install slidebox
```

## Auth

Slidebox accepts any `google.oauth2.Credentials` object, a raw OAuth access token, a service-account JSON path, an OAuth client-secrets file, or falls back to Application Default Credentials.

```python
# Explicit service account
Presentation(title="...", service_account_file="sa.json")

# Pre-built credentials
Presentation(title="...", credentials=my_creds)

# Raw OAuth access token (e.g. when the host already brokered the flow)
Presentation(title="...", access_token=tok)
# Optionally add refresh_token / client_id / client_secret for auto-refresh

# Application default credentials (GCE, Cloud Run, gcloud auth)
Presentation(title="...")
```

## Why slidebox

- **Token-efficient authoring** — short component names, sensible defaults, LLM-friendly.
- **Customisable** — themes, `raw=` escape hatch on every component, subclass to extend.
- **Editable decks** — deterministic object IDs mean the same script can patch a live presentation.
- **One batchUpdate** — atomic creation; no half-built decks.

## Status

Pre-1.0. API may change. See [CHANGELOG.md](CHANGELOG.md).

## License

MIT.
