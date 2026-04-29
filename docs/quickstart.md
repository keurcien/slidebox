# Quickstart

## Install

```bash
pip install slidebox
```

## Create a deck

```python
from slidebox import Presentation, Slide, Title, Text

with Presentation(title="Q1 Review") as deck:
    with Slide():
        Title("Q1 Performance")
        Text("Revenue up 23% YoY")

deck.push()
print(deck.presentation_id)
```

`Presentation` is the root — and the context manager scope in which every
descendant automatically attaches to its parent. `push()` resolves the
layout, compiles to a single atomic `batchUpdate`, and dispatches.

## Authenticate

Slidebox accepts any of:

```python
# 1. Service account
Presentation(service_account_file="sa.json")

# 2. Pre-built google-auth Credentials
Presentation(credentials=my_creds)

# 3. Application Default Credentials (gcloud auth, Cloud Run, GCE)
Presentation()
```

## Update the same deck later

```python
from slidebox import Updater

Updater(deck.presentation_id) \
    .replace_text("k_rev", "$4.8M") \
    .apply()
```

Deterministic object IDs mean the script that created the deck and the
script that patches it can be written independently, weeks apart.
