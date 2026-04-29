# Themes

A `Theme` captures colours, fonts, and per-component styling. Set it
once on the `Presentation` and every component inherits — no prop
drilling, no repeated kwargs.

## Presets

```python
from slidebox import Presentation, themes

Presentation(theme=themes.default())    # light, Inter, sensible defaults
Presentation(theme=themes.dark())       # dark background, light text
Presentation(theme=themes.slate())      # softer blue-grey dark theme
Presentation(theme=themes.minimal())    # black-on-white, Helvetica Neue
```

## Build from scratch

```python
from slidebox import Theme, KpiTheme

brand = Theme(
    background="#0b1120",
    text_primary="#e6edf3",
    text_secondary="#8b949e",
    accent="#58a6ff",
    font_family="Inter",
    kpi=KpiTheme(
        fill="#161b22",
        accent="#58a6ff",
        corner_radius=12,
        padding_pt=20,
    ),
)
Presentation(theme=brand)
```

## Tweak a preset

```python
from slidebox import themes

coral = themes.minimal().merge(accent="#ff5a5f", font_family="IBM Plex Sans")
```

`merge()` returns a new Theme. It replaces top-level fields only —
`kpi` is kept intact unless you pass a new `KpiTheme` explicitly.

## Fields

### `Theme`
| Field            | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `background`     | Slide background. Auto-applied to every slide that doesn't override. |
| `text_primary`   | Default text colour (titles, body).                           |
| `text_secondary` | Muted text (subtitles, captions, KPI labels).                 |
| `accent`         | Brand accent (KPI bar, trend pills, etc).                     |
| `font_family`    | Default font for every text element.                          |
| `text_styles`    | Per-style overrides. Usually empty — styles are derived live from the colour/font fields above. |
| `kpi`            | `KpiTheme` sub-model (see below).                             |
| `shape_fill`     | Default Shape fill if the component doesn't set one.          |
| `shape_stroke`   | Default Shape stroke colour.                                  |

### `KpiTheme`
| Field                 | Description                                            |
| --------------------- | ------------------------------------------------------ |
| `fill`                | Card background.                                       |
| `label_color`         | Label text. `None` → `theme.text_secondary`.           |
| `value_color`         | Headline value text. `None` → `theme.text_primary`.    |
| `accent`              | Left accent bar. `None` → `theme.accent`. `""` hides.  |
| `trend_up_fill`       | Pill background for `+` trends.                        |
| `trend_down_fill`     | Pill background for `-` trends.                        |
| `trend_neutral_fill`  | Pill background otherwise.                             |
| `trend_up_text`       | Pill text colour for `+` trends.                       |
| `trend_down_text`     | Pill text colour for `-` trends.                       |
| `trend_neutral_text`  | Pill text colour otherwise.                            |
| `corner_radius`       | Card corner radius in pt.                              |
| `padding_pt`          | Inner card padding.                                    |
| `label_size_pt` / `value_size_pt` / `trend_size_pt` | Typography scale. |

## Per-component overrides

Instance kwargs always win over the theme.

```python
Title("Hi", color="#ff5a5f")                  # override theme text_primary
Kpi("Revenue", "$4.2M", fill="#ffffff")       # override theme.kpi.fill
Kpi("Revenue", "$4.2M", accent="")             # hide the accent bar
Slide(background="#000000")                   # override theme.background
```

## How composites reach the theme

During `build()`, components call `current_theme()` to read the active
`Presentation`'s theme. That's how `Kpi` knows to use `theme.kpi.accent`
without the caller threading the theme through.

If you subclass `ContainerComponent`, do the same:

```python
from slidebox.context import current_theme
from slidebox.components.base import ContainerComponent

class BrandCard(ContainerComponent):
    message: str = ""

    def build(self):
        theme = current_theme()
        fill = theme.accent if theme else "#4285f4"
        ...
```
