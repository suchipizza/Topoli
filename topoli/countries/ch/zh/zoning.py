"""``ch/zh/zoning`` — zone code and name for any parcel in the Canton of Zürich.

Source: cantonal WFS type ``ms:ogd-0156_arv_basis_np_gn_zonenflaeche_f`` (see :mod:`wfs`),
one GetFeature with a 1 m box around the parcel's interior point. Class A: the zone as published
by the canton in the simplified ÖREB data model, with the municipal decision (``festsetzung``)
and cantonal approval (``genehmigung``) references as the plan reference.

The adapter also *enriches* the context: ``parcel.zoning_code`` / ``zoning_name`` are set so the
regulation and potential steps can use them.
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

ADAPTER_ID = "ch/zh/zoning"

#: Plain-language family per cantonal abbreviation (``typ_zh_abkuerzung``); slot ``family``.
FAMILIES: dict[str, str] = {
    "W": "residential",
    "Q": "quarter_preservation",
    "K": "core",
    "Z": "centre",
    "IG": "industrial",
    "I": "industrial",
    "Oe": "public",
    "OeB": "public",
    "F": "open_space",
    "E": "recreation",
    "L": "agricultural",
    "R": "reserve",
}


class ZoningAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH", canton="ZH")
    licence = ZH_OGD
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        east, north = _point(ctx)
        return [
            wfs.get_features(
                self.id, wfs.TYPE_ZONING, (east - 1, north - 1, east + 1, north + 1), count=5
            )
        ]

    def enrich(self, records: list[Record], ctx: SiteContext) -> SiteContext:
        props = zone_props(records)
        if props is None or ctx.parcel is None:
            return ctx
        parcel = ctx.parcel.model_copy(
            update={
                "zoning_code": str(props.get("typ_gde_abkuerzung") or ""),
                "zoning_name": str(props.get("typ_gde_bezeichnung") or ""),
            }
        )
        return ctx.model_copy(update={"parcel": parcel})

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if not records:
            return []
        rec = records[0]
        props = zone_props(records)
        source = source_for(
            self.id,
            rec,
            authority="Kanton Zürich, Amt für Raumentwicklung (ARE)",
            dataset=wfs.TYPE_ZONING,
            licence=self.licence,
        )
        if props is None:
            return [
                make_finding(
                    finding_id="zoning.zone",
                    template_key="zoning.none",
                    cls="A",
                    severity="info",
                    category="zoning",
                    source=source,
                    icon="🗺",
                )
            ]
        code = str(props.get("typ_gde_abkuerzung") or "")
        family = FAMILIES.get(str(props.get("typ_zh_abkuerzung") or ""), "other")
        floors = props.get("vollgeschosse_max")
        height = props.get("gebaeudehoehe_max")
        template = f"zoning.{family}" if floors else f"zoning.{family}_nofloors"
        return [
            make_finding(
                finding_id="zoning.zone",
                template_key=template,
                cls="A",
                severity="info",
                category="zoning",
                source=source,
                icon="🗺",
                slots={
                    "code": code,
                    "name": str(
                        props.get("typ_gde_bezeichnung") or props.get("typ_zh_bezeichnung") or ""
                    ),
                    "family": family,
                    "floors": str(floors) if floors is not None else "–",
                    "height": f"{float(height):g}" if height is not None else "–",
                    "wohnanteil": str(props.get("wohnanteil_min") or "–"),
                    "municipality": str(props.get("typ_gemeindename") or ""),
                    "plan_ref": plan_reference(props),
                },
            )
        ]

    def health(self) -> HealthStatus:
        try:
            rec = wfs.get_features(
                self.id,
                wfs.TYPE_ZONING,
                (2681685.6, 1247621.3, 2681687.6, 1247623.3),
                count=1,
                ttl=timedelta(0),
            )
            props = zone_props([rec])
            ok = props is not None and "typ_gde_abkuerzung" in props
            detail = "zone feature returned" if ok else "schema drift or no feature"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def zone_props(records: list[Record]) -> dict[str, Any] | None:
    """The in-force zone feature's properties (prefers ``rechtsstatus == inKraft``)."""
    if not records:
        return None
    feats = wfs.features(records[0])
    in_force = [f for f in feats if f.get("properties", {}).get("rechtsstatus") == "inKraft"]
    chosen = (in_force or feats)[:1]
    return dict(chosen[0].get("properties", {})) if chosen else None


def plan_reference(props: dict[str, Any]) -> str:
    parts = []
    if props.get("festsetzungsdatum"):
        date = str(props["festsetzungsdatum"])[:10]
        parts.append(f"Festsetzung {date} Nr. {props.get('festsetzungsnr') or '–'}")
    if props.get("genehmigungsdatum"):
        date = str(props["genehmigungsdatum"])[:10]
        who = props.get("genehmigung") or ""
        parts.append(f"Genehmigung {who} {date} Nr. {props.get('genehmigungsnr') or '–'}")
    return "; ".join(parts) or str(props.get("identifikator") or "")


def _point(ctx: SiteContext) -> tuple[float, float]:
    geom = ctx.parcel_geometry
    if geom is None:
        return ctx.site.coordinates.east, ctx.site.coordinates.north
    p = from_geojson(geom).representative_point()
    return round(float(p.x), 1), round(float(p.y), 1)
