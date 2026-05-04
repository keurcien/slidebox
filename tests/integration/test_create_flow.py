from __future__ import annotations

import pytest

from slidebox import Col, Kpi, Presentation, Row, Slide, Text, Title
from slidebox.errors import AuthError


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


def test_push_uses_drive_create_when_folder_id_set(
    fake_service, fake_client, fake_drive_service, monkeypatch
) -> None:
    """drive_folder_id routes creation through Drive.files.create instead of
    Slides.presentations.create — the path SAs need under most Workspace policies."""
    from slidebox.client import drive_client as drive_module
    from slidebox.client.drive_client import DriveClient

    monkeypatch.setattr(
        drive_module,
        "DriveClient",
        lambda creds, **kw: DriveClient(creds, _service=fake_drive_service, **kw),
    )

    with Presentation(
        title="SA Deck",
        drive_folder_id="folder_abc",
        credentials=object(),
    ) as deck, Slide(id="slide_1"):
        Title("Hello", id="text_title")

    pid = deck.push(client=fake_client)

    # Slides.presentations.create was NOT called.
    assert fake_service.created_ids == []
    # Drive.files.create WAS called, with the right mimeType + parent.
    assert len(fake_drive_service.created_files) == 1
    created = fake_drive_service.created_files[0]
    assert created["body"]["mimeType"] == "application/vnd.google-apps.presentation"
    assert created["body"]["parents"] == ["folder_abc"]
    assert created["body"]["name"] == "SA Deck"
    assert created["supportsAllDrives"] is True
    # Returned id flows through and is used for the subsequent batchUpdate.
    assert pid == created["id"]
    assert fake_service.batch_calls[0]["presentationId"] == pid


def test_push_picks_up_drive_folder_env_var(
    fake_service, fake_client, fake_drive_service, monkeypatch
) -> None:
    from slidebox.client import drive_client as drive_module
    from slidebox.client.drive_client import DriveClient

    monkeypatch.setattr(
        drive_module,
        "DriveClient",
        lambda creds, **kw: DriveClient(creds, _service=fake_drive_service, **kw),
    )
    monkeypatch.setenv("SLIDEBOX_DRIVE_FOLDER_ID", "folder_from_env")

    with Presentation(title="Env Deck", credentials=object()) as deck, Slide(
        id="slide_1"
    ):
        Title("Hi", id="text_title")

    deck.push(client=fake_client)

    assert fake_service.created_ids == []
    assert fake_drive_service.created_files[0]["body"]["parents"] == ["folder_from_env"]


def test_create_presentation_403_raises_auth_error_with_hint(fake_service) -> None:
    """SA users see an actionable message instead of an opaque HttpError."""
    from slidebox.client.slides_client import SlidesClient

    class _FakeResp:
        status = 403

    class _Fake403(Exception):
        def __init__(self) -> None:
            super().__init__("forbidden")
            self.resp = _FakeResp()

    class _Boom:
        def execute(self) -> dict:
            raise _Fake403()

    class _Pres:
        def create(self, body):  # noqa: ARG002
            return _Boom()

    class _Svc:
        def presentations(self):
            return _Pres()

    client = SlidesClient(credentials=None, _service=_Svc())
    with pytest.raises(AuthError, match="drive_folder_id"):
        client.create_presentation("X")
