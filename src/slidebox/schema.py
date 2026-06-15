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

# A "#RRGGBB" (or "RRGGBB") hex color, for exact off-palette overrides.
_HEX = r"^#?[0-9A-Fa-f]{6}$"


class CellSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    col_start: int = Field(..., ge=1, le=12)
    col_span: int = Field(..., ge=1, le=12)
    row_start: int = Field(..., ge=1, le=8)
    row_span: int = Field(..., ge=1, le=8)


class AbsoluteBox(BaseModel):
    """Absolute placement in EMU (English Metric Units, 914400 per inch).

    This is python-pptx's native coordinate system; pass `pptx.util.Emu`,
    `Inches`, `Pt`, etc. (all int subclasses) or raw ints. Coordinates may be
    negative or exceed the slide, so a card can bleed off any edge.
    """

    model_config = ConfigDict(extra="forbid")

    x: int
    y: int
    w: int = Field(..., gt=0)
    h: int = Field(..., gt=0)


class _CardBase(BaseModel):
    """Base for every card. Placed *either* on the 12x8 grid (col/row/span)
    *or* by an absolute `bbox` in EMU — the latter for pixel-exact placement
    (and content that must reach past the grid's gutters)."""

    model_config = ConfigDict(extra="forbid")

    object_id: str
    col_start: int | None = None
    col_span: int | None = None
    row_start: int | None = None
    row_span: int | None = None
    bbox: AbsoluteBox | None = None

    @model_validator(mode="after")
    def _check_placement(self) -> _CardBase:
        cells = (self.col_start, self.col_span, self.row_start, self.row_span)
        has_grid = all(v is not None for v in cells)
        any_grid = any(v is not None for v in cells)
        if self.bbox is not None:
            if any_grid:
                raise ValueError(
                    f"{self.object_id}: use either grid cells or a bbox, not both"
                )
        elif not has_grid:
            raise ValueError(
                f"{self.object_id}: provide grid cells (col/row/span) or a bbox"
            )
        return self


class HeaderCard(_CardBase):
    type: Literal["header"] = "header"
    text: str
    size: Literal["h1", "display", "keyword"] = "h1"
    # Exact point size override. When set, the renderer uses it verbatim and
    # skips auto-fit (for pixel-faithful reproduction of an existing deck).
    size_pt: float | None = Field(default=None, gt=0)
    # Exact "#RRGGBB" text color override (default: on-background text color).
    color: str | None = Field(default=None, pattern=_HEX)
    align: Literal["left", "center", "right"] = "left"

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
    # Typographic variant. "serif" (default) is the brand kicker: serif
    # family, italic. "sans" renders the sans family, upright — for decks
    # whose eyebrow/label is a plain uppercase sans tag.
    variant: Literal["serif", "sans"] = "serif"
    # Exact point size override (skips auto-fit). See HeaderCard.size_pt.
    size_pt: float | None = Field(default=None, gt=0)
    # Exact "#RRGGBB" text color override (default: grey_500).
    color: str | None = Field(default=None, pattern=_HEX)
    align: Literal["left", "center", "right"] = "left"


class BodyCard(_CardBase):
    type: Literal["body"] = "body"
    paragraphs: list[str]
    # Text tone. "default" uses the on-background text color (near-black on
    # light, white on dark). "muted" uses grey_700 — for secondary body copy
    # set a step lighter than the on-background color.
    tone: Literal["default", "muted"] = "default"
    # Exact point size override (skips auto-fit). See HeaderCard.size_pt.
    size_pt: float | None = Field(default=None, gt=0)
    # Indices of paragraphs to render fully bold (e.g. [1] = the second).
    # Mid-paragraph emphasis is also supported via **double asterisks**.
    strong: list[int] = Field(default_factory=list)
    # Exact "#RRGGBB" text color override (default: tone-derived color).
    color: str | None = Field(default=None, pattern=_HEX)
    align: Literal["left", "center", "right"] = "left"

    @model_validator(mode="after")
    def _strong_in_range(self) -> BodyCard:
        n = len(self.paragraphs)
        for i in self.strong:
            if not 0 <= i < n:
                raise ValueError(
                    f"strong index {i} out of range for {n} paragraph(s)"
                )
        return self


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
    # Optional "#RRGGBB" frame around the picture (e.g. a white photo border).
    outline: str | None = Field(default=None, pattern=_HEX)
    outline_pt: float = Field(default=1.0, gt=0)
    # Clockwise rotation in degrees, about the picture's center.
    rotation: float = 0.0

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


