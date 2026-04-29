"""Structural diff engine — scheduled for v0.2.

v0.1 Updater is imperative (user describes each patch). v0.2 will
support `diff(old_tree, new_tree) -> list[UpdateOp]` for declarative
patching, where the user re-runs their presentation script and slidebox
computes the minimal set of batchUpdate requests to bring the live deck
into sync.

The module is intentionally a stub — kept so downstream code can
import it without conditional guards.
"""

from __future__ import annotations


def diff(*_args: object, **_kwargs: object) -> list[object]:
    raise NotImplementedError("diff() ships in slidebox v0.2; v0.1 is imperative-only")
