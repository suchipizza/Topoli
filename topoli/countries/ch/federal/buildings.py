"""``ch/federal/buildings`` — buildings on a parcel from the GWR/RegBL via geo.admin.ch.

Request used: ``identify`` on ``ch.bfs.gebaeude_wohnungs_register`` with the parcel outline as
ESRI rings (``geometryType=esriGeometryPolygon&sr=2056&returnGeometry=true&limit=200``).
The layer has one point per *entrance* (``egid_edid``); we keep only entrances whose ``egrid``
(or ``lparz``) matches the parcel, then collapse entrances to one ``Building`` per EGID.

Attributes used (Merkmalskatalog 4.2, see :mod:`gwr_codes`): ``garea`` (footprint m²),
``gastw`` (floors above ground), ``gbauj`` (construction year), ``gbaup`` (period, when year is
missing), ``gkat``/``gklas`` (category/class), ``gstat`` (status), ``gwaerzh1``/``genh1``
(heating system / energy source), ``gschutzr`` (civil-defence shelter, unused). Missing
attributes are listed in ``Building.missing_attributes``; nothing is defaulted.

Footprint *polygons* are not exposed by an identifiable geo.admin.ch layer; see
``docs/decisions/003-geoadmin-sources.md``. ``geometry_*`` holds the building's reference point
(``gkode``/``gkodn``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record
from topoli.core.domain import Building, Finding, Jurisdiction, Lang, Parcel, Site, Source
from topoli.core.geospatial import contains_point, lv95_to_wgs84, simplify_for_url, to_esri_rings
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.gwr_codes import GBAUP, GENH, GKAT, GKLAS, GSTAT, GWAERZH, label
from topoli.countries.ch.federal.licences import BFS_GWR

ADAPTER_ID = "ch/federal/buildings"
_ATTRS = ("garea", "gastw", "gbauj", "gkat", "gklas", "gstat", "gwaerzh1", "genh1")


class BuildingsAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = BFS_GWR
    ttl = timedelta(days=30)

    def fetch(
        self, site: Site
    ) -> list[Record]:  # pragma: no cover - needs the parcel; see get_buildings
        return []

    def to_findings(self, records: list[Record], site: Site, lang: Lang) -> list[Finding]:
        return []

    def health(self) -> HealthStatus:
        try:
            rec = geoadmin.identify_point(
                self.id,
                geoadmin.LAYER_GWR,
                2600423.0,
                1199521.0,
                tolerance=10,
                return_geometry=False,
                limit=1,
            )
            ok = bool(geoadmin.results(rec))
            detail = "identify returned a building" if ok else "identify returned nothing"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def get_buildings(parcel: Parcel) -> tuple[list[Building], list[Record]]:
    if not parcel.geometry_lv95:
        return [], []
    rings = to_esri_rings(simplify_for_url(parcel.geometry_lv95))
    record = geoadmin.identify_polygon(ADAPTER_ID, geoadmin.LAYER_GWR, rings, return_geometry=True)
    source = Source(
        adapter_id=ADAPTER_ID,
        authority="Bundesamt für Statistik BFS",
        dataset=geoadmin.LAYER_GWR,
        licence=BFS_GWR.id,
        retrieved_at=record.retrieved_at,
        url=record.url,
    )
    by_egid: dict[str, dict[str, Any]] = {}
    for hit in geoadmin.results(record):
        props = hit.get("properties", {})
        on_parcel = (
            (parcel.national_id and props.get("egrid") == parcel.national_id)
            or props.get("lparz") == parcel.local_id
            or (
                props.get("gkode") is not None
                and props.get("gkodn") is not None
                and contains_point(
                    parcel.geometry_lv95, float(props["gkode"]), float(props["gkodn"])
                )
            )
        )
        if not on_parcel or props.get("egid") is None:
            continue
        by_egid.setdefault(str(props["egid"]), props)

    buildings = []
    for egid, props in sorted(by_egid.items()):
        east, north = props.get("gkode"), props.get("gkodn")
        point_lv95 = None
        point_wgs84 = None
        if east is not None and north is not None:
            e, n = float(east), float(north)
            point_lv95 = {"type": "Point", "coordinates": [e, n]}
            lon, lat = lv95_to_wgs84(e, n)
            point_wgs84 = {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]}
        use_parts = [label(GKAT, props.get("gkat")), label(GKLAS, props.get("gklas"))]
        energy_parts = [label(GWAERZH, props.get("gwaerzh1")), label(GENH, props.get("genh1"))]
        year = props.get("gbauj")
        buildings.append(
            Building(
                id=egid,
                geometry_wgs84=point_wgs84,
                geometry_lv95=point_lv95,
                footprint_m2=float(props["garea"]) if props.get("garea") is not None else None,
                use=" · ".join(p for p in use_parts if p) or None,
                year=int(year) if year else None,
                floors=int(props["gastw"]) if props.get("gastw") is not None else None,
                energy=" · ".join(p for p in energy_parts if p) or None,
                heritage=None,
                missing_attributes=[a for a in _ATTRS if props.get(a) in (None, "", "-")]
                + (
                    ["gbauj (period only: " + str(label(GBAUP, props.get("gbaup"))) + ")"]
                    if not year and props.get("gbaup")
                    else []
                ),
                sources=[source],
            )
        )
    # Status is kept on the record for layer 1; demolished/planned buildings are still returned.
    for b in buildings:
        status = label(GSTAT, by_egid[b.id].get("gstat"))
        if status and "bestehend" not in status:
            b.missing_attributes.append(f"gstat={status}")
    return buildings, [record]
