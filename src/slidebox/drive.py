"""Output sinks for a rendered deck: local .pptx and Google Slides.

`save()` writes a .pptx to disk. `to_google_slides()` renders in memory,
uploads the bytes to Drive with conversion to native Google Slides, and
returns the file id + URL — no temp file touches disk.

Re-running a deck and passing the stored `file_id` updates the same Drive
file in place, so the share link and URL stay stable across quarters
(the "refresh the numbers" workflow). Auth is Application Default
Credentials by default, with a pluggable CredentialsProvider for OAuth.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pptx.presentation import Presentation as PptxPresentation

from slidebox.render import Fonts, render
from slidebox.schema import Deck
from slidebox.theme import BrandTheme

SCOPES = ["https://www.googleapis.com/auth/drive"]

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
GSLIDES_MIME = "application/vnd.google-apps.presentation"


@runtime_checkable
class CredentialsProvider(Protocol):
    def credentials(self) -> Any:  # google.auth.credentials.Credentials
        ...


class _ADCProvider:
    def credentials(self) -> Any:
        from google.auth import default

        creds, _ = default(scopes=SCOPES)
        return creds


@dataclass(frozen=True)
class GoogleSlides:
    """Result of an upload: the Drive file id and its editor URL."""

    id: str
    url: str


def _as_presentation(
    deck: Deck | PptxPresentation,
    theme: BrandTheme | None,
    fonts: Fonts | None = None,
) -> PptxPresentation:
    if isinstance(deck, Deck):
        return render(deck, theme=theme, fonts=fonts)
    return deck


def _to_buffer(prs: PptxPresentation) -> io.BytesIO:
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


def save(
    deck: Deck | PptxPresentation,
    path: str | Path,
    *,
    theme: BrandTheme | None = None,
    fonts: Fonts | None = None,
) -> Path:
    """Render `deck` (or pass a Presentation) and write a .pptx to `path`.

    Pass `fonts` (family -> file path / variant dict) to size text from real
    font metrics; see `slidebox.render`.
    """
    prs = _as_presentation(deck, theme, fonts)
    out = Path(path)
    prs.save(str(out))
    return out


def to_google_slides(
    deck: Deck | PptxPresentation,
    *,
    name: str | None = None,
    file_id: str | None = None,
    folder_id: str | None = None,
    theme: BrandTheme | None = None,
    fonts: Fonts | None = None,
    creds: CredentialsProvider | None = None,
) -> GoogleSlides:
    """Render in memory, upload to Drive, convert to Google Slides.

    Pass `file_id` to update an existing deck in place (stable URL).
    Otherwise a new file is created, optionally inside `folder_id`.
    Pass `fonts` to size text from real font metrics (see `slidebox.render`).
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload

    prs = _as_presentation(deck, theme, fonts)
    title = name or (deck.title if isinstance(deck, Deck) else "Slidebox deck")

    provider = creds or _ADCProvider()
    drive = build("drive", "v3", credentials=provider.credentials())
    media = MediaIoBaseUpload(_to_buffer(prs), mimetype=PPTX_MIME, resumable=True)

    if file_id:
        file = (
            drive.files()
            .update(fileId=file_id, media_body=media, body={"name": title},
                    fields="id", supportsAllDrives=True)
            .execute()
        )
    else:
        metadata: dict[str, Any] = {"name": title, "mimeType": GSLIDES_MIME}
        if folder_id:
            metadata["parents"] = [folder_id]
        file = (
            drive.files()
            .create(body=metadata, media_body=media, fields="id",
                    supportsAllDrives=True)
            .execute()
        )

    fid: str = file["id"]
    return GoogleSlides(id=fid, url=f"https://docs.google.com/presentation/d/{fid}/edit")


__all__ = [
    "CredentialsProvider",
    "GoogleSlides",
    "save",
    "to_google_slides",
]
