"""slidebox — grid-based slide library for Choose.

Build standardised, on-brand decks from Python with a declarative,
LLM-friendly builder. Decks render to PowerPoint (.pptx) via python-pptx,
and convert to native Google Slides on upload to Drive.

    from slidebox import Deck, save, to_google_slides

    deck = (
        Deck.new(title="Revue hebdomadaire")
        .slide(bg="beige")
        .header("L'activité de la semaine.", size="h1", col=1, row=2, span=(10, 1))
        .kpi(label="GMV", value="5,1", unit="M€", delta="+16%", delta_dir="up",
             size="md", col=1, row=4, span=(3, 4))
    ).build()

    save(deck, "report.pptx")                 # local .pptx
    g = to_google_slides(deck, name="Report") # -> Google Slides on Drive
    print(g.url)
"""

from __future__ import annotations

from slidebox._version import __version__
from slidebox.builder import (
    DeckBuilder,
    SlideBuilder,
    card_object_id,
    slide_object_id,
)
from slidebox.drive import (
    CredentialsProvider,
    GoogleSlides,
    save,
    to_google_slides,
)
from slidebox.fit import (
    Overflow,
    fit_report,
    format_fit,
    missing_families,
    overflows,
    report_fit,
)
from slidebox.measure import (
    BUNDLED_FAMILIES,
    FitResult,
    bundled_fonts,
    measure_text,
)
from slidebox.render import render
from slidebox.schema import (
    AbsoluteBox,
    Background,
    BodyCard,
    Card,
    CellSpan,
    Deck,
    EyebrowCard,
    HeaderCard,
    ImageCard,
    KpiCard,
    LogoCard,
    PanelCard,
    Slide,
    SubtitleCard,
    TableCard,
    TableCell,
)
from slidebox.theme import BrandTheme
from slidebox.types import RGB

__all__ = [
    "BUNDLED_FAMILIES",
    "RGB",
    "AbsoluteBox",
    "Background",
    "BodyCard",
    "BrandTheme",
    "Card",
    "CellSpan",
    "CredentialsProvider",
    "Deck",
    "DeckBuilder",
    "EyebrowCard",
    "FitResult",
    "GoogleSlides",
    "HeaderCard",
    "ImageCard",
    "KpiCard",
    "LogoCard",
    "Overflow",
    "PanelCard",
    "Slide",
    "SlideBuilder",
    "SubtitleCard",
    "TableCard",
    "TableCell",
    "__version__",
    "bundled_fonts",
    "card_object_id",
    "fit_report",
    "format_fit",
    "measure_text",
    "missing_families",
    "overflows",
    "render",
    "report_fit",
    "save",
    "slide_object_id",
    "to_google_slides",
]
