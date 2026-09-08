"""``ch/federal/geocode`` — address / parcel / coordinates → ``Site``.

Endpoints (see :mod:`topoli.countries.ch.federal.geoadmin` for the docs read):

1. ``SearchServer?type=locations&origins=address|parcel`` for free text.
   Request used: ``searchText=<text>&type=locations&sr=2056&limit=10&origins=address``.
2. ``identify`` on ``ch.bfs.gebaeude_wohnungs_register`` at the resolved point, tolerance 5 px,
   to obtain the authoritative municipality (``ggdename``/``ggdenr``), canton (``gdekt``),
   EGID and the parcel the entrance belongs to (``egrid``/``lparz``).

Input forms accepted (PRD §3.1): free-form postal address; ``Parcel <municipality> <number>``
(also ``Parzelle``/``parcelle``/``particella``); ``lat,lon`` (WGS84) or ``east,north`` (LV95).
Typo tolerance comes from the service's fuzzy matching; we only *score* the result.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from topoli.core.adapters import HealthStatus, Record
from topoli.core.domain import Coordinates, Finding, Jurisdiction, Lang, Site, Source
from topoli.core.geospatial import lv95_to_wgs84, wgs84_to_lv95
from topoli.core.i18n import canton_lang
from topoli.countries.ch.federal import geoadmin
from topoli.countries.ch.federal.licences import BFS_GWR, SWISSTOPO_SEARCH

ADAPTER_ID = "ch/federal/geocode"

_COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)\s*$")
_PARCEL_RE = re.compile(
    r"^\s*(?:parcel|parzelle|parcelle|particella|grundstück|grundstueck)\s+(.+?)\s+(\S+)\s*$",
    re.IGNORECASE,
)
_POSTCODE_RE = re.compile(r"\b([1-9]\d{3})\b")


class ResolveError(LookupError):
    """The input could not be turned into a Swiss location."""


class GeocodeAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = SWISSTOPO_SEARCH
    ttl = timedelta(days=30)

    def fetch(self, site: Site) -> list[Record]:  # pragma: no cover - resolver is called directly
        return []

    def to_findings(self, records: list[Record], site: Site, lang: Lang) -> list[Finding]:
        return []

    def health(self) -> HealthStatus:
        try:
            record = geoadmin.search_locations(
                self.id, "Bundesplatz 3 3011 Bern", origins="address", limit=1
            )
            ok = bool(geoadmin.results(record))
            detail = "search returned a result" if ok else "search returned no result"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )


def resolve_address(text: str) -> tuple[Site, list[Record]]:
    """Resolve free text to a ``Site``. Returns the site and the raw records used."""
    text = text.strip()
    if not text:
        raise ResolveError("empty address")

    if (m := _COORD_RE.match(text)) is not None:
        east, north = _coords_from_pair(float(m.group(1)), float(m.group(2)))
        return _site_from_point(
            text, east, north, address=None, confidence=0.9, records=[], tolerance=25
        )

    if (m := _PARCEL_RE.match(text)) is not None:
        return _resolve_parcel(text, municipality=m.group(1), number=m.group(2))

    return _resolve_postal(text)


def _coords_from_pair(a: float, b: float) -> tuple[float, float]:
    """Accept ``lat,lon`` (WGS84) or ``east,north`` (LV95) and return LV95."""
    if 45 <= a <= 48 and 5 <= b <= 11:
        return wgs84_to_lv95(b, a)
    if 2_400_000 <= a <= 2_900_000 and 1_000_000 <= b <= 1_400_000:
        return a, b
    raise ResolveError(f"coordinates {a},{b} are not in Switzerland (WGS84 lat,lon or LV95 E,N)")


def _resolve_postal(text: str) -> tuple[Site, list[Record]]:
    record = geoadmin.search_locations(ADAPTER_ID, text, origins="address", limit=10)
    hits = geoadmin.results(record)
    if not hits:
        record = geoadmin.search_locations(ADAPTER_ID, text, limit=10)
        hits = [
            h
            for h in geoadmin.results(record)
            if h.get("attrs", {}).get("origin") in ("address", "parcel", "gg25", "zipcode")
        ]
    if not hits:
        raise ResolveError(f"no location found for {text!r}")
    fuzzy = str(record.payload.get("fuzzy", "")).lower() == "true"
    best, confidence = _pick(text, hits, fuzzy)
    attrs = best["attrs"]
    east, north = float(attrs["y"]), float(attrs["x"])
    address = _strip_html(str(attrs.get("label", "")))
    return _site_from_point(
        text, east, north, address=address, confidence=confidence, records=[record]
    )


def _resolve_parcel(text: str, *, municipality: str, number: str) -> tuple[Site, list[Record]]:
    record = geoadmin.search_locations(
        ADAPTER_ID, f"{municipality} {number}", origins="parcel", limit=10
    )
    hits = geoadmin.results(record)
    if not hits:
        raise ResolveError(f"no parcel {number!r} found in {municipality!r}")
    confidence = 0.95 if len(hits) == 1 else 0.6
    attrs = hits[0]["attrs"]
    east, north = float(attrs["y"]), float(attrs["x"])
    address = _strip_html(str(attrs.get("label", "")))
    # detail looks like "7013 geneve 6621 ch296589536314": <number> <municipality> <bfs> <egrid>
    tokens = str(attrs.get("detail", "")).split()
    egrid = tokens[-1].upper() if tokens and tokens[-1].lower().startswith("ch") else None
    bfs = int(tokens[-2]) if len(tokens) >= 2 and tokens[-2].isdigit() else None
    return _site_from_point(
        text,
        east,
        north,
        address=address,
        confidence=confidence,
        records=[record],
        tolerance=25,
        parcel_hint=(egrid, bfs, number),
    )


def _pick(text: str, hits: list[dict[str, Any]], fuzzy: bool) -> tuple[dict[str, Any], float]:
    """Prefer the candidate matching the postcode / municipality the user typed."""
    wanted_pc = _POSTCODE_RE.search(text)
    words = {w for w in re.findall(r"[a-zà-ÿ]+", text.lower()) if len(w) > 3}
    scored: list[tuple[float, dict[str, Any]]] = []
    for hit in hits:
        detail = str(hit.get("attrs", {}).get("detail", "")).lower()
        score = 0.0
        if wanted_pc and wanted_pc.group(1) in detail:
            score += 2
        score += sum(1 for w in words if w in _fold(detail)) / max(1, len(words))
        scored.append((score, hit))
    scored.sort(key=lambda s: s[0], reverse=True)
    best_score, best = scored[0]
    confidence = 0.95
    if fuzzy:
        confidence -= 0.25
    if wanted_pc and wanted_pc.group(1) not in str(best.get("attrs", {}).get("detail", "")):
        confidence -= 0.2
    if len(scored) > 1 and scored[1][0] == best_score:
        confidence -= 0.1
    return best, round(max(0.1, confidence), 2)


def _distance2(hit: dict[str, Any], east: float, north: float) -> float:
    p = hit.get("properties", {})
    try:
        return (float(p["dkode"]) - east) ** 2 + (float(p["dkodn"]) - north) ** 2
    except (KeyError, TypeError, ValueError):
        return float("inf")


def _fold(s: str) -> str:
    return (
        s.replace("ü", "ue")
        .replace("ö", "oe")
        .replace("ä", "ae")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
    )


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _site_from_point(
    input_text: str,
    east: float,
    north: float,
    *,
    address: str | None,
    confidence: float,
    records: list[Record],
    tolerance: int = 5,
    parcel_hint: tuple[str | None, int | None, str | None] = (None, None, None),
) -> tuple[Site, list[Record]]:
    gwr = geoadmin.identify_point(
        ADAPTER_ID,
        geoadmin.LAYER_GWR,
        east,
        north,
        tolerance=tolerance,
        return_geometry=False,
        limit=5,
    )
    records = [*records, gwr]
    entrances = sorted(geoadmin.results(gwr), key=lambda h: _distance2(h, east, north))
    props: dict[str, Any] = entrances[0]["properties"] if entrances else {}
    hint_egrid, hint_bfs, hint_number = parcel_hint
    canton = props.get("gdekt")
    bfs = hint_bfs or props.get("ggdenr")
    municipality = props.get("ggdename") or (address.split()[0] if address and hint_egrid else None)
    egrid = hint_egrid or props.get("egrid")
    local_parcel = hint_number or props.get("lparz")
    egid = str(props["egid"]) if props.get("egid") is not None else None
    if address is None:
        address = str(props.get("strname_deinr") or "") or f"{east:.0f}, {north:.0f} (LV95)"
        if props.get("dplz4") and municipality:
            address = f"{address}, {props['dplz4']} {municipality}"
    if not entrances and not hint_egrid:
        confidence = round(confidence * 0.7, 2)
    lon, lat = lv95_to_wgs84(east, north)
    site_id = f"{bfs}-{local_parcel}" if bfs and local_parcel else f"e{east:.0f}-n{north:.0f}"
    sources = [
        Source(
            adapter_id=ADAPTER_ID,
            authority="Bundesamt für Landestopografie swisstopo",
            dataset="geo.admin.ch SearchServer (locations)",
            licence=SWISSTOPO_SEARCH.id,
            retrieved_at=r.retrieved_at,
            url=r.url,
        )
        for r in records[:-1]
    ] + [
        Source(
            adapter_id=ADAPTER_ID,
            authority="Bundesamt für Statistik BFS",
            dataset=geoadmin.LAYER_GWR,
            licence=BFS_GWR.id,
            retrieved_at=gwr.retrieved_at,
            url=gwr.url,
        )
    ]
    site = Site(
        id=site_id,
        input_address=input_text,
        address=address,
        coordinates=Coordinates(lon=lon, lat=lat, east=east, north=north),
        jurisdiction=Jurisdiction(
            country="CH",
            canton=str(canton) if canton else None,
            municipality=str(municipality) if municipality else None,
            bfs_number=int(bfs) if bfs is not None else None,
        ),
        parcel_ids=[str(egrid)] if egrid else [],
        egid=egid,
        resolve_confidence=confidence,
        lang_default=canton_lang(str(canton) if canton else None),
        sources=sources,
    )
    return site, records
