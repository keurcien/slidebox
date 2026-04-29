"""Tiny two-slide deck. Run:

    SLIDEBOX_SA_JSON=path/to/sa.json python examples/hello_world.py
"""

from __future__ import annotations

import os

from slidebox import Presentation, Slide, Subtitle, Text, Title


def main() -> None:
    sa = os.environ.get("SLIDEBOX_SA_JSON")

    with Presentation(title="Hello slidebox", service_account_file=sa) as deck:
        with Slide(id="cover"):
            Title("Hello, slidebox.", id="cover_title")
            Subtitle("Declarative Google Slides for Python.", id="cover_sub")

        with Slide(id="details"):
            Title("How it works", id="how_title")
            Text(
                "Write your deck with context managers. "
                "Call push(). Slidebox compiles one atomic batchUpdate.",
                id="how_body",
            )

    pid = deck.push()
    print(f"Created presentation: https://docs.google.com/presentation/d/{pid}")


if __name__ == "__main__":
    main()
