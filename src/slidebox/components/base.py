"""Base classes for every slidebox component.

All components are Pydantic models — we get type coercion, validation,
and serialisation for free. The tree is assembled through context
managers: `ContainerComponent.__enter__` pushes itself onto the
`ContextVar` stack and `LeafComponent.__init__` auto-appends to
whatever is on top.

This mirrors Prefab's approach (see `prefab_ui.components.base`) and
lets callers write:

    with Slide():
        with Row():
            Text("hello")          # auto-attaches to Row, not Slide

The `raw` field on every component is a universal escape hatch: its
dict is shallow-merged into the generated API request just before
dispatch, so power users can override anything the library doesn't yet
expose as a typed kwarg.
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, field_validator

from slidebox import context
from slidebox.errors import ValidationError
from slidebox.geometry import Bounds
from slidebox.units import Length

_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]{4,49}$")


class Component(BaseModel):
    """Base class for everything that lives in the component tree.

    Every component can opt into explicit sizing via `width` / `height`
    (makes it a fixed-size child along that axis) and / or a `flex`
    weight (for proportional sizing). Unspecified means `flex=1` — the
    component takes an equal share of remaining space.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,  # allow Field(alias=...) to accept either name
        validate_assignment=False,
    )

    kind: ClassVar[str] = "component"

    id: str | None = None
    metadata: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None

    # Layout sizing — optional on every component.
    width: Length | None = None
    height: Length | None = None
    flex: int | None = None

    # Populated by the layout engine. Not part of the authoring surface
    # but kept on the model so downstream stages can reach it.
    bounds: Bounds | None = Field(default=None, exclude=True)

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not _ID_RE.match(v):
            raise ValidationError(
                f"Invalid id {v!r}: must be 5-50 characters, start with a letter, "
                "and contain only letters, digits, hyphens, or underscores "
                "(Google Slides object-id constraint)"
            )
        return v

    def tree_path(self) -> str:
        """Best-effort human path for error messages.

        The tree doesn't store parent pointers (we keep components as
        plain children lists), so this returns just the component
        itself. The compiler enriches errors with the full path when it
        walks the tree.
        """
        label = f"{type(self).__name__}"
        if self.id:
            label += f"(id={self.id!r})"
        return label


class LeafComponent(Component):
    """A component with no children. Auto-attaches to the current parent."""

    def model_post_init(self, __context: Any) -> None:
        parent = context.current_parent()
        if parent is not None:
            parent.children.append(self)


class ContainerComponent(Component):
    """A component with children. Works as a context manager.

    Children are serialised with their runtime type (via `SerializeAsAny`)
    rather than being down-cast to `Component`, so subtype-only fields
    like `Text.content` survive the JSON round trip.
    """

    children: list[SerializeAsAny[Component]] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        parent = context.current_parent()
        if parent is not None:
            parent.children.append(self)
        # Subclasses can define a build() hook that populates children
        # declaratively (without using a `with` block).
        build = getattr(self, "build", None)
        if callable(build):
            with self:
                build()

    def __enter__(self) -> ContainerComponent:
        context.push(self)
        return self

    def __exit__(self, *exc: Any) -> None:
        context.pop(self)

    def walk(self) -> Any:
        """Yield this node and every descendant in pre-order."""
        yield self
        for child in self.children:
            if isinstance(child, ContainerComponent):
                yield from child.walk()
            else:
                yield child
