"""BrandTheme — Choose defaults; pluggable per workspace."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from slidebox.types import RGB


class BrandTheme(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    beige: RGB = RGB(0xFE, 0xF8, 0xED)
    nude: RGB = RGB(0xD1, 0xAE, 0x9B)
    black: RGB = RGB(0x0B, 0x11, 0x15)
    white: RGB = RGB(0xFF, 0xFF, 0xFF)

    grey_300: RGB = RGB(0xD8, 0xD9, 0xDA)
    grey_500: RGB = RGB(0x8A, 0x8D, 0x8F)
    grey_700: RGB = RGB(0x43, 0x46, 0x47)

    accent_up: RGB = RGB(0x13, 0x48, 0x2B)
    accent_down: RGB = RGB(0x8A, 0x2A, 0x2A)

    # Hairline border colors for KPI cards. Slides API doesn't honour
    # alpha on outline colors, so these are pre-blended:
    #   on black:  rgba(255,255,255,0.18) over theme.black  -> #373C3F
    #   on nude:   rgba( 11, 17, 21,0.18) over theme.nude   -> #AD9283
    # Override these on a custom theme if you change `black` or `nude`,
    # otherwise the pre-blend won't match.
    kpi_border_on_dark: RGB = RGB(0x37, 0x3C, 0x3F)
    kpi_border_on_nude: RGB = RGB(0xAD, 0x92, 0x83)

    serif_family: str = "Sangbleu Republic"
    sans_family: str = "Maison Neue"

    def background_rgb(self, name: str) -> RGB:
        return {
            "beige": self.beige,
            "white": self.white,
            "nude": self.nude,
            "black": self.black,
        }[name]

    def text_on(self, background: str) -> RGB:
        return self.white if background == "black" else self.black

    def delta_color(self, direction: str) -> RGB:
        return {
            "up": self.accent_up,
            "down": self.accent_down,
            "neutral": self.grey_500,
        }[direction]

    def kpi_border_for(self, background: str) -> RGB:
        """Hairline border color for KPI cards on `background`."""
        if background == "black":
            return self.kpi_border_on_dark
        if background == "nude":
            return self.kpi_border_on_nude
        return self.grey_300  # white / beige
