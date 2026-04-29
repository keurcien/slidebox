"""Subclass `ContainerComponent` to ship your own composite.

Run locally with `SLIDEBOX_SA_JSON=... python examples/custom_component.py`.
"""

from __future__ import annotations

import os
from typing import ClassVar

from slidebox import Col, Presentation, Shape, ShapeType, Slide, Text
from slidebox.components.base import ContainerComponent


class BrandCard(ContainerComponent):
    """A branded callout card with a coloured stripe and a message."""

    kind: ClassVar[str] = "brand_card"

    message: str = ""
    accent: str = "#ff5a5f"

    def __init__(self, message: str = "", /, **kwargs: object) -> None:
        super().__init__(message=message, **kwargs)

    def build(self) -> None:
        with Shape(shape_type=ShapeType.ROUND_RECTANGLE, fill=self.accent, corner_radius=6):
            with Col(gap=12, padding=20):
                Text(self.message, style="h3", color="#ffffff")


def main() -> None:
    sa = os.environ.get("SLIDEBOX_SA_JSON")
    with Presentation(title="Brand demo", service_account_file=sa) as deck:
        with Slide():
            with Col(padding="48pt", gap="24pt"):
                BrandCard("Your custom component is just a subclass.", id="card_1")

    pid = deck.push()
    print(f"https://docs.google.com/presentation/d/{pid}")


if __name__ == "__main__":
    main()
