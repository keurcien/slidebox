# Slidebox layout catalog

Reusable slide layouts reverse-engineered from the Choose pitch decks and
built with the slidebox builder. Each layout below lists **when to use it**, a
**code snippet**, and the **recommended max characters** per text area so copy
stays on one screen and doesn't overflow.

All layouts are implemented in [`examples/constat_slide.py`](examples/constat_slide.py).

---

## Shared conventions

**Theme** — one `BrandTheme` drives every slide: Lora (serif) for headlines,
Inter (sans) for everything else, on a `#FFF9ED` cream background.

```python
from slidebox import RGB, BrandTheme, Deck, TableCell, save, to_google_slides

THEME = BrandTheme(serif_family="Lora", sans_family="Inter",
                   beige=RGB(0xFF, 0xF9, 0xED))
```

**Palette** (set `fill` / `color` with these exact hexes for off-palette accents):

| Token        | Hex       | Used for                                   |
|--------------|-----------|--------------------------------------------|
| cream (bg)   | `#FFF9ED` | slide background (`bg="beige"`)            |
| panel        | `#F9F0E0` | side panels, decorative shapes, table head |
| card         | `#F1E4CD` | KPI card fills                             |
| nude         | `#D1AE9B` | timeline axis/nodes, rating stars, quotes  |
| ink          | `#0B1115` | headlines / primary text (auto on light)   |
| grey-700     | `#434647` | body copy (`tone="muted"`)                 |
| grey-500     | `#8A8D8F` | eyebrows / labels (eyebrow default)        |

**Placement** — every card takes *either* grid cells (`col`, `row`, `span` on a
12 × 8 grid) *or* absolute EMU (`x`, `y`, `w`, `h`). The slide canvas is
**9 144 000 × 5 143 500 EMU** (16:9). Handy conversions: `914400 EMU = 1 inch`,
`12700 EMU = 1 pt`. Use the grid for quick on-brand placement; use absolute EMU
to reproduce a precise design or to bleed past the grid's gutters.

**Text sizing** — pass `size_pt=` for an exact point size (no auto-fit). The
character limits below are conservative single-box capacities at that size
(≈0.55 em/glyph) — staying under them guarantees no overflow. Use `**double
asterisks**` inside `body()` for inline bold, and `align="center"|"right"`.

---

## 1 · Split Statement

A full-height image panel on one side; eyebrow + headline + body on the other.
Best for a **section opener or a single strong claim** backed by one photo.

```
┌───────────┬──────────────────────┐
│           │  EYEBROW             │
│   image   │  Big serif headline  │
│   panel   │  Supporting body…    │
└───────────┴──────────────────────┘
```

```python
(b.slide(bg="beige")
 .panel(x=0, y=0, w=4131600, h=5143500, fill="#F9F0E0")          # bleed panel
 .image(source_url="photo.jpg", col=1, row=1, span=(5, 8))
 .eyebrow("LE CONSTAT", col=7, row=2, span=(5, 1), variant="sans", size_pt=12)
 .header("Le marché lifestyle est saturé", size_pt=24, col=7, row=3, span=(5, 2))
 .body(["First paragraph…", "Second, **emphasised** paragraph."],
       col=7, row=5, span=(5, 3), tone="muted", size_pt=10, strong=[1]))
```

| Component | Font · size | Max chars (≈) |
|-----------|-------------|---------------|
| Eyebrow   | Inter 12    | **36** (1 line) |
| Headline  | Lora 24     | **36** (2 × 18) |
| Body      | Inter 10    | **250** (≈6 lines) |

---

## 2 · Stat Cards

An intro text block beside a 2 × 2 grid of KPI cards (big number + caption on a
rounded fill). Use for an **at-a-glance metrics overview**.

```
EYEBROW                 ┌──────┐ ┌──────┐
Headline                │500 K │ │  15  │
Intro copy…             └──────┘ └──────┘
                        ┌──────┐ ┌──────┐
                        │ 80 % │ │ 1/5  │
                        └──────┘ └──────┘
```

```python
# one card (repeat for the 2x2 grid)
(b.panel(rounded=True, fill="#F1E4CD", x=4543975, y=841050, w=2140200, h=1692600)
 .header("500 K", size_pt=32, x=4762062, y=1082100, w=1524300, h=677100)
 .body(["Weekly Active Users"], tone="muted", size_pt=10,
       x=4762062, y=1759200, w=1524300, h=515700))
```

> Place the card fill, number, and label as separate absolute boxes (the number
> sits inset inside the card — don't share the card's origin or it hugs the edge).

| Component   | Font · size | Max chars (≈) |
|-------------|-------------|---------------|
| Eyebrow     | Inter 12    | **37** (1 line) |
| Headline    | Lora 24     | **36** (2 × 18) |
| Intro body  | Inter 10    | **135** (≈3 lines) |
| KPI number  | Lora 32     | **5** (e.g. "500 K") |
| KPI caption | Inter 10    | **36** (2 × 18) |

---

## 3 · Process Timeline

A horizontal axis with evenly spaced nodes; each step has a date tag, a short
title, and a description. Use for a **chronological / how-it-works flow**
(3–4 steps).

```
EYEBROW                                   Section title
●─────────●─────────●─────────●──────►
JOUR J    PENDANT   J+7       J+30
title     title     title     title
body…     body…     body…     body…
```

```python
(b.slide(bg="beige")
 .eyebrow("1. LES DROPS ÉPHÉMÈRES", col=1, row=1, span=(6, 1),
          variant="sans", size_pt=12)
 .header("Après & Pendant", size_pt=24, col=7, row=1, span=(6, 1))
 .panel(fill="#D1AE9B", rounded=True, x=-23025, y=1660775, w=8798700, h=36600)  # axis
 .panel(shape="ellipse", fill="#D1AE9B", outline="#FFF9ED", outline_pt=3,
        x=395191, y=1578025, w=204000, h=204000))                              # node
# per step (cols 1-3, 4-6, 7-9, 10-12):
(b.eyebrow("JOUR J", col=1, row=4, span=(3, 1), variant="sans", size_pt=14, color="#D1AE9B")
 .header("On met en ligne", size_pt=14, col=1, row=5, span=(3, 1))
 .body(["**Bold lead.** Rest of the step description."],
       col=1, row=6, span=(3, 3), tone="muted", size_pt=10))
```

| Component     | Font · size | Max chars (≈) |
|---------------|-------------|---------------|
| Eyebrow       | Inter 12    | **44** |
| Section title | Lora 24     | **22** |
| Step date tag | Inter 14    | **17** |
| Step title    | Lora 14     | **17** (keep ≤ 2 short words) |
| Step body     | Inter 10    | **140** (≈6 lines) |

---

## 4 · Photo Gallery

A centered title/subtitle over a single row of photos (lightly tilted, white
frame). Use to **show a collection of work / products** with minimal text.

```
            EYEBROW (centered)
        Centered serif headline
          Centered subtitle…
   [img] [img] [img] [img] [img]
```

```python
(b.slide(bg="beige")
 .eyebrow("3. LES PROJETS EXCLUSIFS", variant="sans", size_pt=12, align="center",
          x=2856600, y=516450, w=3430800, h=369300)
 .header("Des projets uniques…", size_pt=24, align="center",
         x=1264400, y=885750, w=6615299, h=978899)
 .body(["Centered **lead** + supporting line."], tone="muted", size_pt=10,
       align="center", x=1726400, y=1940850, w=5691300, h=338700)
 .image(source_url="p1.jpg", outline="#FFFFFF", outline_pt=2.5, rotation=-4,
        x=-274026, y=2658956, w=1740953, h=2577211))   # one of ~5 photos
```

| Component | Font · size | Max chars (≈) |
|-----------|-------------|---------------|
| Eyebrow   | Inter 12 (center) | **37** |
| Headline  | Lora 24 (center)  | **74** (2 lines) |
| Subtitle  | Inter 10 (center) | **76** (1 line) |

---

## 5 · Gallery with Captions

Centered title, a row of three framed photos over a colored band, and three
centered caption columns (title + detail). Use for a **three-way comparison or
category showcase**.

```
          Centered headline
   [ img ]    [ img ]    [ img ]
▁▁▁▁▁▁▁▁▁▁ band ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
  Title       Title       Title
  detail…     detail…     detail…
```

```python
(b.slide(bg="beige")
 .panel(x=-75, y=2376000, w=9144000, h=2767500, fill="#F9F0E0")     # band
 .header("Des activations…", size_pt=24, align="center",
         x=272100, y=885737, w=8599800, h=554100)
 .image(source_url="a1.jpg", outline="#FFFFFF", outline_pt=2.5,
        x=457000, y=1658367, w=2445301, h=2171701))                 # one of 3
# per column:
(b.header("Co-créations", size_pt=14, align="center",
          x=430154, y=3943867, w=2499000, h=400200)
 .body(["Make My lemonade, Artemide…"], tone="muted", size_pt=10, align="center",
       x=430154, y=4256391, w=2499000, h=569400))
```

| Component   | Font · size | Max chars (≈) |
|-------------|-------------|---------------|
| Headline    | Lora 24 (center) | **48** |
| Column title| Lora 14 (center) | **23** |
| Column body | Inter 10 (center)| **64** (2 lines) |

---

## 6 · Data Table

A title over a native, editable table. Header row + index column carry the
panel fill; body cells are transparent (show the background). Use for
**detailed tabular data**.

```python
def cell(text, **kw):
    return TableCell(text=str(text), size_pt=8, **kw)

header = [cell(""),                                              # transparent corner
          cell("Nom du produit", fill="#F9F0E0", color="#5F6365", bold=True),
          cell("Quantités", fill="#F9F0E0", color="#5F6365", align="right", bold=True)]
rows = [[cell("1", fill="#F9F0E0", color="#5F6365", align="center"),
         cell("Pack Kobo …", color="#0B1115"),
         cell("35", color="#000000", align="right")]]

(b.header("Qualité du stock disponible", size_pt=24,
          x=539999, y=387600, w=8064000, h=554100)
 .table([header, *rows], x=540000, y=1033800,
        col_widths=[382850, 4306475, 843625, 843625, 843625, 843625],
        row_heights=[381000] + [314300] * 10,
        border="#F1E4CD", border_pt=0.75))
```

Guidelines: keep to **≤ ~10 body rows** and **≤ 6 columns** at 8 pt; a cell with
no `fill` adopts the slide background (don't set white). Right-align numeric
columns, left-align text, center the index.

| Component       | Font · size | Max chars (≈) |
|-----------------|-------------|---------------|
| Title           | Lora 24     | **45** |
| Wide text cell  | Inter 8     | **70** (a label column ~4.3 M EMU) |
| Numeric cell    | Inter 8     | **11** (a ~0.84 M EMU column) |

---

## 7 · Chart

Same frame as the Data Table (title up top, content fills the table footprint),
but the content is a matplotlib/seaborn figure rendered to PNG. Use for **trends
/ distributions** rather than raw numbers.

```python
# render a transparent PNG sized to the content footprint (≈8.82 x 3.85 in),
# styled in the palette, then drop it in as an image:
(b.header("Écoulement du stock par univers", size_pt=24,
          x=539999, y=387600, w=8064000, h=554100)
 .image(source_url="/tmp/stock_chart.png", x=540000, y=1033800,
        w=8063825, h=3524000))
```

Guidelines: save the figure with `transparent=True` and match its aspect ratio
to the box (`w/h`) so it isn't distorted; use the palette (nude bars, grey
gridlines, ink labels). Title max **≈45 chars** (Lora 24).

