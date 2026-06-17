"""Output-sink tests: credential resolution and strict fit enforcement.

These don't touch the network — they exercise the pure helpers and the
`strict=` path of `save` (which raises before any file is written).
"""

from __future__ import annotations

import pytest

from slidebox import BrandTheme, Deck, SlideboxFitError, save
from slidebox.drive import _resolve_credentials

_LORA_INTER = BrandTheme(serif_family="Lora", sans_family="Inter")


class _RawCreds:
    """Looks like a google.auth Credentials: has `token` and `refresh`."""

    def __init__(self) -> None:
        self.token = "abc"

    def refresh(self, request: object) -> None:  # pragma: no cover - not called
        pass


class _Provider:
    def __init__(self, creds: object) -> None:
        self._creds = creds

    def credentials(self) -> object:
        return self._creds


def test_resolve_raw_credentials_used_directly() -> None:
    raw = _RawCreds()
    assert _resolve_credentials(raw) is raw


def test_resolve_provider_calls_credentials() -> None:
    raw = _RawCreds()
    assert _resolve_credentials(_Provider(raw)) is raw


def test_resolve_rejects_garbage() -> None:
    with pytest.raises(TypeError):
        _resolve_credentials(object())


def _overflowing_deck() -> Deck:
    return (
        Deck.new(title="t", object_id="t")
        .slide(bg="white", object_id="s")
        .body(["A very long paragraph that cannot possibly fit a one-cell box "
               "no matter how we slice it, so it must overflow. " * 2],
              size_pt=18, col=1, row=1, span=(2, 1), object_id="too_long")
        .build()
    )


def test_save_strict_raises_on_overflow(tmp_path) -> None:
    out = tmp_path / "deck.pptx"
    with pytest.raises(SlideboxFitError):
        save(_overflowing_deck(), out, theme=_LORA_INTER, check=False, strict=True)
    assert not out.exists()  # strict fails before writing


def test_save_strict_passes_clean_deck(tmp_path) -> None:
    out = tmp_path / "deck.pptx"
    clean = (
        Deck.new(title="t", object_id="t")
        .slide(bg="white", object_id="s")
        .header("A quiet quarter.", size_pt=20, col=1, row=1, span=(10, 2),
                object_id="ok")
        .build()
    )
    save(clean, out, theme=_LORA_INTER, check=False, strict=True)
    assert out.exists()
