# Layout

Slidebox ships a weight-based flex solver (inspired by CSS flexbox) and a
grid helper. All dimensions compile to integer EMU — the unit Google
Slides uses internally.

## Units

Accept `pt`, `inches`, `px`, `emu`, or a raw string.

```python
from slidebox import pt, inches, px

Col(gap=pt(24), padding=inches(0.5))
Col(gap="24pt", padding="0.5in")    # strings also work
```

## Flex (Row / Col)

```python
with Col(gap=24, padding=48, align="start"):
    Title("Dashboard")
    with Row(gap=16):
        Kpi("Revenue",   "$4.2M", trend="+12%")
        Kpi("Users",     "58K",   trend="+8%")
        Kpi("Retention", "94%",   trend="+2%")
```

- `gap`: space between children.
- `padding`: inset from parent bounds. Int, `(vert, horiz)`, or `(t, r, b, l)`.
- `align`: cross-axis. `start | center | end | stretch`.
- `flex=N`: weight when nested inside another flex container.

## Sizing

Children without an explicit size take a `flex=1` share of the remaining
space. Children with a fixed `width` / `height` are honoured first; the
flex pool divides what's left.

## Grid

```python
with Grid(columns=3, gap=16):
    for metric in metrics:
        Kpi(metric.label, metric.value, trend=metric.trend)
```

## Canvas size

Default: Google's 16:9 (720 pt × 405 pt). Override per presentation:

```python
from slidebox import Bounds, pt, Presentation

Presentation(canvas=Bounds(0, 0, pt(960), pt(540)))     # widescreen
```
