"""Chained builder API.

The only thing engineers should use day-to-day. Wraps the Pydantic
schema and handles object-id generation. Every card method takes
required `col`, `row`, `span` (=cells, rows) and an optional
`object_id` for stable round-trip patching.
"""

from __future__ import annotations

from slidebox.grid import GridRes
from slidebox.schema import (
    Background,
    BodyCard,
    Card,
    Deck,
    EyebrowCard,
    HeaderCard,
    ImageCard,
    KpiCard,
    LogoCard,
    Slide,
    SubtitleCard,
)


def _normalize_span(span: int | tuple[int, int]) -> tuple[int, int]:
    if isinstance(span, int):
        return (span, 1)
    return span


def slide_object_id(deck_id: str, ordinal: int) -> str:
    return f"{deck_id}_slide_{ordinal:02d}"


def card_object_id(slide_id: str, type_: str, ordinal: int) -> str:
    return f"{slide_id}.{type_}.{ordinal}"


class SlideBuilder:
    def __init__(self, deck: DeckBuilder, slide: Slide) -> None:
        self._deck = deck
        self._slide = slide
        self._counts: dict[str, int] = {}

    @property
    def model(self) -> Slide:
        """The current Slide pydantic model (read-only snapshot)."""
        return self._slide

    def _next_id(self, type_: str, explicit: str | None) -> str:
        if explicit is not None:
            return explicit
        n = self._counts.get(type_, 0) + 1
        self._counts[type_] = n
        return card_object_id(self._slide.object_id, type_, n)

    def _add(self, card: Card) -> SlideBuilder:
        self._slide = self._slide.model_copy(
            update={"cards": [*self._slide.cards, card]}
        )
        # Re-validate
        self._slide = Slide.model_validate(self._slide.model_dump())
        # Sync back into deck
        self._deck._replace_slide(self._slide)
        return self

    # ---- card methods ------------------------------------------------

    def header(
        self,
        text: str,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        size: str = "h1",
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        return self._add(
            HeaderCard(
                object_id=self._next_id("header", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                text=text,
                size=size,
            )
        )

    def subtitle(
        self,
        text: str,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        return self._add(
            SubtitleCard(
                object_id=self._next_id("subtitle", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                text=text,
            )
        )

    def eyebrow(
        self,
        text: str,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        return self._add(
            EyebrowCard(
                object_id=self._next_id("eyebrow", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                text=text,
            )
        )

    def body(
        self,
        paragraphs: list[str] | str,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        return self._add(
            BodyCard(
                object_id=self._next_id("body", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                paragraphs=paragraphs,
            )
        )

    def kpi(
        self,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        value: str,
        label: str | None = None,
        unit: str | None = None,
        delta: str | None = None,
        delta_dir: str = "neutral",
        size: str = "lg",
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        return self._add(
            KpiCard(
                object_id=self._next_id("kpi", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                label=label,
                value=value,
                unit=unit,
                delta=delta,
                delta_dir=delta_dir,
                size=size,
            )
        )

    def image(
        self,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        source_url: str | None = None,
        drive_file_id: str | None = None,
        placeholder_tone: str | None = None,
        rounded: bool = False,
        caption: str | None = None,
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        return self._add(
            ImageCard(
                object_id=self._next_id("image", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                source_url=source_url,
                drive_file_id=drive_file_id,
                placeholder_tone=placeholder_tone,
                rounded=rounded,
                caption=caption,
            )
        )

    def logo(
        self,
        *,
        col: int,
        row: int,
        span: int | tuple[int, int],
        variant: str = "black",
        size: str = "md",
        object_id: str | None = None,
    ) -> SlideBuilder:
        cs, rs = _normalize_span(span)
        return self._add(
            LogoCard(
                object_id=self._next_id("logo", object_id),
                col_start=col,
                col_span=cs,
                row_start=row,
                row_span=rs,
                variant=variant,
                size=size,
            )
        )

    def build(self) -> Deck:
        return self._deck.build()

    @property
    def deck(self) -> DeckBuilder:
        return self._deck

    # Allow chaining back to the deck for a new slide.
    def slide(
        self,
        *,
        bg: Background = "beige",
        grid: GridRes = "fine",
        label: str | None = None,
        speaker_notes: str | None = None,
        object_id: str | None = None,
    ) -> SlideBuilder:
        return self._deck.slide(
            bg=bg,
            grid=grid,
            label=label,
            speaker_notes=speaker_notes,
            object_id=object_id,
        )


class DeckBuilder:
    def __init__(self, deck: Deck) -> None:
        self._deck = deck
        self._slide_builders: list[SlideBuilder] = []

    @classmethod
    def new(cls, *, title: str, object_id: str | None = None) -> DeckBuilder:
        oid = object_id or "deck"
        return cls(Deck(object_id=oid, title=title, slides=[]))

    def slide(
        self,
        *,
        bg: Background = "beige",
        grid: GridRes = "fine",
        label: str | None = None,
        speaker_notes: str | None = None,
        object_id: str | None = None,
    ) -> SlideBuilder:
        ordinal = len(self._deck.slides) + 1
        oid = object_id or slide_object_id(self._deck.object_id, ordinal)
        s = Slide(
            object_id=oid,
            background=bg,
            grid=grid,
            label=label,
            speaker_notes=speaker_notes,
            cards=[],
        )
        self._deck = self._deck.model_copy(
            update={"slides": [*self._deck.slides, s]}
        )
        sb = SlideBuilder(self, s)
        self._slide_builders.append(sb)
        return sb

    def _replace_slide(self, slide: Slide) -> None:
        new_slides = [
            slide if s.object_id == slide.object_id else s for s in self._deck.slides
        ]
        self._deck = self._deck.model_copy(update={"slides": new_slides})

    def build(self) -> Deck:
        # Final validation pass — re-run discriminated-union + cross-deck checks.
        return Deck.model_validate(self._deck.model_dump())

    @property
    def title(self) -> str:
        return self._deck.title

    @property
    def object_id(self) -> str:
        return self._deck.object_id


# Bind a class-method alias on Deck so the spec's `Deck.new(...)`
# entrypoint works while the chainable thing is actually a DeckBuilder.
def _deck_new(cls: type[Deck], *, title: str, object_id: str | None = None) -> DeckBuilder:
    return DeckBuilder.new(title=title, object_id=object_id)


Deck.new = classmethod(_deck_new)  # type: ignore[attr-defined]
