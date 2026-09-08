"""``ch/federal/parcel`` — cadastral parcel geometry, IDs, area and neighbours.

Requests used (docs in :mod:`topoli.countries.ch.federal.geoadmin`):

1. ``identify`` on ``ch.swisstopo-vd.amtliche-vermessung`` at the site point
   (``geometryType=esriGeometryPoint&tolerance=0&sr=2056&returnGeometry=true``).
   Fallback: the same on ``ch.kantone.cadastralwebmap-farbe`` (no ``bfsnr`` attribute).
2. ``identify`` on the same layer with the parcel outline as ESRI rings
   (``geometryType=esriGeometryPolygon``) → touching parcels for layer-1 section 3.

Area is computed in LV95 with shapely and cross-checked against nothing (the layer publishes
no area attribute); the published value stays ``None`` rather than being invented.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record
from topoli.core.domain import Finding, Jurisdiction, Lang, Parcel, Site, Source
from topoli.core.geospatial import (
    area_m2,
    contains_point,
    simplify_for_url,
    to_esri_rings,
    transform_geojson,
)
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.licences import SWISSTOPO_AV

ADAPTER_ID = "ch/federal/parcel"


class ParcelNotFoundError(LookupError):
    pass


class ParcelAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = SWISSTOPO_AV
    ttl = timedelta(days=30)

    def fetch(self, site: Site) -> list[Record]:
        _, records = get_parcel(site)
        return records

    def to_findings(self, records: list[Record], site: Site, lang: Lang) -> list[Finding]:
        return []  # parcel facts are rendered in layer-1 section 3, not as layer-0 findings

    def health(self) -> HealthStatus:
        try:
            rec = geoadmin.identify_point(self.id, geoadmin.LAYER_AV, 2600423.0, 1199521.0)
            ok = bool(geoadmin.results(rec))
            detail = "identify returned a parcel" if ok else "identify returned nothing"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def get_parcel(site: Site, *, with_neighbours: bool = True) -> tuple[Parcel, list[Record]]:
    east, north = site.coordinates.east, site.coordinates.north
    layer = geoadmin.LAYER_AV
    record = geoadmin.identify_point(ADAPTER_ID, layer, east, north)
    hits = geoadmin.results(record)
    records = [record]
    if not hits:
        layer = geoadmin.LAYER_CADASTRAL_WEBMAP
        record = geoadmin.identify_point(ADAPTER_ID, layer, east, north)
        hits = geoadmin.results(record)
        records.append(record)
    if not hits:
        raise ParcelNotFoundError(f"no cadastral parcel at {east:.1f},{north:.1f}")

    chosen = _choose(hits, site.parcel_ids, east, north)
    props: dict[str, Any] = chosen.get("properties", {})
    if site.parcel_ids and props.get("egris_egrid") not in site.parcel_ids:
        # The entrance point sits in a neighbouring parcel (courtyard, street strip). Follow the
        # EGRID the building register named: search it, then identify at its reference point.
        found, extra = _identify_by_egrid(site.parcel_ids[0], layer)
        records.extend(extra)
        if found is not None:
            chosen = found
            props = chosen.get("properties", {})
    geometry_lv95 = chosen.get("geometry")
    parcel = Parcel(
        national_id=props.get("egris_egrid"),
        local_id=str(props.get("number") or props.get("name") or chosen.get("id")),
        municipality=site.jurisdiction.municipality or str(props.get("bfsnr") or "?"),
        bfs_number=site.jurisdiction.bfs_number
        or (int(props["bfsnr"]) if props.get("bfsnr") else None),
        canton=site.jurisdiction.canton or props.get("ak"),
        geometry_wgs84=transform_geojson(geometry_lv95, to="wgs84") if geometry_lv95 else None,
        geometry_lv95=geometry_lv95,
        area_m2=round(area_m2(geometry_lv95), 1) if geometry_lv95 else None,
        sources=[_source(record, layer)],
    )

    if with_neighbours and geometry_lv95:
        rings = to_esri_rings(simplify_for_url(geometry_lv95))
        neighbours = geoadmin.identify_polygon(ADAPTER_ID, layer, rings, return_geometry=False)
        records.append(neighbours)
        ids = []
        for hit in geoadmin.results(neighbours):
            p = hit.get("properties", {})
            if p.get("egris_egrid") and p.get("egris_egrid") != parcel.national_id:
                ids.append(str(p.get("number") or p.get("egris_egrid")))
        parcel = parcel.model_copy(
            update={
                "adjacent_parcel_ids": sorted(set(ids)),
                "sources": [*parcel.sources, _source(neighbours, layer)],
            }
        )
    return parcel, records


def _identify_by_egrid(egrid: str, layer: str) -> tuple[dict[str, Any] | None, list[Record]]:
    search = geoadmin.search_locations(ADAPTER_ID, egrid, origins="parcel", limit=1)
    hits = geoadmin.results(search)
    if not hits:
        return None, [search]
    attrs = hits[0]["attrs"]
    east, north = float(attrs["y"]), float(attrs["x"])
    ident = geoadmin.identify_point(ADAPTER_ID, layer, east, north)
    for hit in geoadmin.results(ident):
        if hit.get("properties", {}).get("egris_egrid") == egrid:
            return hit, [search, ident]
    return None, [search, ident]


def _choose(
    hits: list[dict[str, Any]], wanted_egrids: list[str], east: float, north: float
) -> dict[str, Any]:
    """Several parcels can touch an entrance point: prefer the GWR's EGRID, then containment."""
    for hit in hits:
        if hit.get("properties", {}).get("egris_egrid") in wanted_egrids:
            return hit
    for hit in hits:
        geom = hit.get("geometry")
        if geom and contains_point(geom, east, north):
            return hit
    return hits[0]


def _source(record: Record, layer: str) -> Source:
    return Source(
        adapter_id=ADAPTER_ID,
        authority="Bundesamt für Landestopografie swisstopo / Kantone (amtliche Vermessung)",
        dataset=layer,
        licence=SWISSTOPO_AV.id,
        retrieved_at=record.retrieved_at,
        url=record.url,
    )
