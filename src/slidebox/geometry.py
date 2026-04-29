"""Geometry primitives.

`Bounds` is the single structure the layout engine assigns to every
component. Coordinates are always integer EMU with the origin at the
top-left of the slide canvas.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Bounds:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def shifted(self, dx: int = 0, dy: int = 0) -> Bounds:
        return Bounds(self.x + dx, self.y + dy, self.w, self.h)

    def inset(self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0) -> Bounds:
        return Bounds(
            self.x + left,
            self.y + top,
            max(0, self.w - left - right),
            max(0, self.h - top - bottom),
        )

    def to_api_transform(self) -> dict[str, object]:
        """Emit a Google Slides API size+transform pair for this bounds.

        Google uses `scaleX=scaleY=1` and moves the element via
        `translateX`/`translateY` — never via size scaling. Keeping scale
        pinned at 1 avoids the class of bugs where a user edits an
        element in the UI and the dimensions no longer match what we
        expected.
        """
        return {
            "size": {
                "width": {"magnitude": self.w, "unit": "EMU"},
                "height": {"magnitude": self.h, "unit": "EMU"},
            },
            "transform": {
                "scaleX": 1,
                "scaleY": 1,
                "translateX": self.x,
                "translateY": self.y,
                "unit": "EMU",
            },
        }
