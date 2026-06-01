"""Weekly performance report — KPI values + matplotlib charts (fake data).

Same Choose theme as the pitch deck, but data-driven: real KPI numbers and
three matplotlib figures (trend line, category bars, revenue donut) styled
in the brand palette and embedded as images.

    uv pip install matplotlib                 # one-time
    uv run examples/kpi_report.py             # -> /tmp/kpi_report.pptx
    uv run examples/kpi_report.py --check     # verify no text overflows
    uv run examples/kpi_report.py --upload    # -> Google Slides on Drive

Charts are rendered to PNGs sized to their exact grid cells (so they don't
distort) and placed with `image(source_url=…)`. Swap the fake data in
`DATA` for real numbers and it regenerates.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from slidebox import BrandTheme, Deck, fit_report, save, to_google_slides
from slidebox.grid import cell_to_emu

# ── Theme palette (hex, from BrandTheme) ─────────────────────────────
_T = BrandTheme()


def _hex(rgb) -> str:
    return f"#{rgb.r:02x}{rgb.g:02x}{rgb.b:02x}"


NUDE = _hex(_T.nude)
DARK = _hex(_T.black)
GREY = _hex(_T.grey_500)
GRID = _hex(_T.grey_300)
UP = _hex(_T.accent_up)
BEIGE = _hex(_T.beige)

_EMU_PER_IN = 914400

# ── Fake data ────────────────────────────────────────────────────────
DATA = {
    "weeks": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"],
    "gmv_weekly": [3.1, 3.4, 3.2, 3.8, 4.0, 3.9, 4.3, 4.6, 4.4, 5.1],  # M€
    "categories": ["Mode", "Beauté", "Design", "Enfant"],
    "category_gmv": [188, 142, 96, 61],  # k€
    "revenue_by_country": {"FR": 512, "DE": 138, "BE": 84, "ES": 61, "Autres": 79},
}


# ── Matplotlib charts (styled in the Choose palette) ─────────────────
def _figsize(col: int, colspan: int, row: int, rowspan: int) -> tuple[float, float]:
    """Inches matching a grid cell exactly, so the image isn't distorted."""
    _, _, w, h = cell_to_emu(col, colspan, row, rowspan, res="fine")
    return (w / _EMU_PER_IN, h / _EMU_PER_IN)


def make_charts(out_dir: Path) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "sans-serif",
        "text.color": DARK,
        "axes.edgecolor": GREY,
        "axes.labelcolor": DARK,
        "xtick.color": GREY,
        "ytick.color": GREY,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
    })
    paths: dict[str, str] = {}

    # 1 — Weekly GMV trend (line), spans an 8x4 cell.
    fig, ax = plt.subplots(figsize=_figsize(1, 8, 4, 4), dpi=200)
    ax.plot(DATA["weeks"], DATA["gmv_weekly"], color=NUDE, linewidth=3,
            marker="o", markersize=7, markerfacecolor=DARK, markeredgecolor=DARK)
    ax.set_ylim(0, max(DATA["gmv_weekly"]) * 1.25)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("left",):
        ax.spines[s].set_color(GREY)
    fig.tight_layout()
    p = out_dir / "trend.png"
    fig.savefig(p, transparent=True)
    plt.close(fig)
    paths["trend"] = str(p)

    # 2 — GMV by category (bars), spans a 7x4 cell.
    fig, ax = plt.subplots(figsize=_figsize(1, 7, 4, 4), dpi=200)
    ax.bar(DATA["categories"], DATA["category_gmv"], color=NUDE, width=0.62)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["left"].set_color(GREY)
    for i, v in enumerate(DATA["category_gmv"]):
        ax.text(i, v + 4, f"{v} k€", ha="center", color=DARK, fontsize=11,
                fontweight="bold")
    ax.set_ylim(0, max(DATA["category_gmv"]) * 1.18)
    fig.tight_layout()
    p = out_dir / "bars.png"
    fig.savefig(p, transparent=True)
    plt.close(fig)
    paths["bars"] = str(p)

    # 3 — Revenue by country (donut), spans a 5x5 cell.
    fig, ax = plt.subplots(figsize=_figsize(1, 5, 3, 5), dpi=200)
    labels = list(DATA["revenue_by_country"])
    values = list(DATA["revenue_by_country"].values())
    shades = ["#D1AE9B", "#C49A85", "#B8866F", "#AD7259", "#D8D9DA"]
    ax.pie(values, labels=labels, colors=shades, startangle=90,
           wedgeprops={"width": 0.42, "edgecolor": BEIGE, "linewidth": 2},
           textprops={"color": DARK, "fontsize": 11})
    ax.set_aspect("equal")
    fig.tight_layout()
    p = out_dir / "donut.png"
    fig.savefig(p, transparent=True)
    plt.close(fig)
    paths["donut"] = str(p)

    return paths


