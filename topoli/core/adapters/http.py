"""Shared ``httpx`` client for every adapter.

WO-02 ships the minimum: one client, user agent, 10 s timeout, three retries with exponential
backoff on transient errors, and a per-audit call counter with a hard budget (PRD §12: ≤ 25
external calls per audit). WO-04 adds the on-disk cache and per-host rate limits on top.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import httpx

from topoli import __version__
from topoli.core.adapters.base import Record

log = logging.getLogger("topoli.http")

USER_AGENT = f"topoli/{__version__} (+https://github.com/suchipizza/Topoli)"
DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
CALL_BUDGET = 25
_RETRY_STATUS = {429, 500, 502, 503, 504}


class BudgetExceededError(RuntimeError):
    """Raised when an audit would exceed the external call budget."""


class HttpClient:
    def __init__(self, *, budget: int = CALL_BUDGET, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.budget = budget
        self.calls = 0
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        )

    def reset(self) -> None:
        self.calls = 0

    def get_json(
        self, adapter_id: str, url: str, params: Mapping[str, Any] | None = None
    ) -> Record:
        """GET ``url`` and wrap the JSON body in a ``Record`` with URL and retrieval time."""
        if self.calls >= self.budget:
            msg = f"call budget of {self.budget} exhausted (adapter {adapter_id})"
            raise BudgetExceededError(msg)
        self.calls += 1
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.get(url, params=params)
            except httpx.TransportError as exc:
                last_exc = exc
            else:
                if response.status_code not in _RETRY_STATUS:
                    response.raise_for_status()
                    return Record(
                        adapter_id=adapter_id,
                        url=str(response.url),
                        retrieved_at=datetime.now(tz=UTC),
                        payload=response.json(),
                        request={"url": url, "params": dict(params or {})},
                    )
                last_exc = httpx.HTTPStatusError(
                    f"HTTP {response.status_code}", request=response.request, response=response
                )
            delay = 0.5 * (2**attempt)
            log.warning(
                "http.retry",
                extra={"adapter_id": adapter_id, "attempt": attempt + 1, "delay": delay},
            )
            time.sleep(delay)
        assert last_exc is not None
        raise last_exc


_client: HttpClient | None = None


def get_client() -> HttpClient:
    """Process-wide client; ``reset()`` it at the start of every audit."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = HttpClient()
    return _client
