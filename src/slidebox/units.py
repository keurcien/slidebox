"""Unit conversions for slidebox.

Google Slides uses EMU (English Metric Units) internally: 914400 EMU per
inch, 12700 EMU per point. Slidebox stores every length as an int EMU so
math is exact. At the API boundary, authors can use any of `pt(24)`,
`inches(0.5)`, `px(12)`, or pass a string like `"24pt"`.

The `Length` type accepts all of these and coerces to an int EMU at
validation time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import BeforeValidator

from slidebox.errors import ValidationError

EMU_PER_PT: int = 12700
EMU_PER_INCH: int = 914400
EMU_PER_PX: int = 9525  # 96 DPI convention

DEFAULT_CANVAS_W_EMU: int = 9144000  # 10 in × 914400 = 720 pt (Google default 16:9)
DEFAULT_CANVAS_H_EMU: int = 5143500  # 5.625 in × 914400 = 405 pt


def pt(value: float) -> int:
    return int(round(value * EMU_PER_PT))


def inches(value: float) -> int:
    return int(round(value * EMU_PER_INCH))


def px(value: float) -> int:
    return int(round(value * EMU_PER_PX))


def emu(value: int) -> int:
    return int(value)


@dataclass(frozen=True)
class Percent:
    """Relative length — resolved by the layout engine against its parent."""

    value: float

    def resolve(self, reference_emu: int) -> int:
        return int(round(reference_emu * self.value / 100.0))


def percent(value: float) -> Percent:
    return Percent(value)


_UNIT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*(pt|in|px|emu)?\s*$", re.IGNORECASE)


def _coerce_length(v: Any) -> int | Percent:
    """Normalise any caller input into EMU int or a Percent."""
    if v is None:
        return 0
    if isinstance(v, Percent):
        return v
    if isinstance(v, bool):
        raise ValidationError(f"Booleans are not valid lengths (got {v!r})")
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(round(v))
    if isinstance(v, str):
        m = _UNIT_RE.match(v)
        if not m:
            raise ValidationError(f"Cannot parse length {v!r}")
        n = float(m.group(1))
        unit = (m.group(2) or "pt").lower()
        if unit == "pt":
            return pt(n)
        if unit == "in":
            return inches(n)
        if unit == "px":
            return px(n)
        return int(round(n))  # emu
    raise ValidationError(f"Unsupported length type: {type(v).__name__}")


Length = Annotated[int, BeforeValidator(_coerce_length)]
"""Absolute length in EMU. Accepts int, float, or a string like '24pt'."""
