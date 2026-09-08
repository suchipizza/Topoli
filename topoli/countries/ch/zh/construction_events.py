"""``ch/zh/construction_events`` — building publications near the site (Canton of Zürich).

Sources (read 2026-09-08, decision 007):

* **Baugesuche im Kanton Zürich** — Statistisches Amt / FK OGD, opendata.swiss
  (https://opendata.swiss/de/dataset/baugesuche-im-kanton-zurich, terms "Freie Nutzung"):
  ``GET https://daten.statistik.zh.ch/ogd/daten/ressourcen/KTZH_00002982_00006183.csv`` — every
  building publication of the cantonal Amtsblatt (rubric ``BP-ZH01``) since June 2022 with
  publication date, objection deadline, municipality (``bfs_nr``), project location
  (street, number, zip), cadastre numbers (``districtCadastre_relation_cadastre_raw``), project
  description, and anonymised applicant / project-author metadata (legal form, town). Updated
  daily; one download per day (cache TTL 24 h), reduced at fetch time to the columns used and
  the last 400 days, gzipped (see :func:`reduce_csv`).
* **Parcel-number positions** — Canton ZH OGD WFS
  ``ms:ogd-0404_arv_basis_avzh_liegenschaften_pos_p`` (MOpublic RealEstate_PosNumber: one point
  per parcel with ``nummer`` and ``bfsnr``), one GetFeature over the search radius. Publications
  carry no coordinates; matching their cadastre numbers to these points locates each project
  without geocoding (two calls per audit).
* Each event links to the Amtsblattportal API record
  ``https://www.amtsblattportal.ch/api/v1/publications/<id>`` (freely accessible; the signed PDF
  is the legally binding version) and to the portal page.

Only publications whose cadastre numbers resolve to a parcel point inside the radius are
returned; the count of unresolved publications in the municipality is reported in the
derivation. No value estimates (PRD §4.2).
"""

from __future__ import annotations

import base64
import csv
import gzip
import io
import json
import math
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record, SiteContext, get_client
from topoli.core.domain import ConstructionEvent, Coordinates, Finding, Jurisdiction
from topoli.core.geospatial import lv95_to_wgs84
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.zh import wfs
from topoli.countries.ch.zh.licences import ZH_BAUGESUCHE

ADAPTER_ID = "ch/zh/construction_events"
CSV_URL = "https://daten.statistik.zh.ch/ogd/daten/ressourcen/KTZH_00002982_00006183.csv"
PORTAL_API = "https://www.amtsblattportal.ch/api/v1/publications/{id}"
PORTAL_PAGE = "https://amtsblatt.zh.ch/#!/search/publications/detail/{id}"
TYPE_PARCEL_POS = "ms:ogd-0404_arv_basis_avzh_liegenschaften_pos_p"
DEFAULT_RADIUS_M = 500.0
DEFAULT_SINCE_MONTHS = 12
KEEP_DAYS = 400

COLUMNS = (
    "id",
    "publicationNumber",
    "publicationDate",
    "entryDeadline",
    "expirationDate",
    "bfs_nr",
    "municipality_name",
    "projectDescription",
    "projectLocation_address_street",
    "projectLocation_address_houseNumber",
    "projectLocation_address_swissZipCode",
    "projectLocation_address_town",
    "districtCadastre_relation_cadastre_raw",
    "buildingContractor_legalEntity_selectType",
    "buildingContractor_company_legalForm_de",
    "buildingContractor_company_address_town",
    "projectFramer_selectType",
    "projectFramer_legalEntity_selectType",
    "projectFramer_company_legalForm_de",
    "projectFramer_company_address_town",
)

_TYPE_RULES: tuple[tuple[str, str], ...] = (
    (r"\babbruch|\brückbau|\babriss", "demolition"),
    (r"\bneubau|\bersatzneubau|\bneuerstellung", "new_building"),
    (r"aufstockung|anbau|erweiterung|ausbau|dachausbau", "extension"),
    (r"umbau|sanierung|renovation|instandsetzung|umnutzung|nutzungsänderung", "conversion"),
    (r"wärmepumpe|solaranlage|photovoltaik|pv-anlage|heizung|fernwärme", "energy"),
    (r"reklame|werbe|beschriftung", "signage"),
    (r"antenne|mobilfunk", "antenna"),
)
_PARCEL_TOKEN = re.compile(r"\b([A-Z]{2}\d{1,6}|\d{1,6})\b")


