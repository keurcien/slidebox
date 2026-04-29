from __future__ import annotations

import pytest

from slidebox.errors import ValidationError
from slidebox.units import EMU_PER_INCH, EMU_PER_PT, _coerce_length, emu, inches, percent, pt, px


def test_pt_to_emu() -> None:
    assert pt(1) == EMU_PER_PT
    assert pt(24) == 24 * EMU_PER_PT


def test_inches_to_emu() -> None:
    assert inches(1) == EMU_PER_INCH
    assert inches(0.5) == EMU_PER_INCH // 2


def test_px_is_96dpi() -> None:
    # 96 px per inch => 914400 / 96 = 9525 EMU/px
    assert px(96) == EMU_PER_INCH


def test_emu_is_identity() -> None:
    assert emu(12345) == 12345


def test_percent_resolves_against_reference() -> None:
    assert percent(50).resolve(1000) == 500
    assert percent(25).resolve(400) == 100


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("24pt", 24 * EMU_PER_PT),
        ("  24pt  ", 24 * EMU_PER_PT),
        ("0.5in", EMU_PER_INCH // 2),
        ("48px", 48 * 9525),
        ("1000emu", 1000),
        ("12", pt(12)),  # bare number defaults to pt
    ],
)
def test_string_coercion(raw: str, expected: int) -> None:
    assert _coerce_length(raw) == expected


def test_bool_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _coerce_length(True)


def test_unparsable_string_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _coerce_length("lots of pt")
