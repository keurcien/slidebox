"""Chunk a list of batchUpdate requests into calls Google will accept.

Google caps a single `presentations.batchUpdate` at 2000 requests. We
split on safe boundaries so that a create + insertText + style trio for
the same objectId never lands in different chunks — splitting them
would break the ordering invariants the compiler worked to preserve.

A request is "safe to start a new chunk at" if it does not reference an
objectId that was created earlier in the current chunk.
"""

from __future__ import annotations

from typing import Any

MAX_PER_CHUNK = 2000

_CREATE_KINDS = frozenset({"createSlide", "createShape", "createImage", "createLine", "createTable"})


def chunk_requests(
    requests: list[dict[str, Any]],
    max_per_chunk: int = MAX_PER_CHUNK,
) -> list[list[dict[str, Any]]]:
    if len(requests) <= max_per_chunk:
        return [requests]

    chunks: list[list[dict[str, Any]]] = []
    start = 0
    n = len(requests)

    while start < n:
        end = min(start + max_per_chunk, n)
        if end < n:
            end = _safe_split_point(requests, start, end)
        chunks.append(requests[start:end])
        start = end
    return chunks


def _safe_split_point(requests: list[dict[str, Any]], start: int, end: int) -> int:
    """Return an index e (start < e <= end) where it is safe to split.

    "Safe" = the request at index e does not reference an objectId that
    was created in the current window [start, e). Walk backward from
    `end` until we find one.
    """
    created: set[str] = {
        cid
        for r in requests[start:end]
        if (cid := _created_object_id(r)) is not None
    }

    safe = end
    while safe > start + 1:
        ref = _referenced_object_id(requests[safe])
        if ref is None or ref not in created:
            return safe
        safe -= 1
        # As we move the split earlier, the request we're stepping over
        # might have created something we should no longer consider "in-chunk".
        stepped_created = _created_object_id(requests[safe])
        if stepped_created:
            created.discard(stepped_created)

    return end  # couldn't find a safer point — accept the full chunk


def _created_object_id(req: dict[str, Any]) -> str | None:
    for kind in _CREATE_KINDS:
        if kind in req:
            oid = req[kind].get("objectId")
            return str(oid) if oid is not None else None
    return None


def _referenced_object_id(req: dict[str, Any]) -> str | None:
    for kind, body in req.items():
        if kind in _CREATE_KINDS:
            return None
        if isinstance(body, dict) and "objectId" in body:
            return str(body["objectId"])
    return None
