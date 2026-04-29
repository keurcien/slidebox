"""Compiler — walks a resolved tree, emits ordered batchUpdate requests.

The compiler is a pure function: (tree, theme) -> BatchPlan. Every IO
concern (auth, network, retry) lives in the client layer.

Ordering invariants enforced here:
  1. A slide is created before any element that lives on it.
  2. A shape is created before text is inserted into it.
  3. Text is inserted before text style is applied.
  4. Alt-text metadata is applied last so it can never block a shape
     from appearing if it validates differently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from slidebox.compile import requests as R
from slidebox.compile.ids import IdAllocator
from slidebox.compile.metadata import encode_metadata
from slidebox.components.base import Component, ContainerComponent
from slidebox.components.image import Image
from slidebox.components.kpi import Kpi
from slidebox.components.kpi_grid import KpiGrid
from slidebox.components.layout import Col, Grid, Row, Spacer, _FlexContainer
from slidebox.components.shape import Shape, ShapeType
from slidebox.components.slide import Slide
from slidebox.components.text import Text
from slidebox.errors import CompileError

if TYPE_CHECKING:
    from slidebox.presentation import Presentation
    from slidebox.theme import TextStyleDef, Theme

_QUOTA_WARN_SLIDES = 100
_QUOTA_WARN_REQUESTS = 2000


@dataclass
class BatchPlan:
    """The product of compilation — ready to send to Google."""

    requests: list[dict[str, Any]] = field(default_factory=list)
    id_map: dict[int, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class Compiler:
    """Turn a resolved Presentation into a BatchPlan."""

    def __init__(self, theme: Theme, allocator: IdAllocator | None = None) -> None:
        self._theme = theme
        self._ids = allocator or IdAllocator()

    def compile(self, deck: Presentation) -> BatchPlan:
        requests: list[dict[str, Any]] = []

        # First pass: allocate IDs for every node. Doing this up front
        # lets sub-compilers reference each other freely by objectId.
        for slide_idx, slide in enumerate(deck.children):
            self._walk_allocate(slide, parent_key=f"slide[{slide_idx}]", index=slide_idx)

        for slide_idx, slide in enumerate(deck.children):
            self._compile_slide(slide, slide_idx, requests)

        plan = BatchPlan(requests=requests, id_map=dict(self._ids.id_map))
        if len(deck.children) > _QUOTA_WARN_SLIDES:
            plan.warnings.append(
                f"{len(deck.children)} slides exceeds the {_QUOTA_WARN_SLIDES}-slide "
                "guideline; consider chunking into separate presentations."
            )
        if len(requests) > _QUOTA_WARN_REQUESTS:
            plan.warnings.append(
                f"{len(requests)} requests exceeds the {_QUOTA_WARN_REQUESTS} per-call "
                "limit; the client will chunk the batchUpdate automatically."
            )
        return plan

    # ── ID pre-pass ───────────────────────────────────────────────────
    def _walk_allocate(self, node: Component, *, parent_key: str, index: int) -> None:
        path = f"{parent_key}[{index}]:{type(node).__name__}"
        self._ids.allocate(node, parent_key, index, path)
        if isinstance(node, ContainerComponent):
            for i, child in enumerate(node.children):
                self._walk_allocate(child, parent_key=path, index=i)

    # ── per-slide ─────────────────────────────────────────────────────
    def _compile_slide(
        self, slide: Slide, slide_idx: int, out: list[dict[str, Any]]
    ) -> None:
        slide_id = self._ids.get(slide)
        if slide_id is None:
            raise CompileError(f"no id allocated for {slide.tree_path()}")
        out.append(R.create_slide(slide_id, insertion_index=slide_idx, layout=slide.layout))

        # Background: slide override wins, else inherit from the theme so
        # callers only have to set a colour once.
        background = slide.background or self._theme.background
        if background:
            out.append(
                R.update_page_properties(
                    slide_id,
                    properties={
                        "pageBackgroundFill": R.solid_fill(background),
                    },
                    fields="pageBackgroundFill",
                )
            )

        for child in slide.children:
            self._compile_element(child, slide_id=slide_id, out=out)

    # ── dispatch per-element ──────────────────────────────────────────
    def _compile_element(
        self, comp: Component, *, slide_id: str, out: list[dict[str, Any]]
    ) -> None:
        if comp.bounds is None:
            raise CompileError(
                f"component {comp.tree_path()} has no bounds — run LayoutEngine first"
            )

        if isinstance(comp, Shape):
            self._compile_shape(comp, slide_id, out)
        elif isinstance(comp, Text):
            self._compile_text(comp, slide_id, out)
        elif isinstance(comp, Image):
            self._compile_image(comp, slide_id, out)
        elif isinstance(comp, (Row, Col, Grid, Spacer, _FlexContainer, Kpi, KpiGrid)):
            # Pure layout: recurse into children, which inherit bounds.
            if isinstance(comp, ContainerComponent):
                for child in comp.children:
                    self._compile_element(child, slide_id=slide_id, out=out)
        elif isinstance(comp, ContainerComponent):
            for child in comp.children:
                self._compile_element(child, slide_id=slide_id, out=out)

    # ── shapes ────────────────────────────────────────────────────────
    def _compile_shape(self, shape: Shape, slide_id: str, out: list[dict[str, Any]]) -> None:
        object_id = self._id_of(shape)
        shape_type = (
            shape.shape_type.value if isinstance(shape.shape_type, ShapeType) else shape.shape_type
        )
        assert shape.bounds is not None
        out.append(
            R.create_shape(object_id, page_id=slide_id, shape_type=shape_type, bounds=shape.bounds)
        )

        props: dict[str, Any] = {}
        fields: list[str] = []
        fill = shape.fill or self._theme.shape_fill
        if fill:
            props["shapeBackgroundFill"] = R.solid_fill(fill)
            fields.append("shapeBackgroundFill")
        stroke = shape.stroke or self._theme.shape_stroke
        if stroke:
            props["outline"] = {
                "outlineFill": R.solid_fill(stroke),
                **({"weight": {"magnitude": shape.stroke_width or 1, "unit": "PT"}}
                   if shape.stroke_width is not None else {}),
            }
            fields.append("outline")
        if props:
            out.append(
                R.update_shape_properties(object_id, properties=props, fields=",".join(fields))
            )

        # Alt-text metadata so Updater can find this element again.
        out.append(self._metadata_request(shape, object_id))

        # Recurse into any children (typically a single Text or layout).
        for child in shape.children:
            self._compile_element(child, slide_id=slide_id, out=out)

    # ── text ──────────────────────────────────────────────────────────
    def _compile_text(self, text: Text, slide_id: str, out: list[dict[str, Any]]) -> None:
        object_id = self._id_of(text)
        assert text.bounds is not None
        out.append(
            R.create_shape(
                object_id,
                page_id=slide_id,
                shape_type=ShapeType.TEXT_BOX.value,
                bounds=text.bounds,
            )
        )
        if text.content:
            out.append(R.insert_text(object_id, text.content))

        style_def = self._resolved_text_style(text)
        style_body, fields = self._text_style_fields(style_def, text)
        if fields:
            out.append(
                R.update_text_style(object_id, style=style_body, fields=",".join(fields))
            )
        if text.align:
            align_map = {"start": "START", "center": "CENTER", "end": "END", "justify": "JUSTIFIED"}
            out.append(
                R.update_paragraph_style(
                    object_id,
                    style={"alignment": align_map[text.align]},
                    fields="alignment",
                )
            )
        # Note: Google's batchUpdate rejects any non-NONE autofitType
        # ("Autofit types other than NONE are not supported"). The
        # `shrink_on_overflow` kwarg is kept on the component for
        # future compatibility but does not emit a request today.

        out.append(self._metadata_request(text, object_id))

    # ── image ─────────────────────────────────────────────────────────
    def _compile_image(self, image: Image, slide_id: str, out: list[dict[str, Any]]) -> None:
        object_id = self._id_of(image)
        assert image.bounds is not None
        out.append(
            R.create_image(object_id, page_id=slide_id, url=image.url, bounds=image.bounds)
        )
        out.append(self._metadata_request(image, object_id, description=image.alt))

    # ── helpers ───────────────────────────────────────────────────────
    def _id_of(self, comp: Component) -> str:
        oid = self._ids.get(comp)
        if oid is None:
            raise CompileError(f"no id allocated for {comp.tree_path()}")
        return oid

    def _resolved_text_style(self, text: Text) -> TextStyleDef:
        base = self._theme.resolve_text_style(text.style).model_copy()
        if text.color:
            base.color = text.color
        if text.size is not None:
            base.size = int(text.size)
        if text.font:
            base.font = text.font
        if text.bold is not None:
            base.bold = text.bold
        if text.italic is not None:
            base.italic = text.italic
        return base

    @staticmethod
    def _text_style_fields(style: TextStyleDef, text: Text) -> tuple[dict[str, Any], list[str]]:
        body: dict[str, Any] = {
            "fontFamily": style.font,
            "fontSize": {"magnitude": style.size / 12700, "unit": "PT"},
            "foregroundColor": {"opaqueColor": {"rgbColor": R.hex_to_rgb(style.color)}},
            "bold": style.bold,
            "italic": style.italic,
        }
        fields = ["fontFamily", "fontSize", "foregroundColor", "bold", "italic"]
        if text.underline:
            body["underline"] = True
            fields.append("underline")
        if text.bg:
            body["backgroundColor"] = {"opaqueColor": {"rgbColor": R.hex_to_rgb(text.bg)}}
            fields.append("backgroundColor")
        return body, fields

    def _metadata_request(
        self, comp: Component, object_id: str, *, description: str | None = None
    ) -> dict[str, Any]:
        marker = encode_metadata(type(comp).__name__, comp.metadata)
        return R.update_alt_text(object_id, title=marker, description=description)