# ── Deck ──────────────────────────────────────────────────────────────
def build(charts: dict[str, str]) -> Deck:
    b = Deck.new(title="Revue hebdomadaire — Choose", object_id="report")

    # 01 · Cover
    b = (
        b.slide(bg="black", label="01 cover", object_id="cover")
        .eyebrow("REVUE HEBDOMADAIRE", col=1, row=2, span=(8, 1),
                 object_id="cover_eyebrow")
        .header("Une semaine en chiffres.", size="display", col=1, row=3,
                span=(10, 2), object_id="cover_title")
        .subtitle("Semaine du 19 au 25 mai 2026.", col=1, row=6, span=(8, 1),
                  object_id="cover_sub")
        .logo(variant="white", col=1, row=8, span=(3, 1), object_id="cover_logo")
    )

    # 02 · KPI grid (4 cards with values + deltas)
    b = (
        b.slide(bg="beige", label="02 kpis", object_id="kpis")
        .eyebrow("VUE D'ENSEMBLE", col=1, row=1, span=(8, 1), object_id="kpis_eyebrow")
        .header("L'activité de la semaine.", size="h1", col=1, row=2, span=(10, 1),
                object_id="kpis_title")
        .kpi(label="GMV", value="5,1", unit="M€", delta="+16% vs S-1",
             delta_dir="up", size="md", col=1, row=4, span=(3, 4),
             object_id="kpi_gmv")
        .kpi(label="Clients actifs", value="512", unit="K", delta="+8%",
             delta_dir="up", size="md", col=4, row=4, span=(3, 4),
             object_id="kpi_wau")
        .kpi(label="Panier moyen", value="47", unit="€", delta="+3%",
             delta_dir="up", size="md", col=7, row=4, span=(3, 4),
             object_id="kpi_aov")
        .kpi(label="Récurrence", value="75", unit="%", delta="+2 pts",
             delta_dir="up", size="md", col=10, row=4, span=(3, 4),
             object_id="kpi_repeat")
    )

    # 03 · Revenue trend (line chart)
    b = (
        b.slide(bg="white", label="03 trend", object_id="trend")
        .eyebrow("GMV HEBDOMADAIRE", col=1, row=1, span=(8, 1),
                 object_id="trend_eyebrow")
        .header("Dix semaines de croissance.", size="h1", col=1, row=2,
                span=(10, 1), object_id="trend_title")
        .image(source_url=charts["trend"], col=1, row=4, span=(8, 4),
               object_id="trend_chart")
        .kpi(label="Croissance", value="+64", unit="%", delta="sur 10 semaines",
             delta_dir="up", size="md", col=10, row=4, span=(3, 4),
             object_id="trend_kpi")
    )

    # 04 · GMV by category (bar chart)
    b = (
        b.slide(bg="beige", label="04 categories", object_id="cats")
        .eyebrow("PAR UNIVERS", col=1, row=1, span=(8, 1), object_id="cats_eyebrow")
        .header("Où se concentre la GMV.", size="h1", col=1, row=2, span=(10, 1),
                object_id="cats_title")
        .image(source_url=charts["bars"], col=1, row=4, span=(7, 4),
               object_id="cats_chart")
        .subtitle("La mode reste le moteur, suivie de près par la beauté.",
                  col=9, row=4, span=(4, 2), object_id="cats_note")
        .kpi(label="Part Mode", value="38", unit="%", size="md",
             col=9, row=6, span=(4, 3), object_id="cats_kpi")
    )

    # 05 · Revenue by country (donut)
    b = (
        b.slide(bg="nude", label="05 geo", object_id="geo")
        .eyebrow("RÉPARTITION GÉOGRAPHIQUE", col=1, row=1, span=(8, 1),
                 object_id="geo_eyebrow")
        .header("La France en tête.", size="h1", col=1, row=2, span=(10, 1),
                object_id="geo_title")
        .image(source_url=charts["donut"], col=1, row=3, span=(5, 5),
               object_id="geo_chart")
        .kpi(label="France", value="55", unit="%", size="md",
             col=7, row=3, span=(3, 3), object_id="geo_fr")
        .kpi(label="Export", value="45", unit="%", size="md",
             col=10, row=3, span=(3, 3), object_id="geo_export")
        .body(["L'export progresse trimestre après trimestre, porté par "
               "l'Allemagne et la Belgique."],
              col=7, row=6, span=(6, 2), object_id="geo_body")
    )

    # 06 · Closing
    b = (
        b.slide(bg="black", label="06 close", object_id="close")
        .header("On en parle ?", size="display", col=1, row=3, span=(10, 2),
                object_id="close_cta")
        .logo(variant="white", col=1, row=7, span=(3, 1), object_id="close_logo")
    )

    return b.build()


