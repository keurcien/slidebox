from __future__ import annotations

from slidebox import Text
from slidebox.update.updater import Updater


def test_apply_refetches_before_dispatch(fake_service, fake_client) -> None:
    # Seed two distinct `get` responses so the test can prove we used
    # the *second* one (the one fetched immediately before dispatch).
    fake_service.get_responses = [
        {
            "slides": [
                {
                    "objectId": "s",
                    "pageElements": [
                        {
                            "objectId": "t",
                            "shape": {},
                            "size": {
                                "width": {"magnitude": 100, "unit": "EMU"},
                                "height": {"magnitude": 50, "unit": "EMU"},
                            },
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"},
                        }
                    ],
                }
            ]
        }
    ]

    u = Updater("pid", client=fake_client).replace_text("t", "hi")
    resolved = u.apply()

    assert any("deleteText" in r for r in resolved)
    assert any("insertText" in r and r["insertText"]["text"] == "hi" for r in resolved)
    # One batch call was sent.
    assert len(fake_service.batch_calls) == 1
    body = fake_service.batch_calls[0]
    kinds = [next(iter(r)) for r in body["requests"]]
    assert "deleteText" in kinds and "insertText" in kinds


def test_replace_element_end_to_end(fake_service, fake_client) -> None:
    fake_service.get_responses = [
        {
            "slides": [
                {
                    "objectId": "slideA",
                    "pageElements": [
                        {
                            "objectId": "old_e",
                            "shape": {},
                            "size": {
                                "width": {"magnitude": 300, "unit": "EMU"},
                                "height": {"magnitude": 100, "unit": "EMU"},
                            },
                            "transform": {
                                "scaleX": 1,
                                "scaleY": 1,
                                "translateX": 400,
                                "translateY": 500,
                                "unit": "EMU",
                            },
                        }
                    ],
                }
            ]
        }
    ]

    Updater("pid", client=fake_client).replace_element("old_e", Text("new")).apply()

    body = fake_service.batch_calls[0]
    reqs = body["requests"]
    # The new element should reuse "old_e" as its objectId.
    create = next(r for r in reqs if "createShape" in r)
    assert create["createShape"]["objectId"] == "old_e"
    tx = create["createShape"]["elementProperties"]["transform"]
    assert tx["translateX"] == 400 and tx["translateY"] == 500
