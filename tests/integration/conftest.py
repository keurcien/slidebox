"""Integration-test fixtures — mocked Google Slides service.

The mock records every batchUpdate body so tests can assert exactly what
slidebox sent. A real network round-trip happens only in e2e tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from slidebox.client.drive_client import DriveClient
from slidebox.client.slides_client import SlidesClient


@dataclass
class FakeDriveService:
    created_files: list[dict[str, Any]] = field(default_factory=list)
    next_id: int = 0

    def files(self) -> FakeDriveFiles:
        return FakeDriveFiles(self)


@dataclass
class FakeDriveFiles:
    service: FakeDriveService

    def create(
        self,
        *,
        body: dict[str, Any],
        fields: str | None = None,
        supportsAllDrives: bool = False,
        media_body: Any = None,
    ) -> FakeExec:
        fid = f"drive_{self.service.next_id}"
        self.service.next_id += 1
        self.service.created_files.append(
            {"id": fid, "body": body, "supportsAllDrives": supportsAllDrives}
        )
        return FakeExec({"id": fid})


@dataclass
class FakeService:
    created_ids: list[str] = field(default_factory=list)
    batch_calls: list[dict[str, Any]] = field(default_factory=list)
    get_responses: list[dict[str, Any]] = field(default_factory=list)

    def presentations(self) -> FakePresentations:
        return FakePresentations(self)


@dataclass
class FakePresentations:
    service: FakeService

    def create(self, body: dict[str, Any]) -> FakeExec:
        pid = f"fake_{len(self.service.created_ids)}"
        self.service.created_ids.append(pid)
        return FakeExec({"presentationId": pid, "title": body.get("title", "")})

    def batchUpdate(self, *, presentationId: str, body: dict[str, Any]) -> FakeExec:
        self.service.batch_calls.append({"presentationId": presentationId, **body})
        return FakeExec({"presentationId": presentationId, "replies": []})

    def get(self, *, presentationId: str) -> FakeExec:
        if self.service.get_responses:
            return FakeExec(self.service.get_responses.pop(0))
        return FakeExec({"presentationId": presentationId, "slides": []})


@dataclass
class FakeExec:
    value: dict[str, Any]

    def execute(self) -> dict[str, Any]:
        return self.value


@pytest.fixture
def fake_service() -> FakeService:
    return FakeService()


@pytest.fixture
def fake_client(fake_service: FakeService) -> SlidesClient:
    return SlidesClient(credentials=None, _service=fake_service)


@pytest.fixture
def fake_drive_service() -> FakeDriveService:
    return FakeDriveService()


@pytest.fixture
def fake_drive_client(fake_drive_service: FakeDriveService) -> DriveClient:
    return DriveClient(credentials=None, _service=fake_drive_service)
