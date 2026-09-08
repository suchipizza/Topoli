"""``ch/federal/contamination`` — federal cadastres of polluted sites (KbS) on the parcel.

The Confederation keeps three KbS cadastres for sites under federal authority; identified in
one ``identify`` call with the parcel outline as ESRI rings:
``ch.bav.kataster-belasteter-standorte-oev`` (public transport, BAV),
``ch.bazl.kataster-belasteter-standorte-zivilflugplaetze`` (civil aerodromes, BAZL),
``ch.vbs.kataster-belasteter-standorte-militaer`` (military, VBS).
The **cantonal** KbS (the vast majority of sites) is a cantonal dataset and reaches the report
as the ÖREB theme ``ch.BelasteteStandorte`` where the cadastre is introduced. A "none" finding
here therefore says "no entry in the federal cadastres", never "not polluted".
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, Jurisdiction
from topoli.core.geospatial import simplify_for_url, to_esri_rings
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import FEDERAL_KBS

ADAPTER_ID = "ch/federal/contamination"
LAYERS = (
    "ch.bav.kataster-belasteter-standorte-oev",
    "ch.bazl.kataster-belasteter-standorte-zivilflugplaetze",
    "ch.vbs.kataster-belasteter-standorte-militaer",
)


class ContaminationAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = FEDERAL_KBS
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        geom = ctx.parcel_geometry
        if geom is None:
            return []
        rings = to_esri_rings(simplify_for_url(geom))
        return [geoadmin.identify_polygon(self.id, ",".join(LAYERS), rings, return_geometry=False)]

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if not records:
            return []
        rec = records[0]
        hits = geoadmin.results(rec)
        source = source_for(
            self.id,
            rec,
            authority="BAV / BAZL / VBS (Bund)",
            dataset=", ".join(LAYERS),
            licence=self.licence,
        )
        if not hits:
            return [
                make_finding(
                    finding_id="contamination.federal",
                    template_key="contamination.none",
                    cls="A",
                    severity="info",
                    category="environment",
                    source=source,
                    icon="🧪",
                )
            ]
        findings = []
        for hit in hits:
            props = hit.get("properties", {})
            name = str(props.get("label") or props.get("name") or props.get("standortname") or "")
            status = str(props.get("status") or props.get("standorttyp") or props.get("typ") or "")
            findings.append(
                make_finding(
                    finding_id=f"contamination.{hit.get('layerBodId', 'federal')}.{hit.get('id')}",
                    template_key="contamination.hit",
                    cls="A",
                    severity="high",
                    category="environment",
                    source=source.model_copy(update={"dataset": str(hit.get("layerBodId", ""))}),
                    icon="🧪",
                    slots={"name": name or "—", "status": status or "—"},
                )
            )
        return findings

    def health(self) -> HealthStatus:
        try:
            rec = geoadmin.identify_point(
                self.id, ",".join(LAYERS), 2600423.0, 1199521.0, return_geometry=False, limit=1
            )
            ok = isinstance(rec.payload, dict) and "results" in rec.payload
            detail = "identify answered" if ok else "unexpected payload"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )
