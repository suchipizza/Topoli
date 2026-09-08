"""Coverage bookkeeping: per-adapter status for one audit and the nightly contract-test result.

WO-04 ships the pieces the cache/contract plumbing needs; WO-03 adds the canton percentages and
``coverage.json`` generation on top of :func:`coverage_entry` and :func:`degraded_from_last_run`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topoli.core.adapters.base import Record
from topoli.core.evidence.report_model import CoverageEntry, CoverageStatus
from topoli.paths import repo_root

LAST_RUN_PATH = Path("tests") / "source-contracts" / "last_run.json"


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