# ── Fonts (stand-ins; swap for real Choose files) ────────────────────
_SUP = "/System/Library/Fonts/Supplemental"
FONTS = {
    "Sangbleu Republic": {"regular": f"{_SUP}/Georgia.ttf",
                          "bold": f"{_SUP}/Georgia Bold.ttf",
                          "italic": f"{_SUP}/Georgia Italic.ttf"},
    "Maison Neue": {"regular": f"{_SUP}/Arial.ttf",
                    "bold": f"{_SUP}/Arial Bold.ttf",
                    "italic": f"{_SUP}/Arial Italic.ttf"},
}


def _fonts() -> dict | None:
    ok = all(Path(p).exists() for spec in FONTS.values() for p in spec.values())
    return FONTS if ok else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Weekly KPI + charts report.")
    ap.add_argument("--output", default="/tmp/kpi_report.pptx")
    ap.add_argument("--upload", action="store_true",
                    help="Upload to Drive as Google Slides.")
    ap.add_argument("--check", action="store_true",
                    help="Report any text that overflows its box.")
    ap.add_argument("--name", default="Revue hebdomadaire — Choose")
    args = ap.parse_args()

    chart_dir = Path(tempfile.mkdtemp(prefix="kpi_report_charts_"))
    charts = make_charts(chart_dir)
    deck = build(charts)
    fonts = _fonts()

    if args.check:
        if fonts is None:
            print("FONTS files not found; cannot run the metric fit check.")
            return
        issues = fit_report(deck, fonts)
        if not issues:
            print("fit check: no overflow — every text box fits.")
        else:
            print(f"fit check: {len(issues)} issue(s):")
            for o in issues:
                print(f"  slide {o.slide_index:2d}  {o.shape_name:20s} "
                      f"{o.kind:6s}  {o.detail}")
        return

    path = save(deck, args.output, fonts=fonts)
    print(f"saved {len(deck.slides)} slides -> {path}")
    print(f"charts in {chart_dir}")

    if args.upload:
        g = to_google_slides(deck, name=args.name, fonts=fonts)
        print(g.url)


if __name__ == "__main__":
    main()
