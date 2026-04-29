from __future__ import annotations

from slidebox import Col, Kpi, Presentation, Row, Slide, Text, Title


def test_push_creates_presentation_and_sends_batch(fake_service, fake_client) -> None:
    with Presentation(title="Hello") as deck, Slide(id="slide_1"):
        Title("Hello world", id="text_title")

    pid = deck.push(client=fake_client)

    assert pid.startswith("fake_")
    assert deck.presentation_id == pid

    assert len(fake_service.batch_calls) == 1
    body = fake_service.batch_calls[0]
    kinds = [next(iter(r)) for r in body["requests"]]
    assert kinds[0] == "createSlide"
    assert "createShape" in kinds
    assert "insertText" in kinds


def test_push_skips_create_when_presentation_id_set(fake_service, fake_client) -> None:
    with Presentation(title="X", presentation_id="existing") as deck, Slide(id="slide_a"):
        Text("hi", id="text_a")

    deck.push(client=fake_client)
    assert deck.presentation_id == "existing"
    assert fake_service.created_ids == []
    assert fake_service.batch_calls[0]["presentationId"] == "existing"


def test_kpi_dashboard_end_to_end(fake_service, fake_client) -> None:
    with Presentation(title="KPIs") as deck, Slide(id="slide_kpis"), Col(gap=24, padding=48):
        Title("Q1 KPIs", id="text_title")
        with Row(gap=16):
            Kpi("Revenue", "$4.2M", trend="+12%", id="kpi_rev")
            Kpi("Users", "58K", trend="+8%", id="kpi_users")
            Kpi("Retention", "94%", trend="+2%", id="kpi_ret")

    deck.push(client=fake_client)
    body = fake_service.batch_calls[0]
    requests = body["requests"]

    # Assert every user-supplied id appears as an objectId.
    all_ids = set()
    for r in requests:
        for v in r.values():
            if isinstance(v, dict) and "objectId" in v:
                all_ids.add(v["objectId"])
    for user_id in ["slide_kpis", "text_title", "kpi_rev", "kpi_users", "kpi_ret"]:
        assert user_id in all_ids, f"missing {user_id} in emitted requests"
