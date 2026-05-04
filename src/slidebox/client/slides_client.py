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
from slidebox.errors import AuthError


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
        try:
            resp = retry_with_backoff(
                lambda: self._service.presentations().create(body=body).execute()
            )
        except Exception as exc:
            if _looks_like_sa_create_403(exc):
                raise AuthError(
                    "Slides' presentations.create() returned 403. This usually "
                    "happens when authenticating as a service account: the call "
                    "tries to write into the caller's My Drive root, which a "
                    "service account does not own. Set Presentation."
                    "drive_folder_id (or the SLIDEBOX_DRIVE_FOLDER_ID env var) "
                    "to a Drive folder the SA can write to — slidebox will then "
                    "create the deck via the Drive API instead."
                ) from exc
            raise
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


def _looks_like_sa_create_403(exc: BaseException) -> bool:
    """Recognise the googleapiclient HttpError raised when an SA hits the
    My-Drive-root restriction on `slides.presentations.create`. We can't
    `isinstance` against HttpError without taking a hard import dep, so we
    sniff the status code on the duck-typed `resp` attribute.
    """
    resp = getattr(exc, "resp", None)
    status = getattr(resp, "status", None)
    try:
        return int(status) == 403
    except (TypeError, ValueError):
        return False
