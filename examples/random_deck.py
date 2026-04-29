"""Random deck demo — showcases themes and the new KpiGrid auto-layout.

Runs against Application Default Credentials.

    uv run examples/random_deck.py
    SLIDEBOX_THEME=slate   uv run examples/random_deck.py
    SLIDEBOX_THEME=minimal uv run examples/random_deck.py
    SLIDEBOX_THEME=dark    uv run examples/random_deck.py
    SLIDEBOX_THEME=warm    uv run examples/random_deck.py
"""

from __future__ import annotations

import os
import random
import string
from datetime import datetime

from slidebox import (
    Col,
    Grid,
    Image,
    Kpi,
    KpiGrid,
    KpiTheme,
    Presentation,
    Shape,
    ShapeType,
    Slide,
    Subtitle,
    Text,
    Theme,
    Title,
    pt,
    themes,
)

METRICS = [
    ("Revenue", lambda: f"${random.randint(1, 9)}.{random.randint(0, 9)}M"),
    ("Active users", lambda: f"{random.randint(10, 99)}K"),
    ("Retention", lambda: f"{random.randint(80, 99)}%"),
    ("NPS", lambda: str(random.randint(30, 80))),
    ("Churn", lambda: f"{random.randint(1, 9)}.{random.randint(0, 9)}%"),
    ("CSAT", lambda: f"{random.randint(85, 99)}%"),
]

LEAD = (
    "Slidebox compiles a declarative tree into one atomic batchUpdate. "
    "Every component has a deterministic id, so the same script can "
    "create a deck today and patch it next week without rebuilding."
)

SHAPE_PALETTE = [
    (ShapeType.RECTANGLE, "#4285f4"),
    (ShapeType.ELLIPSE, "#ea4335"),
    (ShapeType.DIAMOND, "#fbbc04"),
    (ShapeType.TRIANGLE, "#34a853"),
    (ShapeType.ROUND_RECTANGLE, "#ff6d01"),
    (ShapeType.STAR, "#46bdc6"),
    (ShapeType.CLOUD, "#9e4aff"),
    (ShapeType.ARROW, "#e94cbf"),
]


# ── theme ────────────────────────────────────────────────────────────

def _brand_theme() -> Theme:
    """A tuned GitHub-ish dark brand theme."""
    return Theme(
        background="#0d1117",
        text_primary="#e6edf3",
        text_secondary="#7d8590",
        accent="#58a6ff",
        font_family="Inter",
        kpi=KpiTheme(
            fill="#161b22",
            label_color="#7d8590",
            value_color="#e6edf3",
            trend_up_text="#3fb950",
            trend_down_text="#f85149",
            trend_neutral_text="#7d8590",
        ),
    )


def _warm_theme() -> Theme:
    """Cream background, beige KPI cards, editorial serif — Choose-style."""
    return Theme(
        background="#FFF9ED",
        text_primary="#1a1a1a",
        text_secondary="#5a5547",
        accent="#1a1a1a",
        font_family="Lora",
        kpi=KpiTheme(
            fill="#F4E3C9",
            label_color="#5a5547",
            value_color="#1a1a1a",
            trend_up_text="#3a6b3a",
            trend_down_text="#a04040",
            trend_neutral_text="#5a5547",
        ),
    )


def _pick_theme() -> Theme:
    name = os.environ.get("SLIDEBOX_THEME", "warm").lower()
    return {
        "dark": themes.dark,
        "slate": themes.slate,
        "minimal": themes.minimal,
        "default": themes.default,
        "brand": _brand_theme,
        "warm": _warm_theme,
    }.get(name, _brand_theme)()


def _rand_id(prefix: str) -> str:
    return prefix + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def _trend() -> str:
    delta = random.randint(-8, 18)
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta}%"


# ── slides ───────────────────────────────────────────────────────────

def _cover(theme: Theme, stamp: str) -> None:
    with Slide(id="slide_cover"):
        with Col(padding=pt(72), gap=pt(16), justify="center"):
            Text(
                "SLIDEBOX",
                color=theme.accent,
                size=pt(11),
                bold=True,
                height=pt(18),
                id="cover_eyebrow",
            )
            Title("A quiet quarter, mostly.", id="cover_title")
            Subtitle(
                f"Generated {stamp}. Themed, deterministic, patchable.",
                id="cover_subtitle",
            )


def _kpis_three(n_slide: int) -> None:
    """A KPI slide with title + subtitle + 3-card row."""
    picks = random.sample(METRICS, 3)
    with Slide(id=f"slide_kpis_{n_slide}"):
        with Col(padding=pt(40), gap=pt(12)):
            Title("Key metrics", id=f"kpis_{n_slide}_title", height=pt(40))
            Subtitle("This quarter at a glance",
                     id=f"kpis_{n_slide}_sub", height=pt(22))
            with KpiGrid():
                for i, (label, value_fn) in enumerate(picks):
                    Kpi(label, value_fn(), trend=_trend(),
                        id=f"k{n_slide}_{i:02d}")


def _kpis_six(n_slide: int) -> None:
    """A denser KPI slide — 6 cards in a 3×2 grid."""
    picks = random.sample(METRICS, 6)
    with Slide(id=f"slide_kpis_{n_slide}"):
        with Col(padding=pt(40), gap=pt(12)):
            Title("Full scorecard", id=f"kpis_{n_slide}_title", height=pt(40))
            Subtitle("Every tracked metric, one glance",
                     id=f"kpis_{n_slide}_sub", height=pt(22))
            with KpiGrid():
                for i, (label, value_fn) in enumerate(picks):
                    Kpi(label, value_fn(), trend=_trend(),
                        id=f"k{n_slide}_{i:02d}")


def _gallery() -> None:
    seeds = random.sample(range(1, 1000), 6)
    with Slide(id="slide_gallery"):
        with Col(padding=pt(36), gap=pt(18)):
            Title("Gallery", id="gallery_title", height=pt(40))
            with Grid(columns=3, gap=pt(12)):
                for seed in seeds:
                    Image(
                        f"https://picsum.photos/seed/{seed}/600/360",
                        id=_rand_id("img"),
                        alt=f"random image seed {seed}",
                    )


def _shapes() -> None:
    with Slide(id="slide_shapes"):
        with Col(padding=pt(48), gap=pt(20)):
            Title("Shape palette", id="shapes_title", height=pt(40))
            with Grid(columns=4, gap=pt(16)):
                for shape_type, colour in SHAPE_PALETTE:
                    Shape(shape_type=shape_type,
                          fill=colour, id=_rand_id("shape"))


def _chart(theme: Theme) -> None:
    """Render a seaborn bar chart in-memory and embed it as an Image."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    regions = ["Île-de-France", "PACA", "Auvergne-RA", "Occitanie", "Bretagne"]
    values = [random.randint(40, 120) for _ in regions]

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    fig.patch.set_facecolor(theme.background)
    ax.set_facecolor(theme.background)

    sns.barplot(
        x=regions, y=values, ax=ax,
        color=theme.kpi.fill or theme.accent,
        edgecolor=theme.text_primary, linewidth=0.8,
    )
    ax.set_title("Weekly active users by region", color=theme.text_primary,
                 fontsize=16, pad=14, loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("WAU (k)", color=theme.text_secondary)
    ax.tick_params(colors=theme.text_secondary)
    for spine in ax.spines.values():
        spine.set_color(theme.text_secondary)
        spine.set_alpha(0.3)

    with Slide(id="slide_chart"):
        with Col(padding=pt(40), gap=pt(16)):
            Title("Regional split", id="chart_title", height=pt(40))
            Subtitle("Generated with seaborn, uploaded to Drive",
                     id="chart_sub", height=pt(22))
            Image(fig, id="chart_img", alt="WAU by region bar chart")

    plt.close(fig)


def _copy(theme: Theme) -> None:
    with Slide(id="slide_copy"):
        with Col(padding=pt(72), gap=pt(16), justify="center"):
            Text(
                "WHY SLIDEBOX",
                color=theme.accent,
                size=pt(10),
                bold=True,
                height=pt(16),
                id="copy_eyebrow",
            )
            Title("Decks as code.", id="copy_title", height=pt(44))
            Text(LEAD, id="copy_body", size=pt(14))


def build_deck() -> Presentation:
    random.seed()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    theme = _pick_theme()

    with Presentation(title=f"Slidebox deck — {stamp}", theme=theme) as deck:
        _cover(theme, stamp)
        _kpis_three(1)
        _kpis_six(2)
        _gallery()
        _shapes()
        _chart(theme)
        _copy(theme)

    return deck


def main() -> None:
    deck = build_deck()
    pid = deck.push()
    print(
        f"Created {len(deck.children)}-slide deck: https://docs.google.com/presentation/d/{pid}")


if __name__ == "__main__":
    main()
