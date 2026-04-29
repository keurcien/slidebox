"""Image component.

Source can be:

* A URL string (`"https://..."`) — passed through to Slides as-is.
* A local file path (str or `pathlib.Path`) — bytes are read at
  construction time and uploaded to Drive on `push()`.
* A `matplotlib.figure.Figure` — rendered to PNG bytes (via savefig)
  and uploaded.
* Raw `bytes` — uploaded as-is. Pass `mime="image/jpeg"` etc. if not
  PNG.

Non-URL sources stay "pending" on the component until `Presentation.push`
walks the tree, uploads each one through `DriveClient`, and rewrites
`url` to the resulting public link. The Drive upload is content-
addressed, so the same image across decks/patches reuses one file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from pydantic import PrivateAttr

from slidebox.components.base import LeafComponent

_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


class Image(LeafComponent):
    """Picture element. See module docstring for accepted source types."""

    kind: ClassVar[str] = "image"

    url: str = ""
    alt: str | None = None

    _pending_bytes: bytes | None = PrivateAttr(default=None)
    _pending_mime: str = PrivateAttr(default="image/png")
    _pending_name: str = PrivateAttr(default="slidebox-asset")

    def __init__(self, source: Any = "", /, **kwargs: Any) -> None:
        mime_override = kwargs.pop("mime", None)
        name_override = kwargs.pop("name", None)

        url = ""
        pending: tuple[bytes, str, str] | None = None

        if _is_figure(source):
            pending = (
                _figure_to_png(source),
                "image/png",
                name_override or "figure",
            )
        elif isinstance(source, (bytes, bytearray)):
            pending = (
                bytes(source),
                mime_override or "image/png",
                name_override or "bytes",
            )
        elif isinstance(source, Path) or (
            isinstance(source, str) and source and "://" not in source
        ):
            path = Path(source)
            pending = (
                path.read_bytes(),
                mime_override or _MIME_BY_SUFFIX.get(path.suffix.lower(), "image/png"),
                name_override or path.stem,
            )
        elif isinstance(source, str):
            url = source

        super().__init__(url=url, **kwargs)

        if pending is not None:
            self._pending_bytes, self._pending_mime, self._pending_name = pending

    @property
    def pending_bytes(self) -> bytes | None:
        return self._pending_bytes

    @property
    def pending_mime(self) -> str:
        return self._pending_mime

    @property
    def pending_name(self) -> str:
        return self._pending_name

    def resolve_pending(self, url: str) -> None:
        self.url = url
        self._pending_bytes = None


def _is_figure(obj: Any) -> bool:
    cls = type(obj)
    mod = getattr(cls, "__module__", "") or ""
    return mod.startswith("matplotlib.") and cls.__name__ == "Figure"


def _figure_to_png(fig: Any) -> bytes:
    import io

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    return buf.getvalue()
