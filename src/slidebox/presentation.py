"""Presentation — the top-level deck that owns every Slide.

Acts as the root context manager. Build a tree under `with Presentation()`,
then call `.push()` to send it to Google. The same instance can be reused
to push updates (via its Compiler + SlidesClient) without rebuilding.

The Presentation is deliberately NOT a `ContainerComponent` because it
does not attach to anything — it is the root. But it uses the same
ContextVar-based stacking so its children wire up correctly.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny

from slidebox import context
from slidebox.components.slide import Slide
from slidebox.geometry import Bounds
from slidebox.theme import Theme, themes
from slidebox.units import DEFAULT_CANVAS_H_EMU, DEFAULT_CANVAS_W_EMU

if TYPE_CHECKING:

    from slidebox.client.slides_client import SlidesClient


class Presentation(BaseModel):
    """A declarative Google Slides deck."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str = "Untitled"
    theme: Theme = Field(default_factory=themes.default)
    canvas: Bounds = Field(
        default_factory=lambda: Bounds(0, 0, DEFAULT_CANVAS_W_EMU, DEFAULT_CANVAS_H_EMU)
    )
    children: list[SerializeAsAny[Slide]] = Field(default_factory=list)

    presentation_id: str | None = None

    # When set, push() creates the deck via Drive (`files.create` with mimeType
    # `application/vnd.google-apps.presentation`) and lands it in this folder.
    # Required when authenticating as a service account, since Slides' own
    # `presentations.create` writes to the caller's My Drive root and 403s
    # under most Workspace policies for SAs. Falls back to the env var
    # `SLIDEBOX_DRIVE_FOLDER_ID` if not set on the model.
    drive_folder_id: str | None = None

    # Auth — exactly one of these paths is used. `credentials` wins;
    # otherwise resolve_credentials() walks the fallback chain.
    credentials: Any | None = Field(default=None, exclude=True, repr=False)
    service_account_file: str | None = None
    oauth_client_secrets: str | None = None

    def __enter__(self) -> Presentation:
        context.push(self)
        return self

    def __exit__(self, *exc: Any) -> None:
        context.pop(self)

    def push(self, client: SlidesClient | None = None) -> str:
        """Resolve layout, compile to batchUpdate, and dispatch.

        Returns the Google `presentationId`. Creates the presentation
        if `self.presentation_id` is unset; otherwise appends to the
        existing deck.
        """
        from slidebox.client.auth import resolve_credentials
        from slidebox.client.slides_client import SlidesClient
        from slidebox.compile.compiler import Compiler
        from slidebox.layout.engine import LayoutEngine

        folder_id = self.drive_folder_id or os.environ.get("SLIDEBOX_DRIVE_FOLDER_ID")
        needs_drive = bool(folder_id) and self.presentation_id is None

        pending_images = self._collect_pending_images()
        creds: Any | None = None
        if pending_images or needs_drive or client is None:
            creds = resolve_credentials(
                credentials=self.credentials,
                service_account_file=self.service_account_file,
                oauth_client_secrets=self.oauth_client_secrets,
            )

        if pending_images:
            from slidebox.client.drive_client import DriveClient

            drive = DriveClient(creds)
            for img in pending_images:
                url = drive.upload_image(
                    img.pending_bytes,  # type: ignore[arg-type]
                    mime=img.pending_mime,
                    name=img.pending_name,
                )
                img.resolve_pending(url)

        LayoutEngine(self.canvas, self.theme).resolve(self)
        plan = Compiler(self.theme).compile(self)

        if client is None:
            client = SlidesClient(creds)

        if self.presentation_id is None:
            if folder_id:
                from slidebox.client.drive_client import DriveClient

                self.presentation_id = DriveClient(creds).create_presentation_file(
                    self.title, parent_folder_id=folder_id
                )
            else:
                self.presentation_id = client.create_presentation(self.title)

        client.batch_update(self.presentation_id, plan.requests)
        return self.presentation_id

    def _collect_pending_images(self) -> list[Any]:
        from slidebox.components.image import Image

        out: list[Image] = []
        for slide in self.children:
            for node in slide.walk():
                if isinstance(node, Image) and node.pending_bytes is not None:
                    out.append(node)
        return out

    def to_json(self, *, indent: int | None = 2) -> str:
        """Dump the tree as JSON. Useful for debugging and LLM inspection."""
        return self.model_dump_json(indent=indent, exclude_none=True)
