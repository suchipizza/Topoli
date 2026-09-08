"""``ch/zh/heritage`` — protected objects (cantonal and communal) on the parcel, Canton of Zürich.

Source: cantonal WFS type ``ms:ogd-0368_giszhpub_arv_kaz_denkmalschutzobjekte_p``
("Denkmalschutzobjekte", Kantonale Denkmalpflege, ARE), one GetFeature over the parcel's
bounding box (+5 m). Objects are matched to the parcel by ``katasternummer`` (parcel number) or
``egid`` (a building on the parcel); unmatched points inside the box are ignored. Class A.

The City of Zürich's own "Denkmalpflege-Inventar" WFS (ogd.stadt-zuerich.ch) answered HTTP 500
to every request on 2026-09-08; the cantonal dataset includes communal objects (``einstufung``
``kommunal``) and is used instead — see decision 006.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, Jurisdiction
from topoli.core.geospatial import from_geojson
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.zh import wfs
from topoli.countries.ch.zh.licences import ZH_OGD

ADAPTER_ID = "ch/zh/heritage"


class ZhHeritageAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH", canton="ZH")
    licence = ZH_OGD
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        geom = ctx.parcel_geometry
        if geom is None:
            raise LookupError("no parcel geometry")
        minx, miny, maxx, maxy = from_geojson(geom).bounds
        return [
            wfs.get_features(
                self.id, wfs.TYPE_HERITAGE, (minx - 5, miny - 5, maxx + 5, maxy + 5), count=50
            )
        ]

    def matches(self, records: list[Record], ctx: SiteContext) -> list[dict[str, Any]]:
        if not records or ctx.parcel is None:
            return []
        egids = {b.id for b in ctx.buildings}
        out = []
        for f in wfs.features(records[0]):
            p = f.get("properties", {})
            if (
                str(p.get("katasternummer") or "") == ctx.parcel.local_id
                or str(p.get("egid") or "") in egids
            ):
                out.append(dict(p))
        return out

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if not records:
            return []
        source = source_for(
            self.id,
            records[0],
            authority="Kanton Zürich, Kantonale Denkmalpflege (ARE)",
            dataset=wfs.TYPE_HERITAGE,
            licence=self.licence,
        )
        hits = self.matches(records, ctx)
        if not hits:
            return [
                make_finding(
                    finding_id="heritage.zh.none",
                    template_key="heritage.zh.none",
                    cls="A",
                    severity="info",
                    category="heritage",
                    source=source,
                    icon="🏛",
                )
            ]
        findings = []
        for p in hits:
            findings.append(
                make_finding(
                    finding_id=f"heritage.zh.{p.get('odb_id')}",
                    template_key="heritage.zh.listed",
                    cls="A",
                    severity="high",
                    category="heritage",
                    source=source,
                    icon="🏛",
                    slots={
                        "name": str(p.get("objekt") or "—"),
                        "level": str(p.get("einstufung") or "—"),
                        "status": str(p.get("schutz") or "—"),
                        "decision": str(p.get("erlass") or "—"),
                        "year": str(p.get("baujahr") or "—"),
                    },
                )
            )
        return findings

    def health(self) -> HealthStatus:
        try:
            rec = wfs.get_features(
                self.id,
                wfs.TYPE_HERITAGE,
                (2683027, 1247082, 2683147, 1247202),
                count=1,
                ttl=timedelta(0),
            )
            feats = wfs.features(rec)
            ok = bool(feats) and "einstufung" in feats[0].get("properties", {})
            detail = "heritage feature returned" if ok else "schema drift or no feature"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )
