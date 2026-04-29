"""Context-manager stack for declarative component assembly.

Every `ContainerComponent.__enter__` pushes itself onto this stack, and
every new component inspects the top of the stack to find its parent.
The stack is held in a `ContextVar` so concurrent threads or async
tasks each see their own tree without interference — the same pattern
Prefab uses in `prefab_ui.components.base`.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from slidebox.components.base import Component
    from slidebox.theme import Theme

_stack: ContextVar[list[Any] | None] = ContextVar("slidebox_stack", default=None)


def current_parent() -> Any:
    """Return the top of the context stack, or None.

    The parent may be a `ContainerComponent` or a `Presentation` — both
    expose a `children` list that the child will append itself to.
    """
    stack = _stack.get()
    if not stack:
        return None
    return stack[-1]


def current_theme() -> Theme | None:
    """Return the theme of the enclosing `Presentation`, if any.

    Composite components (Kpi, user-defined) call this inside `build()`
    so their sub-elements pick up themed colours and fonts without the
    caller passing the theme down manually.
    """
    stack = _stack.get()
    if not stack:
        return None
    from slidebox.presentation import Presentation

    for node in stack:
        if isinstance(node, Presentation):
            return node.theme
    return None


def push(container: Any) -> None:
    stack = _stack.get()
    if stack is None:
        stack = []
        _stack.set(stack)
    stack.append(container)


def pop(container: Any) -> None:
    stack = _stack.get() or []
    if not stack or stack[-1] is not container:
        raise RuntimeError("slidebox context stack corrupted — popped wrong container")
    stack.pop()


@contextmanager
def defer() -> Generator[None, None, None]:
    """Build components without attaching them to the current parent.

    Useful when you want to assemble a subtree and insert it later:

        with Col() as outer:
            with defer():
                card = Shape(); card.enter(); Text("hi"); card.exit()
            insert(card)
    """
    saved = _stack.get()
    _stack.set(None)
    try:
        yield
    finally:
        _stack.set(saved)


def insert(component: Component) -> Component:
    """Attach a detached component to the current parent.

    Raises if called outside any container context, or if the component
    is already a child of a container.
    """
    parent = current_parent()
    if parent is None:
        raise RuntimeError("insert() requires an enclosing container context")
    for existing in parent.children:
        if existing is component:
            raise RuntimeError("component is already a child of this container")
    parent.children.append(component)
    return component
