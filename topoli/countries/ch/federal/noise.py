"""``ch/federal/noise`` — road and rail noise exposure at the parcel (BAFU noise rasters).

Layers (WMS ``GetFeatureInfo``, one call per layer, value ``value_0`` in dB(A), Lden-type
day/night immission levels computed by BAFU's sonBASE model): ``ch.bafu.laerm-strassenlaerm_tag``,
``ch.bafu.laerm-strassenlaerm_nacht``, ``ch.bafu.laerm-bahnlaerm_tag``,
``ch.bafu.laerm-bahnlaerm_nacht``.
The point sampled is the address entrance (facade); the rasters carry no value inside building
footprints, so the parcel's interior point is only a fallback (class A value at that point).

Bands (class B, ours, stated in ``derivation``): day < 55 dB → *low*, 55–65 → *medium*,
≥ 65 → *high*; night < 45 → *low*, 45–55 → *medium*, ≥ 55 → *high*. These follow the order of
magnitude of the federal Noise Abatement Ordinance (LSV) limit values for residential
sensitivity levels; the applicable limit depends on the zone's sensitivity level, which is a
cantonal ÖREB theme and is reported by the ÖREB adapter, not here. Aircraft noise is not
sampled in Phase 1 (BAZL cadastre layers exist; contribution welcome).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, Jurisdiction, Severity
from topoli.core.geospatial import from_geojson
from topoli.countries.ch.federal import geoadmin, wms
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import BAFU_NOISE

ADAPTER_ID = "ch/federal/noise"
LAYERS = {
    "road_day": "ch.bafu.laerm-strassenlaerm_tag",
    "road_night": "ch.bafu.laerm-strassenlaerm_nacht",
    "rail_day": "ch.bafu.laerm-bahnlaerm_tag",
    "rail_night": "ch.bafu.laerm-bahnlaerm_nacht",
}
_SEVERITY: dict[str, Severity] = {"high": "high", "medium": "medium", "low": "info"}
_DAY_BANDS = ((65.0, "high"), (55.0, "medium"))
_NIGHT_BANDS = ((55.0, "high"), (45.0, "medium"))


def band(db: float, *, night: bool) -> str:
    for threshold, name in _NIGHT_BANDS if night else _DAY_BANDS:
        if db >= threshold:
            return name
    return "low"


class NoiseAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = BAFU_NOISE
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        """Sample at the address entrance (the facade) first — the rasters carry no value inside
        building footprints — and only fall back to the parcel's interior point when empty."""
        records: list[Record] = []
        entrance = (ctx.site.coordinates.east, ctx.site.coordinates.north)
        interior = _sample_point(ctx)
        for layer in LAYERS.values():
            rec = wms.get_feature_info(self.id, layer, *entrance)
            if not wms.feature_values(rec) and interior != entrance:
                rec = wms.get_feature_info(self.id, layer, *interior)
            records.append(rec)
        return records

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        values: dict[str, tuple[float, Record]] = {}
        for rec in records:
            layer = geoadmin.layer_of(rec)
            key = next((k for k, v in LAYERS.items() if v == layer), None)
            vals = wms.feature_values(rec)
            if key and vals:
                values[key] = (max(vals), rec)
        findings = []
        for kind in ("road", "rail"):
            day = values.get(f"{kind}_day")
            night = values.get(f"{kind}_night")
            if day is None:
                continue
            day_db, rec = day
            night_db = night[0] if night else None
            level = band(day_db, night=False)
            if night_db is not None and band(night_db, night=True) == "high":
                level = "high"
            severity = _SEVERITY[level]
            source = source_for(
                self.id,
                rec,
                authority="Bundesamt für Umwelt BAFU",
                dataset=geoadmin.layer_of(rec),
                licence=self.licence,
            )
            slots = {
                "day": f"{day_db:.0f}",
                "night": f"{night_db:.0f}" if night_db is not None else "–",
            }
            findings.append(
                make_finding(
                    finding_id=f"noise.{kind}",
                    template_key=f"noise.{kind}.{level}",
                    cls="B",
                    severity=severity,
                    category="noise",
                    source=source,
                    icon="🔊" if kind == "road" else "🚆",
                    slots=slots,
                    derivation=(
                        f"{kind} day {day_db:.1f} dB, night "
                        f"{night_db if night_db is not None else 'n/a'} dB at the parcel's "
                        "interior point; bands: day <55 low, 55–65 medium, ≥65 high; "
                        "night <45/45–55/≥55."
                    ),
                )
            )
        return findings

    def health(self) -> HealthStatus:
        try:
            rec = wms.get_feature_info(self.id, LAYERS["road_day"], 2681718.0, 1247636.0)
            ok = bool(wms.feature_values(rec))
            detail = "value_0 present" if ok else "no value_0 in GetFeatureInfo"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def _sample_point(ctx: SiteContext) -> tuple[float, float]:
    geom = ctx.parcel_geometry
    if geom is None:
        return ctx.site.coordinates.east, ctx.site.coordinates.north
    p = from_geojson(geom).representative_point()
    return round(float(p.x), 1), round(float(p.y), 1)
