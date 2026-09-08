"""``ch/federal/terrain`` — elevation range and slope of the parcel from swissALTI3D.

Endpoint: elevation profile service (docs read 2026-09-08,
https://docs.geo.admin.ch/access-data/get-elevation-profile.html):
``GET https://api3.geo.admin.ch/rest/services/profile.json``
``?geom=<GeoJSON LineString>&sr=2056&nb_points=<n>``
→ ``[{alts: {COMB, DTM2, DTM25}, dist, easting, northing}, …]``. One request samples a
polyline through the parcel's bounding box (both diagonals, 24 points). ``COMB`` is used.

Slope (class B, stated in ``derivation``): (max − min elevation) ÷ bbox diagonal length, in %
and degrees — a coarse whole-parcel gradient, not a DTM slope raster. Elevation is class A.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta

from topoli.core.adapters import HealthStatus, Record, SiteContext, get_client
from topoli.core.domain import Finding, Jurisdiction
from topoli.core.geospatial import from_geojson
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import SWISSTOPO_ALTI

ADAPTER_ID = "ch/federal/terrain"
PROFILE_URL = "https://api3.geo.admin.ch/rest/services/profile.json"
NB_POINTS = 24


class TerrainAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = SWISSTOPO_ALTI
    ttl = timedelta(days=365)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        geom = ctx.parcel_geometry
        if geom is None:
            e, n = ctx.site.coordinates.east, ctx.site.coordinates.north
            minx, miny, maxx, maxy = e - 15, n - 15, e + 15, n + 15
        else:
            minx, miny, maxx, maxy = from_geojson(geom).bounds
        line = {
            "type": "LineString",
            "coordinates": [
                [round(minx, 1), round(miny, 1)],
                [round(maxx, 1), round(maxy, 1)],
                [round(minx, 1), round(maxy, 1)],
                [round(maxx, 1), round(miny, 1)],
            ],
        }
        params = {
            "geom": json.dumps(line, separators=(",", ":")),
            "sr": 2056,
            "nb_points": NB_POINTS,
        }
        return [get_client().get_json(self.id, PROFILE_URL, params, ttl=self.ttl)]

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if not records:
            return []
        rec = records[0]
        points = rec.payload if isinstance(rec.payload, list) else []
        alts = [float(p["alts"]["COMB"]) for p in points if isinstance(p, dict) and "alts" in p]
        if not alts:
            return []
        lo, hi = min(alts), max(alts)
        geom = ctx.parcel_geometry
        if geom is not None:
            minx, miny, maxx, maxy = from_geojson(geom).bounds
        else:
            minx, miny, maxx, maxy = 0.0, 0.0, 30.0, 30.0
        diag = math.hypot(maxx - minx, maxy - miny) or 1.0
        slope_pct = (hi - lo) / diag * 100
        slope_deg = math.degrees(math.atan((hi - lo) / diag))
        level = "steep" if slope_pct >= 30 else "sloped" if slope_pct >= 10 else "flat"
        source = source_for(
            self.id,
            rec,
            authority="Bundesamt für Landestopografie swisstopo",
            dataset="swissALTI3D via profile service (COMB)",
            licence=self.licence,
        )
        return [
            make_finding(
                finding_id="terrain.slope",
                template_key=f"terrain.{level}",
                cls="B",
                severity="medium" if level == "steep" else "info",
                category="environment",
                source=source,
                icon="⛰",
                slots={
                    "min": f"{lo:.0f}",
                    "max": f"{hi:.0f}",
                    "slope_pct": f"{slope_pct:.0f}",
                    "slope_deg": f"{slope_deg:.0f}",
                },
                derivation=(
                    f"{len(alts)} samples along both bbox diagonals; "
                    f"min {lo:.1f} m, max {hi:.1f} m; "
                    f"slope = (max−min)/diagonal({diag:.0f} m) = {slope_pct:.1f} % "
                    f"≈ {slope_deg:.1f}°; "
                    "flat <10 %, sloped 10–30 %, steep ≥30 %."
                ),
            )
        ]

    def health(self) -> HealthStatus:
        try:
            params = {
                "geom": json.dumps(
                    {"type": "LineString", "coordinates": [[2681624, 1247572], [2681765, 1247676]]}
                ),
                "sr": 2056,
                "nb_points": 4,
            }
            rec = get_client().get_json(self.id, PROFILE_URL, params, ttl=timedelta(0))
            ok = isinstance(rec.payload, list) and bool(rec.payload) and "alts" in rec.payload[0]
            detail = "profile answered" if ok else "schema drift"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )
