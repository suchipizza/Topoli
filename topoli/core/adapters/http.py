"""Shared ``httpx`` client for every adapter (PRD §4.4, §12).

* One client, user agent ``topoli/<version> (+repo)``, 10 s timeout.
* Exponential backoff, 3 attempts, on transport errors and 429/5xx.
* Per-host minimum interval between requests (fair-use rate limit).
* Global call budget per audit (≤ 25 network calls) → :class:`BudgetExceededError`, which the
  pipeline turns into a *degraded* coverage entry, never a crash.
* On-disk cache (:mod:`topoli.core.adapters.cache`) with per-request TTL and
  stale-but-served fallback when the refetch fails.
* ``offline=True`` forbids network access entirely (tests, ``topoli render``).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from topoli import __version__
from topoli.core.adapters import cache
from topoli.core.adapters.base import Record

log = logging.getLogger("topoli.http")

USER_AGENT = f"topoli/{__version__} (+https://github.com/suchipizza/Topoli)"
DEFAULT_TIMEOUT = 10.0
MAX_RETRIES = 3
CALL_BUDGET = 25
_RETRY_STATUS = {429, 500, 502, 503, 504}
#: Minimum seconds between two requests to the same host (fair use; geo.admin.ch is generous).
HOST_MIN_INTERVAL: dict[str, float] = {"api3.geo.admin.ch": 0.05}


class BudgetExceededError(RuntimeError):
    """Raised when an audit would exceed the external call budget."""


class OfflineError(RuntimeError):
    """Raised when a network call is attempted while the client is offline."""


class HttpClient:
    def __init__(
        self,
        *,
        budget: int = CALL_BUDGET,
        timeout: float = DEFAULT_TIMEOUT,
        use_cache: bool = True,
        offline: bool = False,
        cache_root: Path | None = None,
    ) -> None:
        self.budget = budget
        self.use_cache = use_cache
        self.offline = offline
        self.cache_root = cache_root
        self.calls = 0  # network calls (cache hits excluded)
        self.cache_hits = 0
        self.recorded: list[Record] | None = None  # set by the fixture recorder
        self._last_request_at: dict[str, float] = {}
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        )

    def reset(self) -> None:
        self.calls = 0
        self.cache_hits = 0

    # -- public API ---------------------------------------------------------------------------

    def get_json(
        self,
        adapter_id: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        *,
        ttl: timedelta = cache.DEFAULT_TTL,
    ) -> Record:
        """GET ``url`` (cache first) and return a ``Record`` with URL and retrieval time."""
        return self._get(adapter_id, url, params, ttl=ttl, parse=None)

    def _get(
        self,
        adapter_id: str,
        url: str,
        params: Mapping[str, Any] | None,
        *,
        ttl: timedelta,
        parse: Callable[[bytes], Any] | None,
    ) -> Record:
        canonical = cache.canonical_url(url, dict(params or {}))
        cached = cache.read(adapter_id, canonical, self.cache_root) if self.use_cache else None
        if cached is not None and cache.is_fresh(cached, ttl):
            self.cache_hits += 1
            self._record(cached)
            return cached

        if self.offline:
            if cached is not None:
                return self._serve_stale(cached, "offline")
            msg = f"offline: no cached response for {canonical}"
            raise OfflineError(msg)

        try:
            fresh = self._fetch(adapter_id, canonical, parse)
        except (httpx.HTTPError, BudgetExceededError) as exc:
            if cached is not None:
                return self._serve_stale(cached, f"{type(exc).__name__}: {exc}")
            raise
        if self.use_cache:
            cache.write(fresh, self.cache_root)
        self._record(fresh)
        return fresh

    def get_bytes(
        self,
        adapter_id: str,
        url: str,
        params: Mapping[str, Any] | None = None,
        *,
        wrap: Callable[[bytes], Any],
        ttl: timedelta = cache.DEFAULT_TTL,
    ) -> Record:
        """Like :meth:`get_json` for binary responses; ``wrap`` turns the bytes into JSON."""
        return self._get(adapter_id, url, params, ttl=ttl, parse=wrap)

    # -- internals ----------------------------------------------------------------------------

    def _record(self, record: Record) -> None:
        if self.recorded is not None:
            self.recorded.append(record)

    def _serve_stale(self, cached: Record, reason: str) -> Record:
        stale = cached.model_copy(update={"stale_as_of": cached.retrieved_at, "from_cache": True})
        log.warning(
            "http.stale_served",
            extra={"adapter_id": cached.adapter_id, "url": cached.url, "reason": reason},
        )
        self._record(stale)
        return stale

    def _throttle(self, host: str) -> None:
        interval = HOST_MIN_INTERVAL.get(host, 0.0)
        if interval <= 0:
            return
        last = self._last_request_at.get(host)
        if last is not None:
            wait = interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_request_at[host] = time.monotonic()

    def _fetch(
        self, adapter_id: str, canonical: str, parse: Callable[[bytes], Any] | None
    ) -> Record:
        if self.calls >= self.budget:
            msg = f"call budget of {self.budget} exhausted (adapter {adapter_id})"
            raise BudgetExceededError(msg)
        self.calls += 1
        host = httpx.URL(canonical).host
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            self._throttle(host)
            try:
                response = self._client.get(canonical)
            except httpx.TransportError as exc:
                last_exc = exc
            else:
                if response.status_code not in _RETRY_STATUS:
                    response.raise_for_status()
                    payload = parse(response.content) if parse else _json_or_error(response)
                    return Record(
                        adapter_id=adapter_id,
                        url=canonical,
                        retrieved_at=datetime.now(tz=UTC),
                        payload=payload,
                        request={"url": canonical},
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


def _json_or_error(response: httpx.Response) -> Any:
    """Parse JSON; a non-JSON 200 (WMS service exception XML) is an HTTP error for us."""
    try:
        return response.json()
    except ValueError as exc:
        msg = f"non-JSON response from {response.url}: {response.text[:120]!r}"
        raise httpx.HTTPStatusError(msg, request=response.request, response=response) from exc


_client: HttpClient | None = None


def get_client() -> HttpClient:
    """Process-wide client; ``reset()`` it at the start of every audit."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = HttpClient()
    return _client


def set_client(client: HttpClient | None) -> None:
    """Replace the process-wide client (CLI flags, tests)."""
    global _client  # noqa: PLW0603
    _client = client
