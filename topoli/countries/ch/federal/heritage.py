"""``ch/federal/heritage`` — federal heritage inventories touching the parcel.

One ``identify`` call with the parcel outline on:
``ch.babs.kulturgueter`` (KGS inventory of cultural property of national/regional importance,
BABS; attributes ``kgs_nr, beschreibung, kgs_kategorie`` A/B) and
``ch.bak.schutzgebiete-unesco_weltkulturerbe`` (UNESCO World Heritage cultural sites, BAK).

The ISOS inventory (``ch.bak.bundesinventar-schuetzenswerte-ortsbilder``) is listed in the
catalogue but neither ``identify`` nor WMS ``GetFeatureInfo`` return its geometry (tested
2026-09-08, see decision 004); it is reported as *not queryable* in the caveat. Cantonal and
municipal inventories are cantonal data (Zürich: WO-05).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, Jurisdiction
from topoli.core.geospatial import simplify_for_url, to_esri_rings
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import FEDERAL_HERITAGE

ADAPTER_ID = "ch/federal/heritage"
LAYER_KGS = "ch.babs.kulturgueter"
LAYER_UNESCO = "ch.bak.schutzgebiete-unesco_weltkulturerbe"


class HeritageAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = FEDERAL_HERITAGE
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        geom = ctx.parcel_geometry
        if geom is None:
            return []
        rings = to_esri_rings(simplify_for_url(geom))
        return [
            geoadmin.identify_polygon(
                self.id, f"{LAYER_KGS},{LAYER_UNESCO}", rings, return_geometry=False, limit=50
            )
        ]

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if not records:
            return []
        rec = records[0]
        hits = geoadmin.results(rec)
        source = source_for(
            self.id,
            rec,
            authority="BABS / BAK (Bund)",
            dataset=f"{LAYER_KGS}, {LAYER_UNESCO}",
            licence=self.licence,
        )
        findings = []
        for hit in hits:
            props = hit.get("properties", {})
            layer = str(hit.get("layerBodId", ""))
            if layer == LAYER_KGS:
                findings.append(
                    make_finding(
                        finding_id=f"heritage.kgs.{props.get('kgs_nr', '')}",
                        template_key="heritage.kgs",
                        cls="A",
                        severity="high",
                        category="heritage",
                        source=source.model_copy(update={"dataset": LAYER_KGS}),
                        icon="🏛",
                        slots={
                            "name": str(props.get("beschreibung") or props.get("label") or "—"),
                            "category": str(props.get("kgs_kategorie") or "—"),
                        },
                    )
                )
            elif layer == LAYER_UNESCO:
                findings.append(
                    make_finding(
                        finding_id=f"heritage.unesco.{hit.get('id', '')}",
                        template_key="heritage.unesco",
                        cls="A",
                        severity="high",
                        category="heritage",
                        source=source.model_copy(update={"dataset": LAYER_UNESCO}),
                        icon="🏛",
                        slots={"name": str(props.get("label") or props.get("name") or "—")},
                    )
                )
        if not findings:
            findings.append(
                make_finding(
                    finding_id="heritage.federal.none",
                    template_key="heritage.none",
                    cls="A",
                    severity="info",
                    category="heritage",
                    source=source,
                    icon="🏛",
                )
            )
        return findings

    def health(self) -> HealthStatus:
        try:
            rec = geoadmin.identify_point(
                self.id, LAYER_KGS, 2600423.0, 1199521.0, return_geometry=False, limit=1
            )
            hits = geoadmin.results(rec)
            ok = bool(hits) and "kgs_kategorie" in hits[0].get("properties", {})
            detail = "Bundeshaus found in KGS" if ok else "schema drift"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )
