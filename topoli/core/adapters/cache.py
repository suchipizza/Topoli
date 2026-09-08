"""On-disk cache for adapter records (PRD §4.4).

Layout: ``~/.topoli/cache/<adapter_id>/<sha256(canonical request URL)>.json``. Each file is a
serialized :class:`Record`. TTL is decided by the caller (adapters declare ``ttl``; 30 days for
static layers, 24 h for construction events). Stale-but-served: when a refetch fails, the stale
file is returned with ``stale_as_of`` set to its original ``retrieved_at``.

The same files double as **test fixtures**: ``topoli fixtures record`` copies them into
``tests/fixtures/<adapter_id>/<slug>/`` and tests seed a temporary cache from there, so a
replayed test never touches the network.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from topoli.core.adapters.base import Record
from topoli.paths import cache_dir

log = logging.getLogger("topoli.cache")

DEFAULT_TTL = timedelta(days=30)


def canonical_url(url: str, params: Mapping[str, Any] | None) -> str:
    """The exact GET URL httpx would send; used as the cache key and stored in ``Record.url``."""
    return str(httpx.Request("GET", url, params=params).url)


def cache_key(canonical: str) -> str:
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cache_path(adapter_id: str, canonical: str, root: Path | None = None) -> Path:
    return (root or cache_dir()) / adapter_id / f"{cache_key(canonical)}.json"


def read(adapter_id: str, canonical: str, root: Path | None = None) -> Record | None:
    path = cache_path(adapter_id, canonical, root)
    if not path.is_file():
        return None
    try:
        record = Record.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError as exc:  # corrupt file → ignore, will be refetched
        log.warning("cache.corrupt", extra={"path": str(path), "error": str(exc)})
        return None
    return record.model_copy(update={"from_cache": True})


def write(record: Record, root: Path | None = None) -> Path:
    path = cache_path(record.adapter_id, record.url, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = record.model_copy(update={"from_cache": False, "stale_as_of": None})
    tmp = path.with_suffix(".tmp")
    tmp.write_text(clean.model_dump_json(indent=1), encoding="utf-8")
    tmp.replace(path)
    return path


def is_fresh(record: Record, ttl: timedelta, now: datetime | None = None) -> bool:
    now = now or datetime.now(tz=UTC)
    return now - record.retrieved_at <= ttl


@dataclass(frozen=True)
class CacheStats:
    root: Path
    files: int
    bytes: int
    adapters: dict[str, int]

    @property
    def megabytes(self) -> float:
        return round(self.bytes / 1_000_000, 2)


def stats(root: Path | None = None) -> CacheStats:
    root = root or cache_dir()
    files = 0
    total = 0
    adapters: dict[str, int] = {}
    if root.is_dir():
        for path in root.rglob("*.json"):
            files += 1
            total += path.stat().st_size
            adapter_id = path.parent.relative_to(root).as_posix()
            adapters[adapter_id] = adapters.get(adapter_id, 0) + 1
    return CacheStats(root=root, files=files, bytes=total, adapters=dict(sorted(adapters.items())))


def clear(root: Path | None = None, adapter_id: str | None = None) -> int:
    root = root or cache_dir()
    target = root / adapter_id if adapter_id else root
    if not target.is_dir():
        return 0
    count = sum(1 for _ in target.rglob("*.json"))
    shutil.rmtree(target)
    root.mkdir(parents=True, exist_ok=True)
    return count
