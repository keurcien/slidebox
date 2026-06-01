"""Grid math: cell -> EMU bounding box, overlap detection.

The spec (§2) describes the slide as "1920 x 1080 EMU-equivalent
points" but the Google Slides canonical 16:9 surface is actually
9144000 x 5143500 EMU (720 x 405 pt at 12700 EMU/pt). Treating the
spec's 96pt gutter / 32pt gap as raw pt values against the actual
405pt slide height leaves negative row heights at fine (12 x 8).

Resolution: read the spec's gutter and gap in a 1920 x 1080 *design
canvas*, do the layout there, then linearly scale into EMU. The
ratio is uniform (16:9 in / out), so cells are not distorted.
"""

from __future__ import annotations

from typing import Literal

from slidebox.types import SLIDE_H_EMU, SLIDE_W_EMU

GridRes = Literal["coarse", "standard", "fine"]

_GRID_DIMS: dict[str, tuple[int, int]] = {
    "coarse": (6, 4),
    "standard": (12, 6),
    "fine": (12, 8),
}

# Spec §2 design canvas — gutter/gap are expressed in these points.
DESIGN_W_PT = 1920
DESIGN_H_PT = 1080

GUTTER_PT = 96
GAP_PT = 32

EMU_PER_DESIGN_PT_X = SLIDE_W_EMU / DESIGN_W_PT
EMU_PER_DESIGN_PT_Y = SLIDE_H_EMU / DESIGN_H_PT


def grid_dims(res: GridRes) -> tuple[int, int]:
    return _GRID_DIMS[res]


def cell_to_emu(
    col_start: int,
    col_span: int,
    row_start: int,
    row_span: int,
    res: GridRes = "fine",
    gutter_pt: int = GUTTER_PT,
    gap_pt: int = GAP_PT,
) -> tuple[int, int, int, int]:
    cols, rows = grid_dims(res)
    cw = (DESIGN_W_PT - 2 * gutter_pt - (cols - 1) * gap_pt) / cols
    rh = (DESIGN_H_PT - 2 * gutter_pt - (rows - 1) * gap_pt) / rows
    x = gutter_pt + (col_start - 1) * (cw + gap_pt)
    y = gutter_pt + (row_start - 1) * (rh + gap_pt)
    w = col_span * cw + (col_span - 1) * gap_pt
    h = row_span * rh + (row_span - 1) * gap_pt
    return (
        int(x * EMU_PER_DESIGN_PT_X),
        int(y * EMU_PER_DESIGN_PT_Y),
        int(w * EMU_PER_DESIGN_PT_X),
        int(h * EMU_PER_DESIGN_PT_Y),
    )


def cells_overlap(a: object, b: object) -> bool:
    """True if two cards' cell rectangles intersect.

    Both arguments must expose col_start / col_span / row_start / row_span
    (any CellSpan-derived model satisfies this).
    """
    a_c1: int = a.col_start  # type: ignore[attr-defined]
    a_c2: int = a_c1 + a.col_span  # type: ignore[attr-defined]
    a_r1: int = a.row_start  # type: ignore[attr-defined]
    a_r2: int = a_r1 + a.row_span  # type: ignore[attr-defined]
    b_c1: int = b.col_start  # type: ignore[attr-defined]
    b_c2: int = b_c1 + b.col_span  # type: ignore[attr-defined]
    b_r1: int = b.row_start  # type: ignore[attr-defined]
    b_r2: int = b_r1 + b.row_span  # type: ignore[attr-defined]
    return bool(a_c1 < b_c2 and b_c1 < a_c2 and a_r1 < b_r2 and b_r1 < a_r2)


def in_bounds(
    col_start: int, col_span: int, row_start: int, row_span: int, res: GridRes
) -> bool:
    cols, rows = grid_dims(res)
    return (
        1 <= col_start <= cols
        and 1 <= row_start <= rows
        and col_start + col_span - 1 <= cols
        and row_start + row_span - 1 <= rows
        and col_span >= 1
        and row_span >= 1
    )
