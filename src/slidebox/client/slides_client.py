"""Thin wrapper around googleapiclient's Slides service.

The wrapper owns three responsibilities and nothing else:
  1. Build the discovery client with auth.
  2. Apply retry + batching when sending a batchUpdate.
  3. Translate Google's dict replies into slidebox-friendly shapes.

Everything else (compile, layout, ids) is pure business logic that
lives upstream.
"""

from __future__ import annotations

from typing import Any

from slidebox.client.batching import chunk_requests
from slidebox.client.retry import retry_with_backoff


class SlidesClient:
    """Google Slides API facade used by `Presentation.push` and `Updater.apply`."""

    def __init__(self, credentials: Any, *, _service: Any | None = None) -> None:
        if _service is not None:
            # Tests inject a pre-built mock.
            self._service = _service
            return
        from googleapiclient.discovery import build  # local import keeps unit tests light
        self._service = build("slides", "v1", credentials=credentials, cache_discovery=False)

    # ── presentations ────────────────────────────────────────────────
    def create_presentation(self, title: str) -> str:
        body = {"title": title}
        resp = retry_with_backoff(
            lambda: self._service.presentations().create(body=body).execute()
        )
        return str(resp["presentationId"])

    def get_presentation(self, presentation_id: str) -> dict[str, Any]:
        return retry_with_backoff(
            lambda: self._service.presentations().get(presentationId=presentation_id).execute()
        )

    def batch_update(
        self, presentation_id: str, requests: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Send requests to Google, chunked as needed. Returns concatenated replies."""
        if not requests:
            return []
        replies: list[dict[str, Any]] = []
        for chunk in chunk_requests(requests):
            def call(c: list[dict[str, Any]] = chunk) -> dict[str, Any]:
                return self._service.presentations().batchUpdate(  # type: ignore[no-any-return]
                    presentationId=presentation_id, body={"requests": c}
                ).execute()
            resp = retry_with_backoff(call)
            replies.extend(resp.get("replies") or [])
        return replies
