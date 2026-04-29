"""Weight-based flex solver.

Given a total main-axis length and a list of children with either a
fixed size or a flex weight, return the size each child should receive
along the main axis. Fixed sizes are honoured first; whatever remains
is divided among flexible children in proportion to their weights.

Gaps between children are passed in separately and subtracted from the
pool before distribution — matching CSS flexbox semantics for `gap`.
"""

from __future__ import annotations

from dataclasses import dataclass

from slidebox.errors import LayoutError


@dataclass(frozen=True, slots=True)
class FlexChild:
    fixed: int | None  # fixed EMU size along the main axis, if known
    flex: int  # weight (default 1 when fixed is None, else 0)


def solve_flex(main_axis_size: int, children: list[FlexChild], gap: int = 0) -> list[int]:
    """Return the main-axis size allocated to each child (EMU)."""
    if not children:
        return []

    gap_total = gap * (len(children) - 1)
    remaining = main_axis_size - gap_total
    if remaining < 0:
        raise LayoutError(
            f"gap ({gap_total} EMU) exceeds available space ({main_axis_size} EMU)"
        )

    fixed_total = sum(c.fixed for c in children if c.fixed is not None)
    if fixed_total > remaining:
        raise LayoutError(
            f"fixed children ({fixed_total} EMU) exceed available space ({remaining} EMU)"
        )

    flex_pool = remaining - fixed_total
    flex_weight_total = sum(c.flex for c in children if c.fixed is None)

    result: list[int] = []
    running = 0  # track cumulative floor-rounded size to avoid drift
    for idx, child in enumerate(children):
        if child.fixed is not None:
            result.append(child.fixed)
            running += child.fixed
        else:
            if flex_weight_total == 0:
                result.append(0)
                continue
            # Allocate this child's slice, using position to distribute
            # rounding error evenly across children.
            ideal = (child.flex * flex_pool) // flex_weight_total
            # Last flex child gets whatever's left so totals match exactly.
            is_last_flex = not any(
                c.fixed is None for c in children[idx + 1 :]
            )
            if is_last_flex:
                ideal = flex_pool - sum(
                    r for r, c in zip(result, children, strict=False) if c.fixed is None
                )
            result.append(ideal)
            running += ideal

    return result