def reduce_csv(data: bytes) -> dict[str, Any]:
    """Keep the used columns and the last ``KEEP_DAYS`` days; gzip+base64 the result."""
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    cutoff = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(COLUMNS))
    writer.writeheader()
    kept = 0
    for row in reader:
        if (row.get("publicationDate") or "") < cutoff:
            continue
        writer.writerow({k: row.get(k, "") for k in COLUMNS})
        kept += 1
    blob = gzip.compress(out.getvalue().encode("utf-8"))
    return {
        "rows": kept,
        "cutoff": cutoff,
        "columns": list(COLUMNS),
        "csv_gzip_base64": base64.b64encode(blob).decode("ascii"),
    }


def csv_rows(record: Record) -> list[dict[str, str]]:
    payload = record.payload
    if not isinstance(payload, dict) or "csv_gzip_base64" not in payload:
        return []
    text = gzip.decompress(base64.b64decode(payload["csv_gzip_base64"])).decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def reduce_points(data: bytes) -> dict[str, Any]:
    """WFS GeoJSON → ``{"points": [[nummer, bfsnr, x, y], …]}`` (a few % of the raw size)."""
    payload = json.loads(data.decode("utf-8"))
    points = []
    for f in payload.get("features", []):
        p = f.get("properties", {})
        coords = (f.get("geometry") or {}).get("coordinates") or []
        if p.get("nummer") and len(coords) >= 2:
            points.append(
                [str(p["nummer"]), int(p.get("bfsnr") or 0), float(coords[0]), float(coords[1])]
            )
    return {"points": points, "count": len(points)}


def parcel_tokens(raw: str) -> list[str]:
    """``'3147, 3148 und 4620'`` → ``['3147', '3148', '4620']``; ``'AU6979'`` → ``['AU6979']``."""
    return [t for t in _PARCEL_TOKEN.findall(raw or "") if t]


def classify(description: str) -> str:
    text = (description or "").lower()
    for pattern, kind in _TYPE_RULES:
        if re.search(pattern, text):
            return kind
    return "other"


def _party(select_type: str, legal_form: str, town: str) -> str | None:
    if select_type == "person":
        return "Privatperson"
    if select_type == "company" or legal_form:
        return " · ".join(p for p in (legal_form or "Unternehmen", town) if p)
    return None


class ConstructionEventsAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH", canton="ZH")
    licence = ZH_BAUGESUCHE
    ttl = timedelta(hours=24)
    radius_m = DEFAULT_RADIUS_M
    since_months = DEFAULT_SINCE_MONTHS

    def fetch(self, ctx: SiteContext) -> list[Record]:
        east, north = ctx.site.coordinates.east, ctx.site.coordinates.north
        r = self.radius_m
        publications = get_client().get_bytes(self.id, CSV_URL, None, wrap=reduce_csv, ttl=self.ttl)
        params: dict[str, Any] = {
            "SERVICE": "WFS",
            "REQUEST": "GetFeature",
            "VERSION": "2.0.0",
            "TYPENAMES": TYPE_PARCEL_POS,
            "SRSNAME": "EPSG:2056",
            "OUTPUTFORMAT": "application/json; subtype=geojson",
            "BBOX": f"{east - r:.1f},{north - r:.1f},{east + r:.1f},{north + r:.1f},EPSG:2056",
            "COUNT": 5000,
        }
        points = get_client().get_bytes(
            self.id, wfs.WFS_URL, params, wrap=reduce_points, ttl=timedelta(days=30)
        )
        return [publications, points]

    def events(
        self, records: list[Record], ctx: SiteContext
    ) -> tuple[list[ConstructionEvent], dict[str, Any]]:
        """Normalized events within the radius and since-window, plus matching statistics."""
        if len(records) < 2:
            return [], {}
        pub_rec, pts_rec = records[0], records[1]
        as_of = pub_rec.retrieved_at.date()
        since = _months_ago(as_of, self.since_months)
        bfs = ctx.site.jurisdiction.bfs_number
        east, north = ctx.site.coordinates.east, ctx.site.coordinates.north
        points = {
            str(p[0]): (float(p[2]), float(p[3]))
            for p in (pts_rec.payload or {}).get("points", [])
            if bfs is None or int(p[1]) == bfs
        }
        source = source_for(
            self.id,
            pub_rec,
            authority="Kanton Zürich, Statistisches Amt (FK OGD) / Amtsblatt",
            dataset="Baugesuche im Kanton Zürich (BP-ZH01)",
            licence=self.licence,
        )
        by_id: dict[str, ConstructionEvent] = {}
        rows_municipality = 0
        without_parcel = 0
        for row in csv_rows(pub_rec):
            if bfs is not None and row.get("bfs_nr") != str(bfs):
                continue
            pub_date = _parse_date(row.get("publicationDate"))
            if pub_date is None or pub_date < since:
                continue
            rows_municipality += 1
            tokens = parcel_tokens(row.get("districtCadastre_relation_cadastre_raw", ""))
            if not tokens:
                without_parcel += 1
                continue
            located = [(t, points[t]) for t in tokens if t in points]
            if not located:
                continue  # parcel outside the search window (points cover the radius only)
            token, (x, y) = min(
                located, key=lambda tp: math.hypot(tp[1][0] - east, tp[1][1] - north)
            )
            distance = math.hypot(x - east, y - north)
            if distance > self.radius_m:
                continue
            pid = row["id"]
            if pid in by_id and (by_id[pid].distance_m or 0) <= distance:
                continue
            lon, lat = lv95_to_wgs84(x, y)
            address = " ".join(
                p
                for p in (
                    row.get("projectLocation_address_street"),
                    row.get("projectLocation_address_houseNumber"),
                )
                if p
            )
            description = row.get("projectDescription") or ""
            by_id[pid] = ConstructionEvent(
                id=row.get("publicationNumber") or pid,
                location=Coordinates(lon=lon, lat=lat, east=x, north=y),
                parcels=[token],
                type=classify(description),
                description=f"{description} — {address}".strip(" —") if address else description,
                applicant=_party(
                    row.get("buildingContractor_legalEntity_selectType", ""),
                    row.get("buildingContractor_company_legalForm_de", ""),
                    row.get("buildingContractor_company_address_town", ""),
                ),
                project_author=_party(
                    row.get("projectFramer_legalEntity_selectType", ""),
                    row.get("projectFramer_company_legalForm_de", ""),
                    row.get("projectFramer_company_address_town", ""),
                ),
                publication_date=pub_date,
                status="published"
                if (_parse_date(row.get("entryDeadline")) or as_of) < as_of
                else "objection_period",
                distance_m=round(distance, 1),
                sources=[
                    source.model_copy(update={"url": PORTAL_API.format(id=pid)}),
                ],
            )
        events = sorted(by_id.values(), key=lambda e: (e.publication_date, e.id), reverse=True)
        stats: dict[str, Any] = {
            "rows_municipality": rows_municipality,
            "without_parcel_number": without_parcel,
            "as_of": as_of.isoformat(),
            "since": since.isoformat(),
        }
        return events, stats

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        events, stats = self.events(records, ctx)
        if not records:
            return []
        source = source_for(
            self.id,
            records[0],
            authority="Kanton Zürich, Statistisches Amt (FK OGD) / Amtsblatt",
            dataset="Baugesuche im Kanton Zürich (BP-ZH01)",
            licence=self.licence,
        )
        n = len(events)
        nearest = events[0] if events else None
        kinds = sorted({e.type for e in events})
        derivation = (
            f"{stats.get('rows_municipality', 0)} publications in the municipality since "
            f"{stats.get('since')} (as of {stats.get('as_of')}); {n} located within "
            f"{self.radius_m:.0f} m via cadastre numbers; {stats.get('without_parcel_number', 0)} "
            "publications without a parcel number could not be located."
        )
        return [
            make_finding(
                finding_id="activity.nearby",
                template_key="activity.n" if n else "activity.none",
                cls="B",
                severity="info",
                category="activity",
                source=source,
                icon="🏘",
                slots={
                    "n": str(n),
                    "radius": f"{self.radius_m:.0f}",
                    "months": str(self.since_months),
                    "kinds": ", ".join(kinds) or "–",
                    "nearest": (nearest.description[:80] if nearest else "–"),
                    "nearest_m": f"{nearest.distance_m:.0f}"
                    if nearest and nearest.distance_m is not None
                    else "–",
                },
                derivation=derivation,
            )
        ]

    def health(self) -> HealthStatus:
        try:
            rec = get_client().get_bytes(self.id, CSV_URL, None, wrap=reduce_csv, ttl=timedelta(0))
            rows = rec.payload.get("rows", 0) if isinstance(rec.payload, dict) else 0
            ok = rows > 100 and set(COLUMNS) <= set(rec.payload.get("columns", []))
            detail = (
                f"{rows} publications in the last {KEEP_DAYS} days"
                if ok
                else "schema drift or empty CSV"
            )
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _months_ago(when: date, months: int) -> date:
    month = when.month - months
    year = when.year
    while month <= 0:
        month += 12
        year -= 1
    day = min(when.day, 28)
    return date(year, month, day)


def portal_page(event: ConstructionEvent) -> str:
    pid = event.sources[0].url.rsplit("/", 1)[-1] if event.sources and event.sources[0].url else ""
    return PORTAL_PAGE.format(id=pid)


__all__ = [
    "ConstructionEventsAdapter",
    "classify",
    "parcel_tokens",
    "portal_page",
    "reduce_csv",
    "reduce_points",
]
