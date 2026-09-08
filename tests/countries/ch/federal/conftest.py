from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from topoli.core.adapters import get_client
from topoli.core.domain import Building, Parcel, Site
from topoli.countries.ch.federal.buildings import get_buildings
from topoli.countries.ch.federal.geocode import resolve_address
from topoli.countries.ch.federal.parcel import get_parcel

Spine = tuple[Site, Parcel, list[Building]]


@pytest.fixture
def run_spine(replay: Callable[[str, str], int]) -> Callable[[str, str], Spine]:
    """Seed the cache for ``slug`` and run resolve → parcel → buildings offline."""

    def _run(slug: str, address: str, **kw: Any) -> Spine:
        replay("ch/federal/buildings", slug)
        get_client().reset()
        site, _ = resolve_address(address)
        parcel, _ = get_parcel(site)
        buildings, _ = get_buildings(parcel)
        return site, parcel, buildings

    return _run
