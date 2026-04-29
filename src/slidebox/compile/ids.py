"""Deterministic object ID allocation.

User-supplied `id` on a component always wins. When absent, the
allocator derives `{kind}_{parent_hash}_{index}` — stable across runs
given a stable tree structure. Google's object-id limits apply:
5–50 characters, alphanumeric + hyphen + underscore, case-sensitive.

Uniqueness is enforced across the whole presentation; a collision
raises `CompileError` with the offending paths for debugging.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from slidebox.components.base import Component
from slidebox.errors import CompileError

_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_\-]{4,49}$")


def _short_hash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def _derive_id(kind: str, parent_key: str, index: int) -> str:
    suffix = _short_hash(f"{parent_key}/{index}")
    base = f"{kind}_{suffix}"
    # Google caps at 50 chars. `kind` is short, `suffix` is 8 — safe.
    return base[:50]


@dataclass
class IdAllocator:
    """Assigns each component a stable Google `objectId`.

    Use `.allocate(component, parent_key, index)` during the compile
    walk — returns the allocated id and records it in `.id_map` keyed
    by the object's Python `id()`.
    """

    id_map: dict[int, str] = field(default_factory=dict)
    _used: set[str] = field(default_factory=set)
    _first_seen: dict[str, str] = field(default_factory=dict)  # id -> path

    def allocate(self, component: Component, parent_key: str, index: int, path: str) -> str:
        if (existing := self.id_map.get(id(component))) is not None:
            return existing

        if component.id:
            if not _ID_RE.match(component.id):
                raise CompileError(
                    f"id {component.id!r} at {path} doesn't match Google's "
                    "object-id format (letters/digits/_/-, 5-50 chars, leading letter)"
                )
            candidate = component.id
        else:
            kind = getattr(type(component), "kind", "node")
            candidate = _derive_id(kind, parent_key, index)

        if candidate in self._used:
            first = self._first_seen.get(candidate, "<unknown>")
            raise CompileError(
                f"duplicate object id {candidate!r}: first at {first}, again at {path}"
            )

        self._used.add(candidate)
        self._first_seen[candidate] = path
        self.id_map[id(component)] = candidate
        return candidate

    def get(self, component: Component) -> str | None:
        return self.id_map.get(id(component))
