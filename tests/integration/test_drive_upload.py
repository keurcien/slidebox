"""Tests for the Shared Drive plumbing in DriveClient.

The SA-on-Shared-Drive scenario needs three independent flags:
  - files.create with `supportsAllDrives=True` and a `parents` entry
  - permissions.create with `supportsAllDrives=True`
  - files.list with `corpora=drive`, `driveId=<id>`, `includeItemsFromAllDrives=True`

Without any of these, uploads either land in the SA's My Drive (quota 403)
or the cache lookup misses the Shared Drive entirely.
"""

from __future__ import annotations

import hashlib

from slidebox.client.drive_client import DriveClient


def test_upload_image_passes_shared_drive_flags(fake_drive_service) -> None:
    fake_drive_service.drive_id_for_parent["folder_abc"] = "shared_drive_xyz"
    client = DriveClient(
        credentials=None,
        parent_folder_id="folder_abc",
        _service=fake_drive_service,
    )

    url = client.upload_image(b"hello", mime="image/png", name="img")

    # files.create
    assert len(fake_drive_service.created_files) == 1
    created = fake_drive_service.created_files[0]
    assert created["supportsAllDrives"] is True
    assert created["body"]["parents"] == ["folder_abc"]
    assert created["has_media"] is True

    # permissions.create
    assert len(fake_drive_service.permission_calls) == 1
    perm = fake_drive_service.permission_calls[0]
    assert perm["supportsAllDrives"] is True
    assert perm["body"] == {"type": "anyone", "role": "reader"}

    # cache lookup before the create
    assert len(fake_drive_service.list_calls) == 1
    listed = fake_drive_service.list_calls[0]
    assert listed["supportsAllDrives"] is True
    assert listed["corpora"] == "drive"
    assert listed["driveId"] == "shared_drive_xyz"
    assert listed["includeItemsFromAllDrives"] is True
    assert "spaces" not in listed

    # public URL the Slides server-side fetcher can resolve
    assert url.startswith("https://lh3.googleusercontent.com/d/")


def test_upload_image_my_drive_path_unchanged(fake_drive_service) -> None:
    """Without parent_folder_id, behavior matches the pre-Shared-Drive path."""
    client = DriveClient(credentials=None, _service=fake_drive_service)

    client.upload_image(b"hello", mime="image/png", name="img")

    created = fake_drive_service.created_files[0]
    assert "parents" not in created["body"]
    listed = fake_drive_service.list_calls[0]
    assert listed["spaces"] == "drive"
    assert "corpora" not in listed
    assert "driveId" not in listed
    # No driveId resolution call when parent is unset.
    assert fake_drive_service.get_calls == []


def test_upload_image_reuses_cached_file_via_hash(fake_drive_service) -> None:
    """Content-addressed dedup: same bytes → existing file id, no new upload."""
    data = b"already-uploaded"
    digest = hashlib.sha256(data).hexdigest()
    fake_drive_service.cached_hashes[digest] = "existing_file_id"

    client = DriveClient(
        credentials=None,
        parent_folder_id="folder_abc",
        _service=fake_drive_service,
    )

    url = client.upload_image(data)

    assert url == "https://lh3.googleusercontent.com/d/existing_file_id"
    assert fake_drive_service.created_files == []
    assert fake_drive_service.permission_calls == []


def test_drive_id_resolved_once_then_cached(fake_drive_service) -> None:
    fake_drive_service.drive_id_for_parent["folder_abc"] = "shared_drive_xyz"
    client = DriveClient(
        credentials=None,
        parent_folder_id="folder_abc",
        _service=fake_drive_service,
    )

    client.upload_image(b"a")
    client.upload_image(b"b")

    # Two list calls (one per upload), but only one files.get to resolve the drive id.
    assert len(fake_drive_service.list_calls) == 2
    assert len(fake_drive_service.get_calls) == 1
    assert fake_drive_service.get_calls[0]["fileId"] == "folder_abc"
    assert fake_drive_service.get_calls[0]["supportsAllDrives"] is True


def test_create_presentation_file_uses_init_parent(fake_drive_service) -> None:
    client = DriveClient(
        credentials=None,
        parent_folder_id="folder_abc",
        _service=fake_drive_service,
    )

    fid = client.create_presentation_file("Quarterly review")

    created = fake_drive_service.created_files[0]
    assert created["body"]["mimeType"] == "application/vnd.google-apps.presentation"
    assert created["body"]["parents"] == ["folder_abc"]
    assert created["body"]["name"] == "Quarterly review"
    assert created["supportsAllDrives"] is True
    assert fid == created["id"]
