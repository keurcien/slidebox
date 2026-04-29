"""Google Slides API client — the only place in slidebox that does IO."""

from __future__ import annotations

from slidebox.client.auth import DEFAULT_SCOPES, resolve_credentials
from slidebox.client.batching import chunk_requests
from slidebox.client.retry import retry_with_backoff
from slidebox.client.slides_client import SlidesClient

__all__ = [
    "DEFAULT_SCOPES",
    "SlidesClient",
    "chunk_requests",
    "resolve_credentials",
    "retry_with_backoff",
]
