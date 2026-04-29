from __future__ import annotations

from slidebox import Presentation, Slide, Title, themes
from slidebox.compile.compiler import Compiler
from slidebox.geometry import Bounds
from slidebox.layout.engine import LayoutEngine
from slidebox.units import DEFAULT_CANVAS_H_EMU, DEFAULT_CANVAS_W_EMU


def _build_and_compile(theme, text_color: str | None = None):
    with Presentation(theme=theme) as deck, Slide(id="slide_a"):
        (
            Title("Hi", id="text_title", color=text_color)
            if text_color
            else Title("Hi", id="text_title")
        )
    LayoutEngine(
        Bounds(0, 0, DEFAULT_CANVAS_W_EMU, DEFAULT_CANVAS_H_EMU),
        theme,
    ).resolve(deck)
    return Compiler(theme).compile(deck)


def test_default_and_dark_differ() -> None:
    d = themes.default()
    k = themes.dark()
    assert d.background != k.background
    assert d.text_primary != k.text_primary


def test_theme_presets_return_fresh_instances() -> None:
    a = themes.default()
    b = themes.default()
    assert a is not b
    a.background = "#changed"
    assert b.background != "#changed"


def test_h1_style_is_large_and_bold() -> None:
    t = themes.default().resolve_text_style("h1")
    assert t.bold is True
    assert t.size > themes.default().resolve_text_style("body").size


def test_component_override_wins_over_theme() -> None:
    plan = _build_and_compile(themes.dark(), text_color="#ff0000")
    style_reqs = [r for r in plan.requests if "updateTextStyle" in r]
    # fore red colour appears in the style request
    red = None
    for r in style_reqs:
        fg = r["updateTextStyle"]["style"]["foregroundColor"]["opaqueColor"]["rgbColor"]
        if fg.get("red", 0) > 0.99 and fg.get("green", 0) == 0.0:
            red = fg
            break
    assert red is not None, "component color override was ignored"


def test_theme_colour_applies_when_no_override() -> None:
    plan = _build_and_compile(themes.dark())
    style_reqs = [r for r in plan.requests if "updateTextStyle" in r]
    assert style_reqs, "no text style request emitted"
    # Should be dark theme primary — light on dark, so green ~ 0.96
    any_light = any(
        r["updateTextStyle"]["style"]["foregroundColor"]["opaqueColor"]["rgbColor"]["red"] > 0.9
        for r in style_reqs
    )
    assert any_light


def test_merge_produces_new_theme() -> None:
    t = themes.default().merge(accent="#ff0000")
    assert t.accent == "#ff0000"
    assert themes.default().accent != "#ff0000"
