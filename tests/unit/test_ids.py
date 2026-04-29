from __future__ import annotations

import pytest

from slidebox import Presentation, Slide, Text
from slidebox.compile.ids import IdAllocator
from slidebox.errors import CompileError


def test_user_id_wins() -> None:
    t = Text("hi", id="my_text")
    alloc = IdAllocator()
    assert alloc.allocate(t, "root", 0, "root[0]") == "my_text"


def test_derived_id_is_deterministic() -> None:
    t1 = Text("a")
    t2 = Text("a")
    a1 = IdAllocator()
    a2 = IdAllocator()
    assert a1.allocate(t1, "root", 0, "root[0]") == a2.allocate(t2, "root", 0, "root[0]")


def test_collision_raises_with_paths() -> None:
    t1 = Text("a", id="shared")
    t2 = Text("b", id="shared")
    alloc = IdAllocator()
    alloc.allocate(t1, "root", 0, "a-path")
    with pytest.raises(CompileError) as exc:
        alloc.allocate(t2, "root", 1, "b-path")
    assert "a-path" in str(exc.value) and "b-path" in str(exc.value)


def test_invalid_id_format_raises() -> None:
    alloc = IdAllocator()
    # "1abc" starts with a digit → validator in Component raises earlier.
    # Here we simulate a pre-built component that somehow got through.
    t = Text("hi")
    object.__setattr__(t, "id", "$$invalid")
    with pytest.raises(CompileError):
        alloc.allocate(t, "root", 0, "root[0]")


def test_id_map_roundtrip_via_presentation() -> None:
    """A tree built twice yields identical allocations."""
    def build() -> Presentation:
        with Presentation() as deck, Slide(id="slide_a"):
            Text("a", id="text_1")
            Text("b")  # derived
        return deck

    d1, d2 = build(), build()

    a1 = IdAllocator()
    a2 = IdAllocator()
    for i, slide in enumerate(d1.children):
        a1.allocate(slide, "root", i, f"s[{i}]")
        for j, c in enumerate(slide.children):
            a1.allocate(c, f"s[{i}]", j, f"s[{i}]/c[{j}]")
    for i, slide in enumerate(d2.children):
        a2.allocate(slide, "root", i, f"s[{i}]")
        for j, c in enumerate(slide.children):
            a2.allocate(c, f"s[{i}]", j, f"s[{i}]/c[{j}]")

    assert sorted(a1.id_map.values()) == sorted(a2.id_map.values())
