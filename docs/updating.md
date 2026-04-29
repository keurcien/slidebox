# Updating a live deck

Every component carries a deterministic `objectId`. That's what makes
slidebox round-trip: after you `push()`, you can patch the deck later
without touching the rest of the layout.

```python
from slidebox import Updater

Updater(presentation_id) \
    .replace_text("kpi_rev_value", "$4.8M") \
    .replace_text("kpi_rev_trend", "+14%") \
    .apply()
```

## Kpi sub-ids

A `Kpi(id="kpi_rev")` forwards the id to its background shape and derives
three child ids:

| Id                | Element              |
| ----------------- | -------------------- |
| `kpi_rev`         | background card      |
| `kpi_rev_label`   | label text           |
| `kpi_rev_value`   | headline value text  |
| `kpi_rev_trend`   | trend indicator text |

## Methods

| Method                                | Purpose                                                    |
| ------------------------------------- | ---------------------------------------------------------- |
| `replace_text(id, text)`              | Delete the existing text in the shape, insert new.         |
| `update_style(id, color=..., bold=..., italic=..., size_pt=...)` | Targeted style update. |
| `replace_image(id, url)`              | Swap image URL, keep bounds.                               |
| `replace_element(id, component)`      | Delete + re-create at the current live bounds.             |
| `remove(id)`                          | `deleteObject`.                                            |
| `apply()`                             | Re-fetch live state, resolve deferred requests, dispatch.  |
| `dry_run()`                           | Return the resolved request list without dispatching.      |

## Staleness

`apply()` calls `presentations.get` **immediately** before dispatch, so
structural replacements always use the current bounds — the safest way
to coexist with users who may have edited the deck in the UI between
your runs.
