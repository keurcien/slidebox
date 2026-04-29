from __future__ import annotations

import pytest

from slidebox import Text
from slidebox.errors import StaleStateError
from slidebox.geometry import Bounds
from slidebox.update.queries import LiveDeck, LiveElement
from slidebox.update.updater import Updater


def _deck_with(element: LiveElement) -> LiveDeck:
    return LiveDeck(
        presentation_id="p1",
        fetched_at=0.0,
        elements={element.object_id: element},
        slide_ids=[element.page_object_id] if element.page_object_id else [],
    )


def test_replace_text_emits_delete_then_insert() -> None:
    u = Updater("p1").replace_text("t1", "new")
    reqs = u.dry_run(live_deck=LiveDeck(presentation_id="p1", fetched_at=0.0))
    kinds = [next(iter(r)) for r in reqs]
    assert kinds == ["deleteText", "insertText"]
    assert reqs[1]["insertText"]["text"] == "new"


def test_update_style_only_sets_requested_fields() -> None:
    u = Updater("p1").update_style("t1", color="#ff0000", bold=True)
    reqs = u.dry_run(live_deck=LiveDeck(presentation_id="p1", fetched_at=0.0))
    assert len(reqs) == 1
    style_req = reqs[0]["updateTextStyle"]
    assert "foregroundColor" in style_req["style"]
    assert style_req["style"]["bold"] is True
    assert "italic" not in style_req["fields"]


def test_remove_and_replace_image() -> None:
    u = Updater("p1").remove("x").replace_image("img", "https://y.png")
    reqs = u.dry_run(live_deck=LiveDeck(presentation_id="p1", fetched_at=0.0))
    assert any("deleteObject" in r for r in reqs)
    assert any("replaceImage" in r for r in reqs)


def test_replace_element_uses_live_bounds_and_reassigns_id() -> None:
    live = _deck_with(
        LiveElement(
            object_id="kpi_1",
            kind="shape",
            bounds=Bounds(100, 200, 500, 400),
            alt_title=None,
            alt_description=None,
            page_object_id="slide_a",
        )
    )
    new_text = Text("replaced")
    u = Updater("p1").replace_element("kpi_1", new_text)
    reqs = u.dry_run(live_deck=live)
    assert reqs[0] == {"deleteObject": {"objectId": "kpi_1"}}

    # The new text must reuse kpi_1 as its objectId so future lookups still work.
    create_reqs = [r for r in reqs if "createShape" in r]
    assert len(create_reqs) == 1
    assert create_reqs[0]["createShape"]["objectId"] == "kpi_1"
    props = create_reqs[0]["createShape"]["elementProperties"]
    assert props["pageObjectId"] == "slide_a"
    assert props["transform"]["translateX"] == 100
    assert props["transform"]["translateY"] == 200


def test_replace_element_on_missing_id_raises_stale_state() -> None:
    live = LiveDeck(presentation_id="p1", fetched_at=0.0)
    u = Updater("p1").replace_element("gone", Text("x"))
    with pytest.raises(StaleStateError):
        u.dry_run(live_deck=live)


def test_fluent_chain_returns_same_updater() -> None:
    u = Updater("p1")
    assert u.replace_text("x", "y") is u
    assert u.update_style("x", bold=True) is u
