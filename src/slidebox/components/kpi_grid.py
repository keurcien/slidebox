"""KpiGrid — auto-layout container for 1–6 Kpi cards.

The caller doesn't manage Row/Col; the layout engine handles the
placement rule internally:

    N   layout
    1   [K]
    2   [K][K]
    3   [K][K][K]
    4   [K][K]
        [K][K]
    5   [K][K][K]
        [K][K]
    6   [K][K][K]
        [K][K][K]

Every card in a given row has equal width; rows share vertical space
evenly. Inter-card gap is baked in — no knobs.

KpiGrid is a pure layout container: it emits no API requests itself,
only its Kpi children do.
"""

from __future__ import annotations

from typing import ClassVar

from slidebox.components.base import ContainerComponent
from slidebox.errors import LayoutError
from slidebox.units import pt

GRID_GAP_PT: int = 16
MAX_CARDS: int = 6

# Preferred per-card height. The grid shrinks cards below this when it
# has to fit two rows in a small area; otherwise it caps height here and
# leaves vertical slack at the bottom rather than stretching to fill.
PREFERRED_CARD_HEIGHT_PT: int = 130


def row_split(n: int) -> list[int]:
    """Return the card-count per row for `n` cards.

    Raises:
        LayoutError: if `n` exceeds `MAX_CARDS`.
    """
    if n <= 0:
        return []
    if n > MAX_CARDS:
        raise LayoutError(
            f"KpiGrid supports up to {MAX_CARDS} cards (got {n}); "
            "split across multiple slides."
        )
    if n <= 3:
        return [n]
    half = (n + 1) // 2  # top-heavy for odd N
    return [half, n - half]


class KpiGrid(ContainerComponent):
    """Auto-layout container that stacks 1–6 Kpis in 1 or 2 rows."""

    kind: ClassVar[str] = "kpi_grid"


# Exposed for the layout engine.
GRID_GAP_EMU: int = pt(GRID_GAP_PT)
PREFERRED_CARD_HEIGHT_EMU: int = pt(PREFERRED_CARD_HEIGHT_PT)
