"""Coverage bookkeeping: per-adapter status for one audit, the nightly contract-test result,
and the canton coverage table behind the README/website bars (``coverage.json``).

Three tiers per canton (PRD §6.7 "Federal 100%, Zürich x%, …"):

* **federal** — the ten federal adapters; available everywhere except the ÖREB extract,
  which needs the canton to have introduced the cadastre (``OEREB_INTRODUCED``).
* **cantonal** — deep adapters (zoning, regulation, heritage) registered for that canton;
  Phase 1 plans City of Zürich (WO-05). Counted from the registry, so 0 % until they ship.
* **events** — construction-event adapters registered for that canton (WO-06).

A federal adapter whose last nightly contract test failed counts as *degraded* (half weight).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topoli.core.adapters.base import Record
from topoli.core.evidence.report_model import CoverageEntry, CoverageStatus
from topoli.core.i18n.canton_lang import CANTON_LANG
from topoli.paths import repo_root

LAST_RUN_PATH = Path("tests") / "source-contracts" / "last_run.json"
COVERAGE_PATH = Path("coverage.json")

FEDERAL_ADAPTERS = (
    "ch/federal/geocode",
    "ch/federal/parcel",
    "ch/federal/buildings",
    "ch/federal/hazards",
    "ch/federal/noise",
    "ch/federal/contamination",
    "ch/federal/oereb",
    "ch/federal/solar",
    "ch/federal/heritage",
    "ch/federal/terrain",
)
#: Cantons whose ÖREB cadastre web service answered the V2 JSON extract on 2026-09-08
#: (decision 004). Others: status layer says "planned" (TI) or the service errors (GE).
OEREB_INTRODUCED = frozenset(
    {
        "AG",
        "AI",
        "AR",
        "BE",
        "BL",
        "BS",
        "FR",
        "GL",
        "GR",
        "JU",
        "LU",
        "NE",
        "NW",
        "OW",
        "SG",
        "SH",
        "SO",
        "SZ",
        "TG",
        "UR",
        "VD",
        "VS",
        "ZG",
        "ZH",
    }
)
_PLANNED_CANTONAL = 3  # zoning, regulation, heritage — what a "deep" canton ships in Phase 1
_PLANNED_EVENTS = 1


def _registered(tier: str, canton: str) -> list[str]:
    """Adapter ids actually shipped for ``canton`` in ``tier`` (registry, never a wish list)."""
    from topoli.core.adapters.registry import all_specs

    return sorted(
        s.id
        for s in all_specs(tier)  # type: ignore[arg-type]
        if s.adapter.jurisdiction.canton == canton
    )


def coverage_entry(
    adapter_id: str,
    records: list[Record],
    *,
    error: str | None = None,
    not_available: str | None = None,
    not_contributed: str | None = None,
) -> CoverageEntry:
    """Derive the coverage status of one adapter from what it fetched (or failed to)."""
    calls = sum(1 for r in records if not r.from_cache)
    from_cache = bool(records) and all(r.from_cache for r in records)
    status: CoverageStatus
    detail: str | None
    if not_contributed:
        status, detail = "not_contributed", not_contributed
    elif not_available:
        status, detail = "not_available", not_available
    elif error and not records:
        status, detail = "degraded", error
    elif any(r.stale_as_of is not None for r in records):
        oldest = min(r.stale_as_of for r in records if r.stale_as_of is not None)
        status, detail = "degraded", f"served from cache as of {oldest.date().isoformat()}"
    elif error:
        status, detail = "degraded", error
    else:
        status, detail = "ok", None
    return CoverageEntry(
        adapter_id=adapter_id, status=status, detail=detail, calls=calls, from_cache=from_cache
    )


def write_last_run(results: dict[str, dict[str, Any]], path: Path | None = None) -> Path:
    path = path or repo_root() / LAST_RUN_PATH
    payload = {
        "run_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "adapters": results,
        "degraded": sorted(a for a, r in results.items() if not r.get("ok", False)),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def degraded_from_last_run(path: Path | None = None) -> list[str]:
    """Adapter ids whose last nightly contract test failed (→ coverage bar shows *degraded*)."""
    path = path or repo_root() / LAST_RUN_PATH
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return []
    degraded = data.get("degraded", [])
    return [str(a) for a in degraded] if isinstance(degraded, list) else []


def canton_coverage(canton: str, degraded: list[str] | None = None) -> dict[str, Any]:
    degraded = degraded or []
    federal_score = 0.0
    federal: dict[str, str] = {}
    for adapter_id in FEDERAL_ADAPTERS:
        if adapter_id == "ch/federal/oereb" and canton not in OEREB_INTRODUCED:
            federal[adapter_id] = "not_available"
            continue
        if adapter_id in degraded:
            federal[adapter_id] = "degraded"
            federal_score += 0.5
            continue
        federal[adapter_id] = "ok"
        federal_score += 1
    cantonal_ids = _registered("cantonal", canton)
    event_ids = _registered("events", canton)
    return {
        "canton": canton,
        "lang": CANTON_LANG[canton],
        "federal_pct": round(100 * federal_score / len(FEDERAL_ADAPTERS)),
        "cantonal_pct": min(100, round(100 * len(cantonal_ids) / _PLANNED_CANTONAL)),
        "events_pct": min(100, round(100 * len(event_ids) / _PLANNED_EVENTS)),
        "federal": federal,
        "cantonal": list(cantonal_ids),
        "events": list(event_ids),
    }


def build_coverage(degraded: list[str] | None = None) -> dict[str, Any]:
    degraded = degraded_from_last_run() if degraded is None else degraded
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "degraded_adapters": sorted(degraded),
        "cantons": {c: canton_coverage(c, degraded) for c in sorted(CANTON_LANG)},
    }


def write_coverage_json(path: Path | None = None, degraded: list[str] | None = None) -> Path:
    path = path or repo_root() / COVERAGE_PATH
    path.write_text(json.dumps(build_coverage(degraded), indent=2) + "\n", encoding="utf-8")
    return path
