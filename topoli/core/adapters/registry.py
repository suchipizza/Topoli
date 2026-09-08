"""Adapter registry: id → how to run it for a site.

Every adapter registers a runner that takes the resolved ``Site`` (and, when it exists, the
``Parcel``) and returns the raw records it fetched. The fixture recorder and the pipeline
use this table; nothing else should hard-code adapter ids.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from topoli.core.adapters.base import Record
from topoli.core.domain import Parcel, Site

Runner = Callable[[Site, Parcel | None], list[Record]]


class AdapterSpec:
    def __init__(self, adapter_id: str, runner: Runner, ttl: timedelta, needs_parcel: bool) -> None:
        self.id = adapter_id
        self.runner = runner
        self.ttl = ttl
        self.needs_parcel = needs_parcel


_REGISTRY: dict[str, AdapterSpec] = {}


def register(
    adapter_id: str,
    runner: Runner,
    *,
    ttl: timedelta = timedelta(days=30),
    needs_parcel: bool = True,
) -> None:
    _REGISTRY[adapter_id] = AdapterSpec(adapter_id, runner, ttl, needs_parcel)


def get(adapter_id: str) -> AdapterSpec:
    _ensure_loaded()
    try:
        return _REGISTRY[adapter_id]
    except KeyError as exc:
        msg = f"unknown adapter {adapter_id!r}; known: {', '.join(sorted(_REGISTRY))}"
        raise KeyError(msg) from exc


def all_ids() -> list[str]:
    _ensure_loaded()
    return sorted(_REGISTRY)


def _ensure_loaded() -> None:
    # Importing the country packages registers their adapters (side effect on import).
    import topoli.countries.ch.federal  # noqa: F401