---

## 8 · Customer Feedbacks

A title, a short intro, and two testimonial columns (★ rating + quote + author),
over a large decorative shape. Use for **social proof / reviews**.

```
Avis clients
intro with **keywords**…
★ ★ ★ ★ ★              ★ ★ ★ ★ ★
"quote left…"          "quote right…"
        - Name                 - Name
```

```python
STARS = " ".join("★" * 5)
(b.slide(bg="beige")
 .panel(shape="ellipse", fill="#F9F0E0", x=2236850, y=464600, w=4670400, h=4662900)
 .panel(fill="#F9F0E0", x=2236842, y=2826057, w=4670400, h=4203600)
 .header("Avis clients", size_pt=30, x=586160, y=723300, w=4160400, h=554100)
 .body(["Une phrase **d'introduction** avec des **mots clefs** en gras."],
       tone="muted", size_pt=10, x=586150, y=1658400, w=3985800, h=459600))
# per review column:
(b.body([STARS], color="#D1AE9B", size_pt=24, x=699250, y=2431375, w=2000000, h=280000)
 .body(["A sharp selection of brands…"], tone="muted", size_pt=8,
       x=699250, y=2891181, w=3351900, h=280800)
 .body(["- Alexandra L"], tone="muted", size_pt=8,
       x=699250, y=3208850, w=3351900, h=280800))
```

| Component | Font · size | Max chars (≈) |
|-----------|-------------|---------------|
| Title     | Lora 30     | **18** |
| Intro     | Inter 10    | **52** (1 line) |
| Quote     | Inter 8     | **55** per review (keep to one line) |
| Author    | Inter 8     | **55** |

---

## 9 · Quote

A single centered testimonial flanked by oversized quotation marks (opening
top-left, closing bottom-right) with the author below-right. Use for **one
hero quote** as a breather slide.

```
   “
        Vous pouvez écrire une citation,
        plus ou moins longue…
                              - Prénom Nom
                                          ”
```

```python
(b.slide(bg="beige")
 .header("“", size_pt=120, color="#D1AE9B", x=2143446, y=1137099, w=779004, h=652675)
 .header("”", size_pt=120, color="#D1AE9B", x=6221547, y=3353749, w=779004, h=652675)
 .body(["Vous pouvez écrire une citation, plus ou moins longue…"],
       tone="muted", size_pt=12, x=2646750, y=2195250, w=3850500, h=753000)
 .body(["- Prénom Nom"], tone="muted", size_pt=8, align="right",
       x=3224250, y=3072950, w=3273000, h=280800))
```

| Component | Font · size | Max chars (≈) |
|-----------|-------------|---------------|
| Quote text| Inter 12    | **85** (≈2 lines) |
| Author    | Inter 8 (right) | **53** |

---

### Quick reference — character budgets

| Layout              | Tightest text area → budget          |
|---------------------|--------------------------------------|
| Split Statement     | headline ≤ 36 · body ≤ 250           |
| Stat Cards          | KPI number ≤ 5 · caption ≤ 36        |
| Process Timeline    | step title ≤ 17 · step body ≤ 140    |
| Photo Gallery       | headline ≤ 74 · subtitle ≤ 76        |
| Gallery w/ Captions | column title ≤ 23 · body ≤ 64        |
| Data Table          | numeric cell ≤ 11 · text cell ≤ 70   |
| Chart               | title ≤ 45                           |
| Customer Feedbacks  | title ≤ 18 · quote ≤ 55              |
| Quote               | quote ≤ 85 · author ≤ 53             |

> Figures are conservative capacities for the on-brand fonts at the listed
> `size_pt`. Headlines read best well under the cap; treat these as "do not
> exceed", not "fill to". To check a real deck, run
> `uv run examples/kpi_report.py --check` (the `fit_report` metric pass).
