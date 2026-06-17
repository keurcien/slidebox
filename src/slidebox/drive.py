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


def _resolve_credentials(creds: Any) -> Any:
    """Turn whatever the caller passed for `creds` into a Credentials object.

    Accepts, in order:
    - ``None`` — use Application Default Credentials.
    - a raw ``google.auth.credentials.Credentials`` (what ``google.auth.default()``
      returns) — used directly. Detected structurally (it exposes ``token`` and
      ``refresh``), so no wrapper class is needed.
    - a :class:`CredentialsProvider` — its ``.credentials()`` is called.
    """
    if creds is None:
        return _ADCProvider().credentials()
    # A google.auth Credentials object: has a `token` attribute and a
    # `refresh` method. Use it directly so callers can pass the result of
    # `google.auth.default()` without a wrapper.
    if hasattr(creds, "token") and callable(getattr(creds, "refresh", None)):
        return creds
    if hasattr(creds, "credentials") and callable(creds.credentials):
        return creds.credentials()
    raise TypeError(
        "creds must be a google.auth Credentials, a CredentialsProvider, or None"
    )


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


def _check_fit(
    prs: PptxPresentation, fonts: Fonts | None, *, check: bool, strict: bool
) -> None:
    """Report (and optionally enforce) text fit for an already-rendered deck.

    With `check`, prints the report to stderr. With `strict`, raises
    :class:`slidebox.fit.SlideboxFitError` if any box overflows. `strict`
    implies a check is run even if `check` is False.
    """
    import sys

    if not check and not strict:
        return
    from slidebox.fit import format_fit, overflows

    issues = overflows(prs, fonts)
    if check:
        print(format_fit(issues), file=sys.stderr)
    if strict:
        issues.raise_if_overflow()


def save(
    deck: Deck | PptxPresentation,
    path: str | Path,
    *,
    theme: BrandTheme | None = None,
    fonts: Fonts | None = None,
    check: bool = True,
    strict: bool = False,
) -> Path:
    """Render `deck` (or pass a Presentation) and write a .pptx to `path`.

    Pass `fonts` (family -> file path / variant dict) to size text from real
    font metrics; see `slidebox.render`. With `check=True` (default) a fit
    report is printed to stderr so overflowing text boxes are visible at
    compile time; pass `check=False` to silence it. With `strict=True` a
    :class:`slidebox.fit.SlideboxFitError` is raised (before writing) if any
    text box overflows — useful in CI to fail on a broken deck.
    """
    prs = _as_presentation(deck, theme, fonts)
    _check_fit(prs, fonts, check=check, strict=strict)
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
    creds: Any | None = None,
    check: bool = True,
    strict: bool = False,
) -> GoogleSlides:
    """Render in memory, upload to Drive, convert to Google Slides.

    Pass `file_id` to update an existing deck in place (stable URL).
    Otherwise a new file is created, optionally inside `folder_id`.

    `folder_id` may be a folder in a **Shared Drive** (or a Shared Drive's
    id). This is required for service accounts: a service account has no
    My Drive storage quota, so creating at the drive root fails with
    "Service Accounts do not have storage quota". Targeting a Shared Drive
    folder makes the Shared Drive own the file, which works. Shared-Drive
    calls are already enabled (`supportsAllDrives=True`).

    Pass `fonts` to size text from real font metrics (see `slidebox.render`).

    `creds` accepts a raw ``google.auth.credentials.Credentials`` (e.g. the
    object returned by ``google.auth.default()``), a :class:`CredentialsProvider`,
    or ``None`` for Application Default Credentials — no wrapper class needed.

    With `strict=True` a :class:`slidebox.fit.SlideboxFitError` is raised
    (before uploading) if any text box overflows.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload

    prs = _as_presentation(deck, theme, fonts)
    _check_fit(prs, fonts, check=check, strict=strict)
    title = name or (deck.title if isinstance(deck, Deck) else "Slidebox deck")

    drive = build("drive", "v3", credentials=_resolve_credentials(creds))
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
