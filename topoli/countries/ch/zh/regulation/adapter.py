"""``ch/zh/regulation`` — extracted BZO rules for the parcel's zone (City of Zürich only).

Requires the zone code from ``ch/zh/zoning`` (``ctx.parcel.zoning_code``). Other Zürich
municipalities keep their zone code but get :class:`NotContributedError` → coverage
``not_contributed`` and a class-D stub ("regulation parsing for <municipality> not yet
contributed"), as PRD §4.2 prescribes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, Jurisdiction, Regulation
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.zh.licences import ZH_BZO
from topoli.countries.ch.zh.regulation.parser import ZoneRules, parse_bzo
from topoli.countries.ch.zh.regulation.source import bzo_text, bzo_version, fetch_bzo

ADAPTER_ID = "ch/zh/regulation"
CITY_OF_ZURICH_BFS = 261


class NotContributedError(LookupError):
    """The municipality's ordinance has not been parsed yet (contribution welcome)."""


class RegulationAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH", canton="ZH", municipality="Zürich", bfs_number=261)
    licence = ZH_BZO
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        if ctx.site.jurisdiction.bfs_number != CITY_OF_ZURICH_BFS:
            raise NotContributedError(
                f"regulation parsing for {ctx.site.jurisdiction.municipality} not yet contributed"
            )
        if ctx.parcel is None or not ctx.parcel.zoning_code:
            raise LookupError("no zone code for this parcel")
        return [fetch_bzo(self.id)]

    def regulation(self, records: list[Record], ctx: SiteContext) -> Regulation | None:
        if not records or ctx.parcel is None or not ctx.parcel.zoning_code:
            return None
        rec = records[0]
        parsed = parse_bzo(bzo_text(rec))
        zone = parsed.for_code(ctx.parcel.zoning_code)
        source = source_for(
            self.id,
            rec,
            authority="Stadt Zürich (Gemeinderat)",
            dataset=f"BZO 2016, AS 700.100 — {bzo_version(rec) or 'consolidated text'}",
            licence=self.licence,
        )
        if zone is None:
            zone = ZoneRules(ctx.parcel.zoning_code, unresolved=["all"])
        return Regulation(
            jurisdiction=self.jurisdiction,
            zone_code=ctx.parcel.zoning_code,
            zone_name=ctx.parcel.zoning_name,
            source_document=source,
            rules=zone.rules,
            unresolved=zone.unresolved,
            parser_version=parsed.parser_version,
        )

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        reg = self.regulation(records, ctx)
        if reg is None:
            return []
        by_key = {r.key: r for r in reg.rules}
        if not reg.rules:
            return [
                make_finding(
                    finding_id="regulation.rules",
                    template_key="regulation.plan_specific",
                    cls="D",
                    severity="info",
                    category="zoning",
                    source=reg.source_document,
                    icon="📏",
                    slots={"code": reg.zone_code, "name": reg.zone_name or ""},
                )
            ]
        floors = by_key.get("max_full_floors")
        height = by_key.get("max_building_height_m")
        far = by_key.get("floor_area_ratio")
        spans = [s for r in (floors, height, far) if r for s in r.evidence_spans]
        return [
            make_finding(
                finding_id="regulation.rules",
                template_key="regulation.rules",
                cls="A",
                severity="info",
                category="zoning",
                source=reg.source_document,
                icon="📏",
                slots={
                    "code": reg.zone_code,
                    "floors": str(floors.value) if floors else "–",
                    "height": f"{float(height.value):g}" if height else "–",
                    "far": f"{float(far.value):g}" if far else "–",
                    "article": floors.evidence_spans[0].article if floors else "–",
                    "n_rules": str(len(reg.rules)),
                },
                evidence_spans=spans,
                rule_ref="max_full_floors" if floors else None,
            )
        ]

    def health(self) -> HealthStatus:
        try:
            rec = fetch_bzo(self.id)
            parsed = parse_bzo(bzo_text(rec))
            w4 = parsed.zones.get("W4")
            ok = bool(w4 and any(r.key == "floor_area_ratio" for r in w4.rules))
            detail = (
                f"parsed {len(parsed.zones)} zones ({bzo_version(rec)})"
                if ok
                else "W4 AZ not parsed — layout drift?"
            )
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )
