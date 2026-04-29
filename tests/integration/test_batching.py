from __future__ import annotations

import pytest

from slidebox.client.batching import chunk_requests
from slidebox.client.retry import _is_retryable, retry_with_backoff
from slidebox.errors import QuotaExceededError


def test_small_batch_not_split() -> None:
    reqs = [{"createSlide": {"objectId": f"s{i}"}} for i in range(5)]
    assert chunk_requests(reqs) == [reqs]


def test_large_batch_splits_on_safe_boundary() -> None:
    # 2500 independent createSlide requests → 2 chunks (2000 + 500)
    reqs = [{"createSlide": {"objectId": f"s{i}"}} for i in range(2500)]
    chunks = chunk_requests(reqs, max_per_chunk=2000)
    assert len(chunks) == 2
    assert len(chunks[0]) == 2000
    assert sum(len(c) for c in chunks) == 2500


def test_split_never_separates_create_from_dependent() -> None:
    """createShape + insertText for the same id must land in the same chunk."""
    reqs = []
    for i in range(1500):
        reqs.append({"createShape": {"objectId": f"s{i}"}})
    # Small trailing pair that references a new id at the boundary.
    reqs.append({"createShape": {"objectId": "last"}})
    reqs.append({"insertText": {"objectId": "last", "text": "x"}})
    chunks = chunk_requests(reqs, max_per_chunk=1500)
    # "last" createShape and its insertText must co-locate.
    for chunk in chunks:
        ids = {r.get("createShape", {}).get("objectId") for r in chunk if "createShape" in r}
        for r in chunk:
            if "insertText" in r:
                # If insertText for "last" is in this chunk, createShape("last") must be too
                if r["insertText"]["objectId"] == "last":
                    assert "last" in ids


# ── retry ─────────────────────────────────────────────────────────────

class _FakeErr(Exception):
    def __init__(self, status: int) -> None:
        self.status_code = status


def test_retryable_429() -> None:
    assert _is_retryable(_FakeErr(429))
    assert _is_retryable(_FakeErr(503))
    assert not _is_retryable(_FakeErr(400))
    assert not _is_retryable(_FakeErr(401))


def test_retry_succeeds_after_transient_failures() -> None:
    calls = {"n": 0}
    slept: list[float] = []

    def fn() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise _FakeErr(429)
        return "ok"

    result = retry_with_backoff(fn, initial_delay=0.01, sleep=slept.append)
    assert result == "ok"
    assert calls["n"] == 3
    assert len(slept) == 2


def test_retry_exhaustion_raises_quota_error() -> None:
    def fn() -> None:
        raise _FakeErr(429)

    with pytest.raises(QuotaExceededError):
        retry_with_backoff(fn, max_attempts=3, initial_delay=0.01, sleep=lambda _: None)


def test_non_retryable_propagates_original_exception() -> None:
    def fn() -> None:
        raise _FakeErr(400)

    # Not wrapped as QuotaExceededError — caller sees the true cause.
    with pytest.raises(_FakeErr):
        retry_with_backoff(fn, max_attempts=3, initial_delay=0.01, sleep=lambda _: None)
