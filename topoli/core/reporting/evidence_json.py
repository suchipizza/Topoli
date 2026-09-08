"""Layer 2 — ``./reports/<municipality>-<parcel>/evidence.json`` and ``raw/`` (PRD §3.5).

``evidence.json`` is the ``AuditResult`` (every finding, shown or not, coverage, timings, parser
versions). ``raw/<adapter_id>.json`` holds the records each adapter fetched, exactly as received.
``geometry.geojson`` holds the parcel outline and building points in **WGS84** (for GIS tools)
with the LV95 copies in ``properties``. Re-rendering (``topoli render``) needs only these files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from topoli.core.adapters import Record
from topoli.core.evidence import AuditResult

REPORTS_ROOT = Path("reports")


def report_dir(result: AuditResult, root: Path | None = None) -> Path:
    parcel = result.parcels[0] if result.parcels else None
    slug = parcel.slug if parcel else result.site.id
    return (root or REPORTS_ROOT) / slug


def write_evidence(
    result: AuditResult, records: dict[str, list[Record]] | None = None, *, root: Path | None = None
) -> Path:
    out = report_dir(result, root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "evidence.json").write_text(
        result.model_dump_json(by_alias=True, indent=1), encoding="utf-8"
    )
    raw = out / "raw"
    raw.mkdir(exist_ok=True)
    for adapter_id, recs in (records or {}).items():
        name = adapter_id.replace("/", "__") + ".json"
        (raw / name).write_text(
            json.dumps([r.model_dump(mode="json") for r in recs], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    (out / "geometry.geojson").write_text(
        json.dumps(geometry_collection(result), ensure_ascii=False), encoding="utf-8"
    )
    return out


def load_evidence(path: Path) -> AuditResult:
    path = path / "evidence.json" if path.is_dir() else path
    return AuditResult.model_validate_json(path.read_text(encoding="utf-8"))


def geometry_collection(result: AuditResult) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for p in result.parcels:
        if p.geometry_wgs84:
            features.append(
                {
                    "type": "Feature",
                    "geometry": p.geometry_wgs84,
                    "properties": {
                        "kind": "parcel",
                        "local_id": p.local_id,
                        "egrid": p.national_id,
                        "area_m2": p.area_m2,
                        "geometry_lv95": p.geometry_lv95,
                    },
                }
            )
    for b in result.buildings:
        if b.geometry_wgs84:
            features.append(
                {
                    "type": "Feature",
                    "geometry": b.geometry_wgs84,
                    "properties": {
                        "kind": "building",
                        "egid": b.id,
                        "floors": b.floors,
                        "footprint_m2": b.footprint_m2,
                        "geometry_lv95": b.geometry_lv95,
                    },
                }
            )
    for e in result.events:
        if e.location:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [e.location.lon, e.location.lat]},
                    "properties": {
                        "kind": "event",
                        "id": e.id,
                        "type": e.type,
                        "date": e.publication_date.isoformat(),
                        "distance_m": e.distance_m,
                        "east": e.location.east,
                        "north": e.location.north,
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}
