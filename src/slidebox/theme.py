"""Theme — one place to declare colours, fonts, and component styling.

Themes are Pydantic models. Every field has a sensible default so
`Theme()` is valid; users override whatever they care about:

    custom = Theme(
        background="#0b0f19",
        text_primary="#f5f7fa",
        text_secondary="#9aa0a6",
        accent="#4285f4",
        font_family="Inter",
    )

The theme flows three ways:
1. `Presentation(theme=...)` sets the active theme for the whole deck.
2. Component kwargs override the theme at the instance level
   (`Text("hi", color="#ff0000")`).
3. Composite components (`Kpi`) read the theme via `current_theme()`
   during `build()` so their sub-elements pick up themed defaults.

Text styles are *computed* from the theme fields live, so
`Theme(font_family="Roboto")` or `themes.dark().merge(accent="#ff5a5f")`
works without calling any rebuild helper.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from slidebox.units import Length, pt


class TextStyleDef(BaseModel):
    """Resolved look for a named style key (e.g. 'h1', 'body')."""

    size: Length = pt(14)
    color: str = "#111111"
    font: str = "Inter"
    bold: bool = False
    italic: bool = False


class KpiTheme(BaseModel):
    """Colour palette for the Kpi composite.

    Geometry (padding, corner radius, font sizes) is fixed on purpose.
    Only colours are themable so KPIs stay consistent across decks.
    """

    fill: str = "#1f2330"                # card background
    label_color: str | None = None       # None → theme.text_secondary
    value_color: str | None = None       # None → theme.text_primary
    trend_up_text: str = "#34d058"
    trend_down_text: str = "#f85149"
    trend_neutral_text: str = "#9aa0a6"


_STYLE_PRESETS: dict[str, tuple[int, bool, bool]] = {
    # name -> (size_pt, bold, use_secondary_color)
    "h1": (36, True, False),
    "h2": (24, True, False),
    "h3": (18, True, False),
    "subtitle": (18, False, True),
    "body": (14, False, False),
    "caption": (11, False, True),
}


class Theme(BaseModel):
    """Declarative styling defaults applied at compile time."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Colours
    background: str = "#ffffff"
    text_primary: str = "#111111"
    text_secondary: str = "#5f6368"
    accent: str = "#1a73e8"

    # Typography
    font_family: str = "Inter"

    # Explicit per-style overrides. Usually empty — styles are computed
    # from the colour/font fields above, which is why simply setting
    # `font_family="Roboto"` is enough to re-skin every text element.
    text_styles: dict[str, TextStyleDef] = Field(default_factory=dict)

    # Components
    kpi: KpiTheme = Field(default_factory=KpiTheme)

    # Shape defaults — apply when a Shape has no explicit fill/stroke.
    shape_fill: str | None = None
    shape_stroke: str | None = None

    def resolve_text_style(self, name: str) -> TextStyleDef:
        """Return the concrete text style for a named key.

        Explicit overrides in `text_styles` win; otherwise fields are
        derived from the theme's colour/font defaults on the fly.
        """
        if name in self.text_styles:
            return self.text_styles[name]
        size_pt, bold, use_secondary = _STYLE_PRESETS.get(name, (14, False, False))
        colour = self.text_secondary if use_secondary else self.text_primary
        return TextStyleDef(size=pt(size_pt), color=colour, font=self.font_family, bold=bold)

    def resolve_kpi_colors(self) -> dict[str, str]:
        """Collapse the Kpi sub-theme against the parent theme.

        Any `None` field on `KpiTheme` falls back to the matching Theme
        field so themes don't have to duplicate colours.
        """
        return {
            "fill": self.kpi.fill,
            "label_color": self.kpi.label_color or self.text_secondary,
            "value_color": self.kpi.value_color or self.text_primary,
            "trend_up_text": self.kpi.trend_up_text,
            "trend_down_text": self.kpi.trend_down_text,
            "trend_neutral_text": self.kpi.trend_neutral_text,
        }

    def merge(self, **overrides: Any) -> Theme:
        """Return a copy with top-level fields replaced."""
        return self.model_copy(update=overrides)


class _Themes:
    """Namespace for built-in theme presets. Each call returns a fresh instance."""

    @staticmethod
    def default() -> Theme:
        return Theme()

    @staticmethod
    def dark() -> Theme:
        return Theme(
            background="#0f1116",
            text_primary="#f5f7fa",
            text_secondary="#9aa0a6",
            accent="#4285f4",
            kpi=KpiTheme(fill="#1f2330"),
        )

    @staticmethod
    def minimal() -> Theme:
        return Theme(
            background="#ffffff",
            text_primary="#000000",
            text_secondary="#666666",
            accent="#000000",
            font_family="Helvetica Neue",
            kpi=KpiTheme(
                fill="#f4f4f4",
                label_color="#666666",
                value_color="#000000",
                trend_up_text="#137333",
                trend_down_text="#a50e0e",
                trend_neutral_text="#666666",
            ),
        )

    @staticmethod
    def slate() -> Theme:
        """A softer dark theme with blue-grey tones."""
        return Theme(
            background="#1a2332",
            text_primary="#e8eef5",
            text_secondary="#8fa0b3",
            accent="#5b9dff",
            kpi=KpiTheme(
                fill="#243447",
                label_color="#8fa0b3",
                value_color="#e8eef5",
            ),
        )


themes = _Themes()
