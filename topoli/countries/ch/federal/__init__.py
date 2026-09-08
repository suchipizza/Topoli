"""Federal (all-of-Switzerland) adapters built on the geo.admin.ch REST services.

Importing this package registers the federal adapters in ``topoli.core.adapters.registry``.
"""

from __future__ import annotations

from datetime import timedelta

from topoli.core.adapters.base import Record
from topoli.core.adapters.registry import register
from topoli.core.domain import Parcel, Site


def _run_geocode(site: Site, parcel: Parcel | None) -> list[Record]:
    from topoli.countries.ch.federal.geocode import resolve_address

    _, records = resolve_address(site.input_address)
    return records


def _run_parcel(site: Site, parcel: Parcel | None) -> list[Record]:
    from topoli.countries.ch.federal.parcel import get_parcel

    _, records = get_parcel(site)
    return records


def _run_buildings(site: Site, parcel: Parcel | None) -> list[Record]:
    from topoli.countries.ch.federal.buildings import get_buildings

    if parcel is None:
        return []
    _, records = get_buildings(parcel)
    return records


register("ch/federal/geocode", _run_geocode, ttl=timedelta(days=30), needs_parcel=False)
register("ch/federal/parcel", _run_parcel, ttl=timedelta(days=30), needs_parcel=False)
register("ch/federal/buildings", _run_buildings, ttl=timedelta(days=30), needs_parcel=True)
