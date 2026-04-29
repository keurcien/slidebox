"""Retry with exponential backoff and jitter.

The Slides API enforces strict per-minute quotas. Rather than letting a
429 propagate, we retry a handful of times with exponentially growing
sleeps. A final failure surfaces as `QuotaExceededError` so callers can
distinguish it from programming errors.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

from slidebox.errors import QuotaExceededError

log = logging.getLogger(__name__)
T = TypeVar("T")

_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def _is_retryable(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if status is None:
        resp = getattr(exc, "resp", None)
        status = getattr(resp, "status", None)
    if status is None:
        return False
    try:
        return int(status) in _RETRYABLE_STATUSES
    except (TypeError, ValueError):
        return False


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    max_attempts: int = 5,
    initial_delay: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 32.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call fn() with exponential backoff on retryable failures.

    - Retryable errors (429, 5xx) are retried up to `max_attempts` times;
      exhaustion raises `QuotaExceededError`.
    - Non-retryable errors propagate immediately so callers see the true
      cause (auth, validation, network, etc.) rather than a quota wrapper.
    """
    delay = initial_delay
    last_exc: BaseException | None = None
    attempts_used = 0
    for attempt in range(1, max_attempts + 1):
        attempts_used = attempt
        try:
            return fn()
        except BaseException as exc:
            if not _is_retryable(exc):
                raise
            if attempt == max_attempts:
                last_exc = exc
                break
            sleep_for = delay + random.uniform(0, delay / 2)
            log.warning(
                "retryable API failure on attempt %s/%s: %s (sleeping %.2fs)",
                attempt,
                max_attempts,
                exc,
                sleep_for,
            )
            sleep(sleep_for)
            delay = min(delay * factor, max_delay)
            last_exc = exc
    assert last_exc is not None
    raise QuotaExceededError(
        f"Google Slides API failed after {attempts_used} attempts: {last_exc}"
    ) from last_exc
