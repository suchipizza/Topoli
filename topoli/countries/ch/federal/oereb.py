"""``ch/federal/oereb`` — public-law restrictions (ÖREB / RDPPF) for the parcel.

Two steps:

1. Availability: ``identify`` on ``ch.swisstopo-vd.stand-oerebkataster`` at the site point →
   ``oereb_status_de`` ("ÖREB-Kataster eingeführt" or "Einführung geplant …"), ``oereb_webservice``
   (the canton's base URL) and ``oereb_extract_url``. Layer maintained by swisstopo (V+D).
2. Extract: the cantonal ÖREB web service, federal directive "ÖREB-Webservice (Aufruf eines
   Auszugs)" V2.0 (https://www.cadastre.ch/de/oereb-webservice):
   ``GET <oereb_webservice>/extract/json/?EGRID=<egrid>&LANG=<lang>``.
   Tested 2026-09-08: ZH, BE, VS answer JSON; GE answers a different JSON dialect (``Item``);
   TI has no cadastre yet. Three key styles are tolerated (``Extract``/``extract``/``Item``,
   ``code``/``Code``); anything else → *degraded* coverage, never an exception.

One finding per concerned theme (class A: as published), carrying the responsible office and
the legal provisions as evidence spans (title, official number, URL). Legal text is **not**
parsed into rules here (WO-05 does that for Zürich only). The noise sensitivity level and
the cantonal polluted-sites cadastre arrive through this adapter as themes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record, SiteContext, get_client
from topoli.core.domain import EvidenceSpan, Finding, GeometryIntersection, Jurisdiction, Severity
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import OEREB_CANTONAL, SWISSTOPO_OEREB_STATUS

ADAPTER_ID = "ch/federal/oereb"
LAYER_STATUS = "ch.swisstopo-vd.stand-oerebkataster"

_HIGH_THEMES = {
    "ch.BelasteteStandorte",
    "ch.Grundwasserschutzzonen",
    "ch.Grundwasserschutzareale",
    "ch.Waldabstandslinien",
    "ch.Planungszonen",
    "ch.BaulinienNationalstrassen",
    "ch.BaulinienEisenbahnanlagen",
}


class OerebNotAvailableError(LookupError):
    """The canton has not introduced the ÖREB cadastre for this municipality."""


class OerebAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = OEREB_CANTONAL
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        site = ctx.site
        status = geoadmin.identify_point(
            self.id,
            LAYER_STATUS,
            site.coordinates.east,
            site.coordinates.north,
            return_geometry=False,
            limit=1,
        )
        records = [status]
        hits = geoadmin.results(status)
        props: dict[str, Any] = hits[0].get("properties", {}) if hits else {}
        if not _introduced(props):
            raise OerebNotAvailableError(str(props.get("oereb_status_de") or "unknown status"))
        egrid = (
            ctx.parcel.national_id
            if ctx.parcel
            else (site.parcel_ids[0] if site.parcel_ids else None)
        )
        base = str(props.get("oereb_webservice") or "").rstrip("/")
        if not egrid or not base:
            raise OerebNotAvailableError("no EGRID or web service URL")
        lang = site.lang_default
        extract = get_client().get_json(
            self.id, f"{base}/extract/json/", {"EGRID": egrid, "LANG": lang}, ttl=self.ttl
        )
        records.append(extract)
        return records

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        if len(records) < 2:
            return []
        extract = records[1]
        ex = _extract_root(extract.payload)
        if ex is None:
            return []
        real_estate = _get(ex, "RealEstate") or {}
        restrictions = _get(real_estate, "RestrictionOnLandownership") or []
        area = _get(real_estate, "LandRegistryArea")
        source = source_for(
            self.id,
            extract,
            authority=_office_name(_get(ex, "PLRCadastreAuthority") or {}) or "ÖREB-Katasterstelle",
            dataset="ÖREB-Kataster extract (GetExtractById, JSON)",
            licence=self.licence,
        )
        findings: list[Finding] = []
        seen: set[str] = set()
        for r in restrictions:
            theme = _get(r, "Theme") or {}
            code = str(_get(theme, "Code") or "")
            legend = _text(_get(r, "LegendText"))
            key = f"{code}|{legend}"
            if key in seen:
                continue
            seen.add(key)
            office = _office_name(_get(r, "ResponsibleOffice") or {})
            spans = []
            for lp in _get(r, "LegalProvisions") or []:
                spans.append(
                    EvidenceSpan(
                        document=_text(_get(lp, "Title")) or "Rechtsvorschrift",
                        article=_text(_get(lp, "OfficialNumber")) or "—",
                        text=legend or _text(_get(lp, "Title")) or code,
                        url=_text(_get(lp, "TextAtWeb")) or None,
                    )
                )
            share = _get(r, "AreaShare")
            pct = _get(r, "PartInPercent")
            inter = None
            if share is not None and pct is not None:
                inter = GeometryIntersection(
                    area_m2=float(share), fraction=min(1.0, float(pct) / 100)
                )
            severity: Severity = "medium" if code in _HIGH_THEMES else "info"
            findings.append(
                make_finding(
                    finding_id=f"oereb.{code}.{len(seen)}",
                    template_key="oereb.theme",
                    cls="A",
                    severity=severity,
                    category="zoning" if "Nutzungsplanung" in code else "environment",
                    source=source,
                    icon="📜",
                    slots={
                        "theme": _text(_get(theme, "Text")) or code,
                        "legend": legend or "—",
                        "office": office or "—",
                        "status": _text(_get(_get(r, "Lawstatus") or {}, "Text")) or "—",
                        "pct": f"{float(pct):.0f}%" if pct is not None else "–",
                    },
                    intersection=inter,
                    evidence_spans=spans,
                )
            )
        if not findings:
            findings.append(
                make_finding(
                    finding_id="oereb.none",
                    template_key="oereb.none",
                    cls="A",
                    severity="info",
                    category="zoning",
                    source=source,
                    icon="📜",
                    slots={"area": str(area or "–")},
                )
            )
        return findings

    def health(self) -> HealthStatus:
        try:
            rec = geoadmin.identify_point(
                self.id, LAYER_STATUS, 2681718.0, 1247636.0, return_geometry=False, limit=1
            )
            hits = geoadmin.results(rec)
            ok = bool(hits) and "oereb_webservice" in hits[0].get("properties", {})
            detail = "status layer answered" if ok else "status layer schema drift"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def status_source(record: Record) -> Any:
    return source_for(
        ADAPTER_ID,
        record,
        authority="Bundesamt für Landestopografie swisstopo",
        dataset=LAYER_STATUS,
        licence=SWISSTOPO_OEREB_STATUS,
    )


def _introduced(props: dict[str, Any]) -> bool:
    status = str(props.get("oereb_status_de") or "").lower()
    return "eingeführt" in status or "introduit" in status


def _extract_root(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    resp = payload.get("GetExtractByIdResponse")
    if isinstance(resp, dict):
        for key in ("Extract", "extract"):
            if isinstance(resp.get(key), dict):
                return dict(resp[key])
    if isinstance(payload.get("Item"), dict):  # Geneva dialect
        return dict(payload["Item"])
    return None


def _get(node: dict[str, Any], key: str) -> Any:
    """Case-tolerant key lookup (``Code``/``code``)."""
    if key in node:
        return node[key]
    lower = key[0].lower() + key[1:]
    if lower in node:
        return node[lower]
    upper = key[0].upper() + key[1:]
    return node.get(upper)


def _text(value: Any) -> str:
    """Localized text lists (``[{"Language": "de", "Text": "…"}]``) or plain strings → str."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("Text") or value.get("text") or "")
    if isinstance(value, list):
        for item in value:
            txt = _text(item)
            if txt:
                return txt
    return ""


def _office_name(office: dict[str, Any]) -> str:
    return _text(_get(office, "Name")) if office else ""