class PanelCard(_CardBase):
    """A filled background shape.

    A decorative block (a colored side panel, a timeline bar, a node dot, an
    arrowhead) that sits *behind* the other cards. It always renders first,
    and — unlike content cards — it is exempt from the no-overlap rule, since
    its whole purpose is to underlay the image/text placed on top of it.

    `shape` selects the geometry (rectangle / ellipse / triangle); `rounded`
    rounds a rectangle's corners. `fill`/`outline` are exact "#RRGGBB" colors;
    `rotation` is clockwise degrees (e.g. 90 → a right-pointing triangle).
    """

    type: Literal["panel"] = "panel"
    shape: Literal["rectangle", "ellipse", "triangle"] = "rectangle"
    # Fill is `tone` (a brand background tone) by default; set `fill` to an
    # exact "#RRGGBB" hex to override it (for reproducing off-palette colors).
    tone: Background = "beige"
    fill: str | None = Field(default=None, pattern=_HEX)
    rounded: bool = False
    outline: str | None = Field(default=None, pattern=_HEX)
    outline_pt: float = Field(default=1.0, gt=0)
    rotation: float = 0.0


class TableCell(BaseModel):
    """One table cell: text plus optional per-cell styling."""

    model_config = ConfigDict(extra="forbid")

    text: str = ""
    bold: bool = False
    fill: str | None = Field(default=None, pattern=_HEX)
    color: str | None = Field(default=None, pattern=_HEX)
    align: Literal["left", "center", "right"] = "left"
    size_pt: float | None = Field(default=None, gt=0)


class TableCard(_CardBase):
    """A native table (rows x columns of styled cells).

    `cells` is a rectangular grid (list of rows). `col_widths`/`row_heights`
    are per-column / per-row sizes in EMU (else split evenly). `border` is a
    uniform "#RRGGBB" gridline color; `font` overrides the default sans family.
    Placed by absolute `bbox` (recommended) or on the grid.
    """

    type: Literal["table"] = "table"
    cells: list[list[TableCell]]
    col_widths: list[int] | None = None
    row_heights: list[int] | None = None
    font: str | None = None
    border: str | None = Field(default=None, pattern=_HEX)
    border_pt: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def _rectangular(self) -> TableCard:
        if not self.cells or not self.cells[0]:
            raise ValueError("table needs at least one cell")
        ncol = len(self.cells[0])
        if any(len(r) != ncol for r in self.cells):
            raise ValueError("every table row must have the same column count")
        if self.col_widths is not None and len(self.col_widths) != ncol:
            raise ValueError("col_widths length must match the column count")
        if self.row_heights is not None and len(self.row_heights) != len(self.cells):
            raise ValueError("row_heights length must match the row count")
        return self


Card = Annotated[
    HeaderCard
    | SubtitleCard
    | EyebrowCard
    | BodyCard
    | KpiCard
    | ImageCard
    | LogoCard
    | PanelCard
    | TableCard,
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
            # Absolutely-placed cards carry no grid cells; skip grid bounds.
            if c.bbox is None and not in_bounds(
                c.col_start, c.col_span, c.row_start, c.row_span, self.grid
            ):
                raise ValueError(
                    f"card {c.object_id!r} out of {self.grid} grid "
                    f"({cols}x{rows}): col {c.col_start}+{c.col_span} "
                    f"row {c.row_start}+{c.row_span}"
                )
            for o in seen:
                # Overlap is only checked between two grid-placed content
                # cards. Panels are background underlays, and absolute boxes
                # opt out of grid overlap detection.
                if c.type == "panel" or o.type == "panel":
                    continue
                if c.bbox is not None or o.bbox is not None:
                    continue
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
    "AbsoluteBox",
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
    "PanelCard",
    "Slide",
    "SubtitleCard",
    "TableCard",
    "TableCell",
]
