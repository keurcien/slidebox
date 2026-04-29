"""Updater — fluent API for patching a live Google Slides deck."""

from __future__ import annotations

from slidebox.update.queries import LiveDeck, fetch_presentation
from slidebox.update.updater import Updater

__all__ = ["LiveDeck", "Updater", "fetch_presentation"]
