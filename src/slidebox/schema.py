"""Pydantic source of truth for Deck / Slide / Card.

Card is a discriminated union over the `type` field. Validation is
fail-fast: overlapping cells, out-of-bounds spans, duplicate ids,
header word counts, KPI value type — all rejected at model build.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from slidebox.grid import GridRes, cells_overlap, grid_dims, in_bounds

Background = Literal["beige", "white", "nude", "black"]


class CellSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    col_start: int = Field(..., ge=1, le=12)
    col_span: int = Field(..., ge=1, le=12)
    row_start: int = Field(..., ge=1, le=8)
    row_span: int = Field(..., ge=1, le=8)


class _CardBase(CellSpan):
    object_id: str


class HeaderCard(_CardBase):
    type: Literal["header"] = "header"
    text: str
    size: Literal["h1", "display", "keyword"] = "h1"

    @model_validator(mode="after")
    def _word_cap(self) -> HeaderCard:
        if len(self.text.split()) > 15:
            raise ValueError(
                f"header text exceeds the 15-word brand cap: {self.text!r}"
            )
        return self


class SubtitleCard(_CardBase):
    type: Literal["subtitle"] = "subtitle"
    text: str


class EyebrowCard(_CardBase):
    type: Literal["eyebrow"] = "eyebrow"
    text: str


class BodyCard(_CardBase):
    type: Literal["body"] = "body"
    paragraphs: list[str]


class KpiCard(_CardBase):
    type: Literal["kpi"] = "kpi"
    label: str | None = None
    value: str
    unit: str | None = None
    delta: str | None = None
    delta_dir: Literal["up", "down", "neutral"] = "neutral"
    size: Literal["sm", "md", "lg", "xl"] = "lg"

    @model_validator(mode="after")
    def _value_is_string(self) -> KpiCard:
        if not isinstance(self.value, str):
            raise ValueError("KPI value must be a string to preserve formatting")
        return self


class ImageCard(_CardBase):
    type: Literal["image"] = "image"
    source_url: str | None = None
    drive_file_id: str | None = None
    placeholder_tone: str | None = None
    rounded: bool = False
    caption: str | None = None

    @model_validator(mode="after")
    def _has_source(self) -> ImageCard:
        if not (self.source_url or self.drive_file_id or self.placeholder_tone):
            raise ValueError(
                "ImageCard needs one of source_url / drive_file_id / placeholder_tone"
            )
        return self


class LogoCard(_CardBase):
    type: Literal["logo"] = "logo"
    variant: Literal["black", "white"] = "black"
    size: Literal["sm", "md", "lg"] = "md"


Card = Annotated[
    HeaderCard | SubtitleCard | EyebrowCard | BodyCard | KpiCard | ImageCard | LogoCard,
    Field(discriminator="type"),
]


class Slide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str
    background: Background = "beige"
    grid: GridRes = "fine"
    cards: list[Card] = Field(default_factory=list)
    speaker_notes: str | None = None
    label: str | None = None

    @model_validator(mode="after")
    def _validate_layout(self) -> Slide:
        cols, rows = grid_dims(self.grid)
        seen: list[Card] = []
        for c in self.cards:
            if not in_bounds(c.col_start, c.col_span, c.row_start, c.row_span, self.grid):
                raise ValueError(
                    f"card {c.object_id!r} out of {self.grid} grid "
                    f"({cols}x{rows}): col {c.col_start}+{c.col_span} "
                    f"row {c.row_start}+{c.row_span}"
                )
            for o in seen:
                if cells_overlap(c, o):
                    raise ValueError(
                        f"cards {c.object_id!r} and {o.object_id!r} overlap on slide {self.object_id!r}"
                    )
            seen.append(c)
        return self


class Deck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_id: str
    title: str
    slides: list[Slide] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> Deck:
        seen: set[str] = set()
        for s in self.slides:
            if s.object_id in seen:
                raise ValueError(f"duplicate slide object_id: {s.object_id!r}")
            seen.add(s.object_id)
            for c in s.cards:
                if c.object_id in seen:
                    raise ValueError(f"duplicate card object_id: {c.object_id!r}")
                seen.add(c.object_id)
        return self

    def find(self, object_id: str) -> Card | Slide:
        for s in self.slides:
            if s.object_id == object_id:
                return s
            for c in s.cards:
                if c.object_id == object_id:
                    return c
        raise KeyError(f"no element with object_id={object_id!r}")

    def to_json(self, *, canonical: bool = False) -> str:
        if canonical:
            import json

            data = self.model_dump(mode="json")
            return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)
        return self.model_dump_json(indent=2)


__all__ = [
    "Background",
    "BodyCard",
    "Card",
    "CellSpan",
    "Deck",
    "EyebrowCard",
    "HeaderCard",
    "ImageCard",
    "KpiCard",
    "LogoCard",
    "Slide",
    "SubtitleCard",
]
