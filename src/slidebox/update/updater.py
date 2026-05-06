"""Updater — fluent API for patching a live deck.

Each method returns `self` and appends a request (or a thunk that
resolves once live state is known) to an internal buffer. Calling
`.apply()` re-fetches the live deck to mitigate staleness, resolves
any deferred requests that depend on live bounds, then dispatches the
whole payload as a single batchUpdate.

Why thunks? Structural replacements (`replace_element`) need the exact
current bounds of the target element. Those bounds aren't known at
enqueue time — we defer the creation of the final request until
`apply()` so the user's fluent chain stays declarative.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from slidebox.compile import requests as R
from slidebox.compile.compiler import Compiler
from slidebox.compile.ids import IdAllocator
from slidebox.errors import StaleStateError
from slidebox.theme import themes
from slidebox.update.queries import LiveDeck, fetch_presentation

if TYPE_CHECKING:
    from slidebox.client.slides_client import SlidesClient
    from slidebox.components.base import Component

_DeferredReq = Callable[[LiveDeck], list[dict[str, Any]]]


class Updater:
    """Declarative patcher for a live Google Slides deck."""

    def __init__(
        self,
        presentation_id: str,
        *,
        credentials: Any | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_uri: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        service_account_file: str | None = None,
        oauth_client_secrets: str | None = None,
        client: SlidesClient | None = None,
    ) -> None:
        self.presentation_id = presentation_id
        self._buffer: list[dict[str, Any] | _DeferredReq] = []
        self._client = client
        self._credentials = credentials
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_uri = token_uri
        self._client_id = client_id
        self._client_secret = client_secret
        self._sa_file = service_account_file
        self._oauth_secrets = oauth_client_secrets

    # ── fluent API ────────────────────────────────────────────────────
    def replace_text(self, object_id: str, new_text: str) -> Updater:
        self._buffer.append(R.delete_text(object_id))
        self._buffer.append(R.insert_text(object_id, new_text))
        return self

    def update_style(
        self,
        object_id: str,
        *,
        color: str | None = None,
        bold: bool | None = None,
        italic: bool | None = None,
        size_pt: float | None = None,
    ) -> Updater:
        style: dict[str, Any] = {}
        fields: list[str] = []
        if color is not None:
            style["foregroundColor"] = {"opaqueColor": {"rgbColor": R.hex_to_rgb(color)}}
            fields.append("foregroundColor")
        if bold is not None:
            style["bold"] = bold
            fields.append("bold")
        if italic is not None:
            style["italic"] = italic
            fields.append("italic")
        if size_pt is not None:
            style["fontSize"] = {"magnitude": size_pt, "unit": "PT"}
            fields.append("fontSize")
        if fields:
            self._buffer.append(
                R.update_text_style(object_id, style=style, fields=",".join(fields))
            )
        return self

    def replace_image(self, object_id: str, url: str) -> Updater:
        self._buffer.append(R.replace_image(object_id, url))
        return self

    def remove(self, object_id: str) -> Updater:
        self._buffer.append(R.delete_object(object_id))
        return self

    def replace_element(self, object_id: str, new_component: Component) -> Updater:
        """Replace an element in-place with a fresh component at the same bounds."""

        def _resolve(deck: LiveDeck) -> list[dict[str, Any]]:
            el = deck.element(object_id)
            if el is None:
                raise StaleStateError(
                    f"object {object_id!r} is no longer present in presentation "
                    f"{deck.presentation_id!r}"
                )
            if el.bounds is None:
                raise StaleStateError(
                    f"object {object_id!r} has no resolvable bounds — cannot replace"
                )
            # Give the new component the freed id so later lookups continue to work.
            new_component.id = object_id
            new_component.bounds = el.bounds

            theme = themes.default()
            compiler = Compiler(theme, allocator=IdAllocator())
            out: list[dict[str, Any]] = [R.delete_object(object_id)]
            if el.page_object_id:
                compiler._walk_allocate(
                    new_component, parent_key=f"replace({object_id})", index=0
                )
                compiler._compile_element(
                    new_component, slide_id=el.page_object_id, out=out
                )
            return out

        self._buffer.append(_resolve)
        return self

    # ── execute ───────────────────────────────────────────────────────
    def dry_run(self, live_deck: LiveDeck | None = None) -> list[dict[str, Any]]:
        """Return the resolved request list without dispatching.

        If any deferred requests depend on live state, pass a prepared
        `LiveDeck` (useful for tests); otherwise fetch one.
        """
        if live_deck is None:
            live_deck = fetch_presentation(self._client_or_build(), self.presentation_id)
        out: list[dict[str, Any]] = []
        for entry in self._buffer:
            if callable(entry):
                out.extend(entry(live_deck))
            else:
                out.append(entry)
        return out

    def apply(self) -> list[dict[str, Any]]:
        """Resolve deferred requests, re-fetch live state, and dispatch."""
        client = self._client_or_build()
        live = fetch_presentation(client, self.presentation_id)
        resolved = self.dry_run(live_deck=live)
        client.batch_update(self.presentation_id, resolved)
        self._buffer.clear()
        return resolved

    # ── helpers ───────────────────────────────────────────────────────
    def _client_or_build(self) -> SlidesClient:
        if self._client is not None:
            return self._client
        from slidebox.client.auth import resolve_credentials
        from slidebox.client.slides_client import SlidesClient

        creds = resolve_credentials(
            credentials=self._credentials,
            access_token=self._access_token,
            refresh_token=self._refresh_token,
            token_uri=self._token_uri,
            client_id=self._client_id,
            client_secret=self._client_secret,
            service_account_file=self._sa_file,
            oauth_client_secrets=self._oauth_secrets,
        )
        self._client = SlidesClient(creds)
        return self._client
