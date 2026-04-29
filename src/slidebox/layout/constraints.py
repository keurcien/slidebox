"""Normalise padding / margin / gap kwargs into a 4-tuple (t, r, b, l)."""

from __future__ import annotations

from collections.abc import Iterable

from slidebox.errors import ValidationError
from slidebox.units import _coerce_length


def normalise_padding(value: object) -> tuple[int, int, int, int]:
    """Accept int, 2-tuple (vertical, horizontal), or 4-tuple (t, r, b, l)."""
    if value is None:
        return (0, 0, 0, 0)
    if isinstance(value, (int, float, str)):
        v = _coerce_length(value)
        if not isinstance(v, int):
            raise ValidationError("padding cannot be a percent value")
        return (v, v, v, v)
    if isinstance(value, Iterable):
        vals = [_coerce_length(v) for v in value]
        int_vals: list[int] = []
        for v in vals:
            if not isinstance(v, int):
                raise ValidationError("padding cannot contain a percent value")
            int_vals.append(v)
        if len(int_vals) == 2:
            vy, vx = int_vals
            return (vy, vx, vy, vx)
        if len(int_vals) == 4:
            return (int_vals[0], int_vals[1], int_vals[2], int_vals[3])
    raise ValidationError(f"Invalid padding spec: {value!r}")
