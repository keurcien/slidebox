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
    list_calls: list[dict[str, Any]] = field(default_factory=list)
    permission_calls: list[dict[str, Any]] = field(default_factory=list)
    get_calls: list[dict[str, Any]] = field(default_factory=list)
    # Stub: maps parent folder id → driveId returned by files.get
    drive_id_for_parent: dict[str, str] = field(default_factory=dict)
    # Stub: list of (digest, file_id) hits returned in order
    cached_hashes: dict[str, str] = field(default_factory=dict)
    next_id: int = 0

    def files(self) -> FakeDriveFiles:
        return FakeDriveFiles(self)

    def permissions(self) -> FakeDrivePermissions:
        return FakeDrivePermissions(self)


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
            {
                "id": fid,
                "body": body,
                "supportsAllDrives": supportsAllDrives,
                "has_media": media_body is not None,
            }
        )
        return FakeExec({"id": fid})

    def list(self, **kwargs: Any) -> FakeExec:
        self.service.list_calls.append(kwargs)
        # Crude digest extraction from the q string for cache hits in tests.
        q = kwargs.get("q", "")
        for digest, fid in self.service.cached_hashes.items():
            if digest in q:
                return FakeExec({"files": [{"id": fid}]})
        return FakeExec({"files": []})

    def get(
        self,
        *,
        fileId: str,
        fields: str | None = None,
        supportsAllDrives: bool = False,
    ) -> FakeExec:
        self.service.get_calls.append(
            {"fileId": fileId, "fields": fields, "supportsAllDrives": supportsAllDrives}
        )
        drive_id = self.service.drive_id_for_parent.get(fileId)
        out: dict[str, Any] = {}
        if drive_id is not None:
            out["driveId"] = drive_id
        return FakeExec(out)


@dataclass
class FakeDrivePermissions:
    service: FakeDriveService

    def create(
        self,
        *,
        fileId: str,
        body: dict[str, Any],
        fields: str | None = None,
        supportsAllDrives: bool = False,
    ) -> FakeExec:
        self.service.permission_calls.append(
            {
                "fileId": fileId,
                "body": body,
                "supportsAllDrives": supportsAllDrives,
            }
        )
        return FakeExec({"id": "perm_1"})


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
