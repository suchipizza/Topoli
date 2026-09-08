"""``ch/federal/solar`` — roof suitability for solar energy (Sonnendach, BFE).

Layer ``ch.bfe.solarenergie-eignung-daecher`` via ``identify`` with the parcel outline
(ESRI rings). One feature per roof surface with ``gwr_egid``, ``klasse`` (1 = gering … 5 =
hervorragend), ``klasse_text`` ("Mittel##Moyenne##Media##Mean##Mittel" — DE##FR##IT##EN##RM),
``flaeche`` (m²), ``ausrichtung`` (° from south, −180…180), ``neigung`` (°), ``gstrahlung``
(kWh/a), ``stromertrag`` (kWh/a). Roofs are attributed to the parcel's buildings by EGID; if no
EGID matches, every roof inside the outline is kept. The finding reports the best roof class
per building (class A) plus the total suitable roof area (class B sum).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, Jurisdiction
from topoli.core.geospatial import simplify_for_url, to_esri_rings
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import BFE_SOLAR

ADAPTER_ID = "ch/federal/solar"
LAYER = "ch.bfe.solarenergie-eignung-daecher"
_LEVELS = {1: "poor", 2: "medium", 3: "good", 4: "very_good", 5: "excellent"}


class SolarAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = BFE_SOLAR
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        geom = ctx.parcel_geometry
        if geom is None:
            return []
        rings = to_esri_rings(simplify_for_url(geom))
        return [geoadmin.identify_polygon(self.id, LAYER, rings, return_geometry=False, limit=200)]

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if not records:
            return []
        rec = records[0]
        roofs = [h.get("properties", {}) for h in geoadmin.results(rec)]
        egids = {b.id for b in ctx.buildings}
        mine = [r for r in roofs if str(r.get("gwr_egid")) in egids] if egids else []
        if not mine:
            mine = roofs
        source = source_for(
            self.id, rec, authority="Bundesamt für Energie BFE", dataset=LAYER, licence=self.licence
        )
        if not mine:
            return [
                make_finding(
                    finding_id="solar.none",
                    template_key="solar.none",
                    cls="A",
                    severity="info",
                    category="environment",
                    source=source,
                    icon="☀️",
                )
            ]
        best = max(mine, key=lambda r: (_int(r.get("klasse")), _float(r.get("flaeche"))))
        klass = _int(best.get("klasse"))
        good_area = sum(_float(r.get("flaeche")) for r in mine if _int(r.get("klasse")) >= 3)
        total_yield = sum(_float(r.get("stromertrag")) for r in mine if _int(r.get("klasse")) >= 3)
        level = _LEVELS.get(klass, "medium")
        return [
            make_finding(
                finding_id="solar.best_roof",
                template_key=f"solar.{level}",
                cls="A",
                severity="info",
                category="environment",
                source=source,
                icon="☀️",
                slots={
                    "klasse": str(klass),
                    "area": f"{good_area:.0f}",
                    "yield_mwh": f"{total_yield / 1000:.0f}",
                    "roofs": str(len(mine)),
                },
                derivation=(
                    f"best of {len(mine)} roof surfaces: class {klass}; suitable area = Σ flaeche "
                    f"where klasse ≥ 3 = {good_area:.0f} m²; "
                    f"yield = Σ stromertrag = {total_yield:.0f} kWh/a"
                ),
            )
        ]

    def health(self) -> HealthStatus:
        try:
            rec = geoadmin.identify_point(
                self.id, LAYER, 2681686.65, 1247622.32, return_geometry=False, limit=1
            )
            hits = geoadmin.results(rec)
            ok = bool(hits) and "klasse" in hits[0].get("properties", {})
            detail = "roof with klasse returned" if ok else "schema drift or no roof"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def _int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0
