"""Kpi — a professional metric card.

Opinionated on purpose: the only knobs the author sees are `label`,
`value`, `trend`, and (rarely) `fill`. Everything else — padding,
corner radius, font sizes, colours — is baked in or driven by the
active `Theme`, so KPIs look consistent across decks.

    ┌────────────────────────────┐
    │  REVENUE                   │   small-caps label
    │                            │
    │  $4.2M                     │   large headline
    │  ▲ +12%                    │   inline trend with arrow
    └────────────────────────────┘
"""

from __future__ import annotations

from typing import Any, ClassVar

from slidebox.components.base import ContainerComponent
from slidebox.components.layout import Col, Spacer
from slidebox.components.shape import Shape, ShapeType
from slidebox.components.text import Text
from slidebox.context import current_theme
from slidebox.units import pt

# Baked-in visual constants. Themes customise colours, not geometry.
# These are tuned so two rows of KPIs fit on a 405pt slide with
# room for title + subtitle above.
_CORNER_RADIUS_PT = 8
_PADDING_PT = 14
_LABEL_SIZE_PT = 9
_VALUE_SIZE_PT = 24
_TREND_SIZE_PT = 10
_LABEL_HEIGHT_PT = 12
_VALUE_HEIGHT_PT = 28
_TREND_HEIGHT_PT = 14
_INNER_GAP_PT = 4


class Kpi(ContainerComponent):
    """Labelled metric card.

    Args:
        label: Short descriptor ("Revenue").
        value: The headline number ("$4.2M").
        trend: Optional change indicator ("+12%"). Sign picks the colour
            and arrow (▲ for +, ▼ for -, bare for other).
        fill: Override the card background. Defaults to `theme.kpi.fill`.
    """

    kind: ClassVar[str] = "kpi"

    label: str = ""
    value: str = ""
    trend: str | None = None
    fill: str | None = None

    def __init__(self, label: str = "", value: str = "", /, **kwargs: Any) -> None:
        super().__init__(label=label, value=value, **kwargs)

    def build(self) -> None:
        theme = current_theme()
        colours = theme.resolve_kpi_colors() if theme else self._hardcoded_colours()

        fill = self.fill or colours["fill"]

        # Forward the user id to the card shape; derive child ids so the
        # Updater can replace any sub-element later.
        root_id = self.id
        self.id = None
        label_id = f"{root_id}_label" if root_id else None
        value_id = f"{root_id}_value" if root_id else None
        trend_id = f"{root_id}_trend" if root_id else None

        trend_display, trend_color = self._trend_display(colours)

        with Shape(
            shape_type=ShapeType.ROUND_RECTANGLE,
            fill=fill,
            corner_radius=_CORNER_RADIUS_PT,
            id=root_id,
        ), Col(gap=pt(_INNER_GAP_PT), padding=pt(_PADDING_PT), align="start"):
            Text(
                self.label.upper(),
                color=colours["label_color"],
                size=pt(_LABEL_SIZE_PT),
                bold=True,
                id=label_id,
                height=pt(_LABEL_HEIGHT_PT),
            )
            # Flex gap pushes value + trend toward the bottom.
            Spacer(flex=1)
            Text(
                self.value,
                color=colours["value_color"],
                size=pt(_VALUE_SIZE_PT),
                bold=True,
                id=value_id,
                height=pt(_VALUE_HEIGHT_PT),
            )
            if self.trend:
                Text(
                    trend_display,
                    color=trend_color,
                    size=pt(_TREND_SIZE_PT),
                    bold=True,
                    id=trend_id,
                    height=pt(_TREND_HEIGHT_PT),
                )

    # ── helpers ───────────────────────────────────────────────────────
    def _trend_display(self, colours: dict[str, str]) -> tuple[str, str]:
        raw = (self.trend or "").strip()
        if raw.startswith("+"):
            return f"▲ {raw}", colours["trend_up_text"]
        if raw.startswith("-"):
            return f"▼ {raw}", colours["trend_down_text"]
        return raw, colours["trend_neutral_text"]

    @staticmethod
    def _hardcoded_colours() -> dict[str, str]:
        """Fallbacks when no Presentation theme is in scope (orphan trees)."""
        return {
            "fill": "#1f2330",
            "label_color": "#9aa0a6",
            "value_color": "#ffffff",
            "trend_up_text": "#34d058",
            "trend_down_text": "#f85149",
            "trend_neutral_text": "#9aa0a6",
        }
