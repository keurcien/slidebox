"""Drive client used to host image bytes for the Slides API.

The Slides API only embeds images by URL or Drive file ID — there is
no binary upload path on `presentations.batchUpdate`. So when a user
hands `Image` a local path, raw bytes, or a matplotlib Figure, slidebox
uploads the bytes to Drive at `push()` time and rewrites the component
to reference the resulting public URL.

Files are content-addressed: the SHA-256 of the bytes is stored in the
file's `appProperties`. The same image used across decks (or across
patches of the same deck) reuses one Drive file rather than churning
new copies on every push. This keeps the deterministic-id story intact
on the asset side too.

Scope: `drive.file` — slidebox sees and touches only files it created.

Shared Drive support: when `parent_folder_id` is set, every Drive call
includes `supportsAllDrives=True` and the cache-lookup query targets
the resolved Shared Drive (`corpora=drive`, `driveId=<id>`). Without
those flags, service-account uploads land in the SA's non-existent
My Drive and 403 with a storage-quota error.
"""

from __future__ import annotations

import hashlib
from typing import Any

from slidebox.client.retry import retry_with_backoff

_HASH_KEY = "slidebox_sha256"


class DriveClient:
    """Minimal Drive v3 wrapper for slidebox image uploads."""

    def __init__(
        self,
        credentials: Any,
        *,
        parent_folder_id: str | None = None,
        _service: Any | None = None,
    ) -> None:
        self._parent = parent_folder_id
        # Resolved lazily on first cache lookup. `False` means "not yet
        # resolved"; `None` means "resolved, parent is in My Drive";
        # a string means "resolved, parent lives in this Shared Drive".
        self._drive_id: str | None | _Sentinel = _UNRESOLVED
        if _service is not None:
            self._service = _service
            return
        from googleapiclient.discovery import build
        self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def create_presentation_file(self, title: str) -> str:
        """Create an empty Google Slides file via Drive and return its id.

        Use this path on a service-account principal: `slides.presentations.create`
        writes into the caller's My Drive root, which an SA does not own — many
        Workspace policies surface that as a 403. Drive's `files.create` works,
        and additionally lets us land the deck directly in the configured
        parent folder instead of renaming/moving after the fact.
        """
        body: dict[str, Any] = {
            "name": title,
            "mimeType": "application/vnd.google-apps.presentation",
        }
        if self._parent:
            body["parents"] = [self._parent]
        file = retry_with_backoff(
            lambda: self._service.files()
            .create(body=body, fields="id", supportsAllDrives=True)
            .execute()
        )
        return str(file["id"])

    def upload_image(
        self,
        data: bytes,
        *,
        mime: str = "image/png",
        name: str = "slidebox-asset",
    ) -> str:
        """Upload bytes (or reuse an existing file) and return a public URL."""
        digest = hashlib.sha256(data).hexdigest()

        cached = self._find_by_hash(digest)
        if cached is not None:
            return _public_url(cached)

        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(data, mimetype=mime, resumable=False)
        body: dict[str, Any] = {
            "name": f"{name}-{digest[:8]}",
            "mimeType": mime,
            "appProperties": {_HASH_KEY: digest},
        }
        if self._parent:
            body["parents"] = [self._parent]
        file = retry_with_backoff(
            lambda: self._service.files()
            .create(
                body=body,
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
        file_id = str(file["id"])

        # Slides' server-side image fetcher reads the URL anonymously, so the
        # file must be publicly readable. On a Shared Drive this requires the
        # drive's sharing settings to allow "anyone with link" — if Workspace
        # blocks it, this call surfaces the policy error directly.
        retry_with_backoff(
            lambda: self._service.permissions()
            .create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
        return _public_url(file_id)

    def _find_by_hash(self, digest: str) -> str | None:
        q = (
            f"appProperties has {{ key='{_HASH_KEY}' and value='{digest}' }} "
            "and trashed=false"
        )
        list_kwargs: dict[str, Any] = {
            "q": q,
            "fields": "files(id)",
            "pageSize": 1,
            "supportsAllDrives": True,
        }
        drive_id = self._resolve_drive_id()
        if drive_id:
            list_kwargs["corpora"] = "drive"
            list_kwargs["driveId"] = drive_id
            list_kwargs["includeItemsFromAllDrives"] = True
        else:
            list_kwargs["spaces"] = "drive"
        resp = retry_with_backoff(lambda: self._service.files().list(**list_kwargs).execute())
        files = resp.get("files") or []
        if not files:
            return None
        return str(files[0]["id"])

    def _resolve_drive_id(self) -> str | None:
        """Look up the Shared Drive id that owns the configured parent folder.

        Returns None when there is no parent or when the parent lives in
        My Drive. Cached after the first call to avoid an extra round trip
        per uploaded image.
        """
        if self._drive_id is not _UNRESOLVED:
            return self._drive_id  # type: ignore[return-value]
        if self._parent is None:
            self._drive_id = None
            return None
        resp = retry_with_backoff(
            lambda: self._service.files()
            .get(fileId=self._parent, fields="driveId", supportsAllDrives=True)
            .execute()
        )
        self._drive_id = resp.get("driveId")
        return self._drive_id  # type: ignore[return-value]


class _Sentinel:
    """Marker for `DriveClient._drive_id == not-yet-resolved`."""


_UNRESOLVED = _Sentinel()


def _public_url(file_id: str) -> str:
    # lh3 form is the most reliable for the Slides server-side fetcher;
    # the classic `drive.google.com/uc?id=` form sometimes hits virus-scan
    # or auth interstitials for larger assets.
    return f"https://lh3.googleusercontent.com/d/{file_id}"
