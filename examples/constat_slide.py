"""Reproduce three slides of the Choose "Template Pitch" deck with slidebox.

1. "LE CONSTAT — Le marché lifestyle est saturé" (image panel + text).
2. "NOTRE CIBLE — Le scroll Choose, un réflexe matinal" (text + 2x2 KPI cards).
3. "1. LES DROPS ÉPHÉMÈRES" timeline (a 4-step process on a horizontal axis).

All three share the source theme: Lora (serif) headlines, Inter (sans)
labels/body, on a #FFF9ED cream background. Resolved source colors map to the
brand palette — black #0B1115 (DARK1), grey_500 #8A8D8F (LIGHT2), grey_700
#434647 (LIGHT1) — plus a few off-palette accents set explicitly via hex
(#F9F0E0 panel, #F1E4CD card, #D1AE9B nude axis/nodes).

    uv run examples/constat_slide.py                 # -> /tmp/constat_slide.pptx
    uv run examples/constat_slide.py --upload        # -> Google Slides (My Drive)
    uv run examples/constat_slide.py --file-id <id>  # update in place
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from slidebox import RGB, BrandTheme, Deck, TableCell, save, to_google_slides

# Left-panel image (any image; the task allows any). Fetched on first run so
# the script is self-contained; override LEFT_IMAGE with your own file.
LEFT_IMAGE = "/tmp/constat_left.jpg"
LEFT_IMAGE_URL = "https://picsum.photos/seed/choose-lifestyle/900/1160"


def ensure_image() -> str:
    p = Path(LEFT_IMAGE)
    if not p.exists():
        with urllib.request.urlopen(LEFT_IMAGE_URL, timeout=30) as resp:
            p.write_bytes(resp.read())
    return str(p)


def gallery(i: int) -> str:
    """A stand-in portrait stock photo for the project galleries (any image)."""
    p = Path(f"/tmp/proj_{i}.jpg")
    if not p.exists():
        url = f"https://picsum.photos/seed/proj{i}/700/780"
        with urllib.request.urlopen(url, timeout=30) as resp:
            p.write_bytes(resp.read())
    return str(p)


# Typography (Lora/Inter) + the exact cream the source uses as its background.
THEME = BrandTheme(
    serif_family="Lora",
    sans_family="Inter",
    beige=RGB(0xFF, 0xF9, 0xED),
)

# Off-palette source colors, set explicitly via hex.
PANEL_FILL = "#F9F0E0"   # ACCENT2 — Le constat side panel
CARD_FILL = "#F1E4CD"    # ACCENT3 — Notre cible KPI cards
NUDE = "#D1AE9B"         # ACCENT4 — timeline axis, nodes, arrowhead, date tags
CREAM = "#FFF9ED"        # ACCENT1 — node outline (matches the background)


def slide_constat(b):
    """Image panel + eyebrow / headline / body."""
    return (
        b.slide(bg="beige", label="02 constat", object_id="s_constat")
        # Side panel, absolute EMU so it bleeds to the slide edges. These are
        # the source panel's exact bounds: x=0, full height, ~45% width.
        .panel(x=0, y=0, w=4131600, h=5143500, fill=PANEL_FILL,
               object_id="constat_panel")
        .image(source_url=LEFT_IMAGE, col=1, row=1, span=(5, 8),
               object_id="constat_image")
        .eyebrow("LE CONSTAT", col=7, row=2, span=(5, 1), variant="sans",
                 size_pt=12, object_id="constat_eyebrow")
        .header("Le marché lifestyle est saturé", size="h1", size_pt=24,
                col=7, row=3, span=(5, 2), object_id="constat_title")
        .body([
            "Les consommateurs sont submergés, les marques peinent à se "
            "démarquer. Les canaux classiques ne suffisent plus pour capter "
            "une audience CSP+ exigeante, en quête de sens.",
            "Il manque un espace éditorial, premium, qui crée de l'envie et "
            "de la surprise au quotidien.",
        ], col=7, row=5, span=(5, 3), tone="muted", size_pt=10, strong=[1],
            object_id="constat_body")
        .logo(variant="black", size="sm", col=12, row=8, span=(1, 1),
              object_id="constat_logo")
    )


# KPI cards in EXACT source EMU (card rect / number box / label box). Using the
# source boxes — not grid cells — keeps the number's padding inside the card,
# instead of letting it hug the edge.
_CARDS = [
    ("500 K", "Weekly Active Users",
     (4543975, 841050, 2140200, 1692600),
     (4762062, 1082100, 1524300, 677100),
     (4762062, 1759200, 1524300, 515700)),
    ("15", "Achats par an par client",
     (6760371, 841050, 2884500, 1692600),
     (6978471, 1082100, 1524300, 677100),
     (6978471, 1759200, 1524300, 515700)),
    ("80 %", "De femmes — 25-40 ans • CSP+",
     (4543975, 2609850, 2140200, 1692600),
     (4762062, 2850900, 1524300, 677100),
     (4762062, 3528000, 1524300, 515700)),
    ("1 / 5", "De la communauté en Île-de-France",
     (6760371, 2609850, 2884500, 1692600),
     (6978471, 2850900, 1524300, 677100),
     (6978475, 3528000, 1671900, 515700)),
]


def _abs(box):
    x, y, w, h = box
    return dict(x=x, y=y, w=w, h=h)


def slide_cible(b):
    """Left text block + a 2x2 grid of KPI cards (all absolute EMU)."""
    b = (
        b.slide(bg="beige", label="05 cible", object_id="s_cible")
        .eyebrow("NOTRE CIBLE", variant="sans", size_pt=12,
                 x=560100, y=1459350, w=3430800, h=369300,
                 object_id="cible_eyebrow")
        .header("Le scroll Choose, un réflexe matinal", size_pt=24,
                x=560100, y=1828650, w=3430800, h=978899,
                object_id="cible_title")
        .body([
            "Plus qu'un public opportuniste, **une communauté qui a intégré "
            "l'app dans sa routine**, à la manière d'un social media.",
        ], tone="muted", size_pt=10,
            x=560100, y=2883750, w=3430800, h=800400, object_id="cible_body")
    )
    for n, (value, label, rect, num, lbl) in enumerate(_CARDS, start=1):
        b = (
            b.panel(rounded=True, fill=CARD_FILL, object_id=f"cible_card{n}",
                    **_abs(rect))
            .header(value, size_pt=32, object_id=f"cible_num{n}", **_abs(num))
            .body([label], tone="muted", size_pt=10,
                  object_id=f"cible_lbl{n}", **_abs(lbl))
        )
    return b.logo(variant="black", size="sm", col=12, row=8, span=(1, 1),
                  object_id="cible_logo")


# Timeline axis geometry (absolute EMU, exact from the source).
_AXIS = dict(x=-23025, y=1660775, w=8798700, h=36600)          # rounded bar
_NODE_X = (395191, 2593734, 4961312, 7263898)                  # 4 dots
_NODE_Y, _NODE_D = 1578025, 204000

# Per-step content: date tag, two-line title, body (** = bold run).
_STEPS = [
    ("JOUR J", "On met en ligne",
     "**Choose prend en charge la création de la vente et sa mise en ligne.** "
     "Visuels, diffusion auprès de la communauté, on s'occupe de tout."),
    ("PENDANT LA VENTE", "Vous gérez les expéditions",
     "Pendant la vente, vous recevez les commandes et expédiez directement "
     "aux clients en **dropshipping, depuis votre propre stock, avec vos "
     "transporteurs**."),
    ("J + 7 OU J + 14", "On clôture la vente",
     "À l'issue de la vente, une fois le délai de rétractation respecté "
     "(14 jours) et les retours / réclamations traités, **vous nous facturez "
     "les quantités vendues**."),
    ("J + 30", "On vous règle votre facture",
     "Choose vous règle la **facture que vous nous avez envoyée**, à 10 jours."),
]


def slide_timeline(b):
    """A horizontal axis with four process steps."""
    b = (
        b.slide(bg="beige", label="07 timeline", object_id="s_timeline")
        .eyebrow("1. LES DROPS ÉPHÉMÈRES", col=1, row=1, span=(6, 1),
                 variant="sans", size_pt=12, object_id="tl_eyebrow")
        .header("Après & Pendant", size="h1", size_pt=24, col=7, row=1,
                span=(6, 1), object_id="tl_header")
        # Axis bar + arrowhead (absolute EMU).
        .panel(fill=NUDE, rounded=True, object_id="tl_axis", **_AXIS)
        .panel(shape="triangle", fill=NUDE, rotation=90, object_id="tl_arrow",
               x=8730000, y=1599075, w=160000, h=160000)
    )
    # Four nodes on the axis (nude dots with a cream ring).
    for i, nx in enumerate(_NODE_X, start=1):
        b = b.panel(shape="ellipse", fill=NUDE, outline=CREAM, outline_pt=3,
                    x=nx, y=_NODE_Y, w=_NODE_D, h=_NODE_D,
                    object_id=f"tl_node{i}")
    # Four columns: date tag (row 4), title (row 5), body (rows 6-8).
    for i, (date, title, body) in enumerate(_STEPS):
        col = 1 + i * 3
        # The 4th column's body is short in the source; keep its corner cell
        # free for the logo (col 12, row 8).
        body_rows = 2 if i == 3 else 3
        b = (
            b.eyebrow(date, col=col, row=4, span=(3, 1), variant="sans",
                      size_pt=14, color=NUDE, object_id=f"tl_date{i}")
            .header(title, size="h1", size_pt=14, col=col, row=5, span=(3, 1),
                    object_id=f"tl_title{i}")
            .body([body], col=col, row=6, span=(3, body_rows), tone="muted",
                  size_pt=10, object_id=f"tl_body{i}")
        )
    return b.logo(variant="black", size="sm", col=12, row=8, span=(1, 1),
                  object_id="tl_logo")


WHITE = "#FFFFFF"   # ACCENT6 — photo frame outline

# Slide 14 — "3. LES PROJETS EXCLUSIFS": centered title + a row of 5 photos.
# Each photo is slightly tilted (rotation in degrees), as in the source — the
# bbox/angle are derived from the source affine transform (shear -> rotation).
_PROJ_IMAGES = [
    (-274026, 2658956, 1740953, 2577211, -4.06),
    (1238729, 2791402, 2278024, 2418544, 2.95),
    (3426625, 2681373, 1950523, 2509023, -2.87),
    (5388884, 2866050, 2062100, 2479000, 0.0),
    (7497292, 2762961, 2200634, 2584583, 2.29),
]


def slide_projets(b):
    b = (
        b.slide(bg="beige", label="14 projets", object_id="s_projets")
        .eyebrow("3. LES PROJETS EXCLUSIFS", variant="sans", size_pt=12,
                 align="center", x=2856600, y=516450, w=3430800, h=369300,
                 object_id="proj_eyebrow")
        .header("Des projets uniques à la croisée du story-telling et de "
                "l'expérience", size_pt=24, align="center",
                x=1264400, y=885750, w=6615299, h=978899, object_id="proj_title")
        .body(["Créés **sur-mesure avec les marques** pour exprimer leur ADN."],
              tone="muted", size_pt=10, align="center",
              x=1726400, y=1940850, w=5691300, h=338700, object_id="proj_sub")
    )
    for i, (x, y, w, h, rot) in enumerate(_PROJ_IMAGES):
        b = b.image(source_url=gallery(i + 1), outline=WHITE, outline_pt=2.5,
                    rotation=rot, x=x, y=y, w=w, h=h, object_id=f"proj_img{i}")
    return b


# Slide 15 — "Des activations…": 3 framed photos over an ACCENT2 band, with
# three centered caption columns (Lora title + Inter detail).
_ACT_IMAGES = [
    (457000, 1658367, 2445301, 2171701),
    (3349350, 1658367, 2445301, 2171699),
    (6317900, 1658367, 2445301, 2171702),
]
_ACT_COLS = [
    ("Co-créations", "Make My lemonade, Artemide, Gamin Gamine, Color Therapis…",
     430154, 3943867, 2499000),
    ("Créations produits", "Calendriers de l'avent, Trousse beauté…",
     3335924, 3943867, 2499000),
    ("Incarnations physiques", "Maison de Vacances, Marché de Noël…",
     6241704, 3943867, 2499000),
]


def slide_activations(b):
    b = (
        b.slide(bg="beige", label="15 activations", object_id="s_activations")
        # Lower ACCENT2 band, full width (absolute, behind everything).
        .panel(x=-75, y=2376000, w=9144000, h=2767500, fill=PANEL_FILL,
               object_id="act_band")
        .eyebrow("3. LES PROJETS EXCLUSIFS", variant="sans", size_pt=12,
                 align="center", x=2856600, y=516450, w=3430800, h=369300,
                 object_id="act_eyebrow")
        .header("Des activations qu'on ne pourrait pas créer seuls",
                size_pt=24, align="center",
                x=272100, y=885737, w=8599800, h=554100, object_id="act_title")
    )
    for i, (x, y, w, h) in enumerate(_ACT_IMAGES):
        b = b.image(source_url=gallery(i + 6), outline=WHITE, outline_pt=2.5,
                    x=x, y=y, w=w, h=h, object_id=f"act_img{i}")
    for i, (title, detail, x, yt, w) in enumerate(_ACT_COLS):
        b = (
            b.header(title, size_pt=14, align="center",
                     x=x, y=yt, w=w, h=400200, object_id=f"act_t{i}")
            .body([detail], tone="muted", size_pt=10, align="center",
                  x=x, y=4256391, w=w, h=569400, object_id=f"act_d{i}")
        )
    return b


# Slide 8 (other deck) — "Qualité du stock disponible": a 11x6 data table.
_TBL_X, _TBL_Y = 540000, 1033800
_COL_W = [382850, 4306475, 843625, 843625, 843625, 843625]
_ROW_H = [381000] + [314300] * 10
_HF, _HFG = "#F9F0E0", "#5F6365"        # header/index fill + grey text
_PROD, _NUM = "#0B1115", "#000000"      # product vs number text
_BORDER = "#F1E4CD"
_TBL_ROWS = [
    (1, "Pack Kobo Libra Colour Blanc - Sleep Cover Bleu", 35, 35, "0 %", 21),
    (2, "Pack Kobo Clara BW - Sleep Cover au Choix - Jaune", 20, 20, "0 %", 16),
    (3, "Pack Kobo Clara BW - Sleep Cover au Choix - Vert", 50, 50, "0 %", 15),
    (4, "Pack Kobo Libra Colour Noir - Sleep Cover Bleu", 12, 12, "0 %", 6),
    (5, "Pack Kobo Clara BW - Sleep Cover au Choix - Bleu", 30, 30, "0 %", 6),
    (6, "Pack Kobo Clara BW - Sleep Cover au Choix - Rose", 30, 30, "0 %", 4),
    (7, "Pack Kobo Clara Colour Blanc - Sleep Cover au Choix - Rose", 20, 20, "0 %", 3),
    (8, "Pack Kobo Clara Colour Noir - Sleep Cover au Choix - Bleu", 19, 20, "5 %", 0),
    (9, "Pack Kobo Clara Colour Noir - Sleep Cover au Choix - Vert", 29, 39, "26 %", 0),
    (10, "Pack Kobo Clara Colour Blanc - Sleep Cover au Choix - Bleu", 14, 20, "30 %", 0),
]


def _cell(text, **kw):
    return TableCell(text=str(text), size_pt=8, **kw)


def slide_table(b):
    # Body / corner cells are TRANSPARENT in the source (fill NOT_RENDERED) so
    # the cream slide background shows through — only the header row and index
    # column carry the #F9F0E0 fill. (Setting them solid white was the bug.)
    header = [
        _cell(""),  # top-left corner: no fill (transparent)
        _cell("Nom du produit", fill=_HF, color=_HFG, align="left", bold=True),
        _cell("Quantités vendues", fill=_HF,
              color=_HFG, align="right", bold=True),
        _cell("Stock\ninitial", fill=_HF, color=_HFG, align="right", bold=True),
        _cell("Qualité\ndu stock", fill=_HF,
              color=_HFG, align="right", bold=True),
        _cell("Nombre d'alertes", fill=_HF,
              color=_HFG, align="right", bold=True),
    ]
    cells = [header]
    for idx, name, vend, stock, qual, alerts in _TBL_ROWS:
        cells.append([
            _cell(idx, fill=_HF, color=_HFG, align="center"),
            _cell(name, color=_PROD, align="left"),
            _cell(vend, color=_NUM, align="right"),
            _cell(stock, color=_NUM, align="right"),
            _cell(qual, color=_NUM, align="right"),
            _cell(alerts, color=_NUM, align="right"),
        ])
    return (
        b.slide(bg="beige", label="08 table", object_id="s_table")
        .header("Qualité du stock disponible", size_pt=24,
                x=539999, y=387600, w=8064000, h=554100, object_id="tbl_title")
        .table(cells, x=_TBL_X, y=_TBL_Y, col_widths=_COL_W, row_heights=_ROW_H,
               border=_BORDER, border_pt=0.75, object_id="stock_table")
    )


# Slide 9 (new, creative) — same layout as the table slide, but the content
# area holds a seaborn bar chart instead. Same title box + table footprint.
CHART_PNG = "/tmp/stock_chart.png"
_CHART_X, _CHART_Y = 540000, 1033800
_CHART_W, _CHART_H = 8063825, 3524000
_EMU_PER_IN = 914400

# Fictional sell-through by product universe (creative data, on-brand palette).
_CHART_DATA = {
    "Liseuses": 92, "Coques & étuis": 78, "Beauté": 64,
    "Maison": 57, "Enfant": 49, "Accessoires": 41, "Papeterie": 33,
}


def make_chart(path: str) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    dark, grey, grid = "#0B1115", "#8A8D8F", "#E7DBCB"
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Helvetica", "Arial", "DejaVu Sans"],
        "text.color": dark, "axes.labelcolor": grey,
        "xtick.color": grey, "ytick.color": dark,
    })
    names = list(_CHART_DATA)
    vals = list(_CHART_DATA.values())
    # Warm nude gradient, deepest for the best performer.
    palette = sns.blend_palette(["#EAD9CC", "#C49A85", "#A86F54"], len(vals))
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    colors = [None] * len(vals)
    for rank, i in enumerate(order):
        colors[i] = palette[rank]

    fig, ax = plt.subplots(figsize=(_CHART_W / _EMU_PER_IN, _CHART_H / _EMU_PER_IN),
                           dpi=200)
    sns.barplot(x=vals, y=names, palette=colors, orient="h", ax=ax)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Taux d'écoulement (%)", fontsize=11)
    ax.set_ylabel("")
    ax.tick_params(labelsize=11)
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(grid)
    ax.grid(axis="x", color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    for i, v in enumerate(vals):
        ax.text(v + 1.5, i, f"{v} %", va="center", ha="left",
                fontsize=11, fontweight="bold", color=dark)
    fig.tight_layout()
    fig.savefig(path, transparent=True)
    plt.close(fig)
    return path


def slide_chart(b):
    return (
        b.slide(bg="beige", label="09 chart", object_id="s_chart")
        .header("Écoulement du stock par univers", size_pt=24,
                x=539999, y=387600, w=8064000, h=554100, object_id="chart_title")
        .image(source_url=CHART_PNG, x=_CHART_X, y=_CHART_Y,
               w=_CHART_W, h=_CHART_H, object_id="stock_chart_img")
    )


# Slide 10 — "Avis clients" (from another deck): two review columns (5-star
# rating + quote + author) over a big decorative beige circle/rectangle.
GOLD = "#D1AE9B"   # rating stars (nude, ACCENT4)
STARS = " ".join("★" * 5)   # thin spaces spread the row a touch wider

# (stars box, quote, author) per review column — absolute EMU from the source.
_REVIEWS = [
    ((699250, 2431375, 2000000, 280000),
     "A sharp selection of brands highlighting beautiful products with very "
     "good quality. Lots of good discoveries.", "- Alexandra L"),
    ((4746550, 2431375, 2000000, 280000),
     "Everything is there : a great interface, various type of products and "
     "an irreproachable customer service :)", "- Bob D"),
]


def slide_avis(b):
    b = (
        b.slide(bg="beige", label="10 avis", object_id="s_avis")
        # Decorative beige shapes behind everything (ellipse + rectangle).
        .panel(shape="ellipse", fill=PANEL_FILL,
               x=2236850, y=464600, w=4670400, h=4662900, object_id="avis_circle")
        .panel(shape="rectangle", fill=PANEL_FILL,
               x=2236842, y=2826057, w=4670400, h=4203600, object_id="avis_rect")
        .header("Avis clients", size_pt=30,
                x=586160, y=723300, w=4160400, h=554100, object_id="avis_title")
        .body(["Vous pouvez écrire une petite phrase **d'introduction** et "
               "mettre en en avant un ou plusieurs **mots clefs** en gras."],
              tone="muted", size_pt=10,
              x=586150, y=1658400, w=3985800, h=459600, object_id="avis_intro")
    )
    for i, (sbox, quote, author) in enumerate(_REVIEWS):
        sx, sy, sw, sh = sbox
        b = (
            b.body([STARS], color=GOLD, size_pt=24,
                   x=sx, y=sy, w=sw, h=sh, object_id=f"avis_stars{i}")
            .body([quote], tone="muted", size_pt=8,
                  x=sx if i == 0 else 4746550, y=2891181, w=3351900, h=280800,
                  object_id=f"avis_quote{i}")
            .body([author], tone="muted", size_pt=8,
                  x=sx if i == 0 else 4746550, y=3208850, w=3351900, h=280800,
                  object_id=f"avis_author{i}")
        )
    return b


# Slide 11 — a centered testimonial quote, flanked by big decorative quote
# marks (opening top-left, closing bottom-right), with the author below-right.
def slide_quote(b):
    return (
        b.slide(bg="beige", label="11 quote", object_id="s_quote")
        # Decorative quotation marks (nude, serif) — opening and closing.
        .header("“", size_pt=120, color=NUDE,
                x=2143446, y=1137099, w=779004, h=652675, object_id="q_open")
        .header("”", size_pt=120, color=NUDE,
                x=6221547, y=3353749, w=779004, h=652675, object_id="q_close")
        .body(["Vous pouvez écrire une citation, plus ou moins longue. En "
               "italique en restant sur la Roboto, en évitant de trop "
               "différencier le texte pour une bonne lecture."],
              tone="muted", size_pt=12,
              x=2646750, y=2195250, w=3850500, h=753000, object_id="q_text")
        .body(["- Prénom Nom"], tone="muted", size_pt=8, align="right",
              x=3224250, y=3072950, w=3273000, h=280800, object_id="q_author")
    )


def build() -> Deck:
    b = Deck.new(title="Template Pitch (slidebox repro)", object_id="pitch")
    b = slide_constat(b)
    b = slide_cible(b)
    b = slide_timeline(b)
    b = slide_projets(b)
    b = slide_activations(b)
    b = slide_table(b)
    b = slide_chart(b)
    b = slide_avis(b)
    b = slide_quote(b)
    return b.build()


def main() -> None:
    ap = argparse.ArgumentParser(description="Reproduce three Pitch slides.")
    ap.add_argument("--output", default="/tmp/constat_slide.pptx")
    ap.add_argument("--upload", action="store_true",
                    help="Upload to Drive as Google Slides.")
    ap.add_argument("--folder", default=None,
                    help="Drive folder / Shared Drive id to create in.")
    ap.add_argument("--file-id", default=None,
                    help="Update an existing Google Slides file in place.")
    ap.add_argument("--name", default="Template Pitch (slidebox repro)")
    args = ap.parse_args()

    ensure_image()
    make_chart(CHART_PNG)
    deck = build()
    path = save(deck, args.output, theme=THEME)
    print(f"saved {len(deck.slides)} slide(s) -> {path}")

    if args.upload or args.file_id:
        g = to_google_slides(deck, name=args.name, theme=THEME,
                             folder_id=args.folder, file_id=args.file_id)
        print(g.url)
        print(f"file_id={g.id}")


if __name__ == "__main__":
    main()
