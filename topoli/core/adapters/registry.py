"""Adapter registry: id → adapter instance (+ how to run it).

Every adapter package registers its adapters on import. The fixture recorder, the pipeline and
the coverage table use this registry; nothing else hard-codes adapter ids.
"""

from __future__ import annotations

from typing import Literal

from topoli.core.adapters.base import Adapter

Tier = Literal["spine", "federal", "cantonal", "events"]


class AdapterSpec:
    def __init__(self, adapter: Adapter, tier: Tier, needs_parcel: bool) -> None:
        self.adapter = adapter
        self.id = adapter.id
        self.tier = tier
        self.needs_parcel = needs_parcel


_REGISTRY: dict[str, AdapterSpec] = {}


def register(adapter: Adapter, *, tier: Tier, needs_parcel: bool = True) -> None:
    _REGISTRY[adapter.id] = AdapterSpec(adapter, tier, needs_parcel)


def get(adapter_id: str) -> AdapterSpec:
    _ensure_loaded()
    try:
        return _REGISTRY[adapter_id]
    except KeyError as exc:
        msg = f"unknown adapter {adapter_id!r}; known: {', '.join(sorted(_REGISTRY))}"
        raise KeyError(msg) from exc


def all_specs(tier: Tier | None = None) -> list[AdapterSpec]:
    _ensure_loaded()
    return [s for s in _REGISTRY.values() if tier is None or s.tier == tier]


def all_ids() -> list[str]:
    return [s.id for s in all_specs()]


def _ensure_loaded() -> None:
    # Importing the country packages registers their adapters (side effect on import).
    import topoli.countries.ch.federal
    import topoli.countries.ch.zh  # noqa: F401
