"""Shared primitive types: RGB colors, EMU helpers."""

from __future__ import annotations

from typing import NamedTuple


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    def as_api(self) -> dict[str, dict[str, float]]:
        return {
            "rgbColor": {
                "red": self.r / 255.0,
                "green": self.g / 255.0,
                "blue": self.b / 255.0,
            }
        }


PT_TO_EMU = 12700
SLIDE_W_EMU = 9144000
SLIDE_H_EMU = 5143500
