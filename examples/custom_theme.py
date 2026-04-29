"""Build your own theme by merging onto a preset."""

from __future__ import annotations

from slidebox import Presentation, Slide, Title, themes


def main() -> None:
    monochrome = themes.minimal().merge(
        accent="#ff5a5f",
        font_family="IBM Plex Sans",
    )
    with Presentation(title="Custom theme", theme=monochrome) as deck:
        with Slide():
            Title("Monochrome with a pop of coral")

    print(deck.to_json())


if __name__ == "__main__":
    main()
