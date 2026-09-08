"""The deterministic audit pipeline (PRD §3.2). WO-03 ships steps 1–4: spine + federal layers.

Every adapter runs in isolation: an exception becomes a *degraded* coverage entry plus an
explicit class-D "unknown" finding; a ``LookupError`` raised by the adapter (e.g. the ÖREB
cadastre not introduced in that canton) becomes *not_available*. Partial failure never
aborts (PRD §3.2).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from topoli.core.adapters import BudgetExceededError, Record, SiteContext, get_client
from topoli.core.adapters.registry import AdapterSpec, all_specs
from topoli.core.domain import Building, Category, Finding, Parcel, Site
from topoli.core.evidence import CoverageEntry, Timing, validate_all
from topoli.core.scoring.coverage import coverage_entry
from topoli.countries.ch.federal.buildings import get_buildings
from topoli.countries.ch.federal.findings import unknown_finding
from topoli.countries.ch.federal.geocode import resolve_address
from topoli.countries.ch.federal.parcel import ParcelNotFoundError, get_parcel

log = logging.getLogger("topoli.pipeline")

_CATEGORY_OF: dict[str, Category] = {
    "ch/federal/hazards": "hazard",
    "ch/federal/noise": "noise",
    "ch/federal/contamination": "environment",
    "ch/federal/oereb": "zoning",
    "ch/federal/solar": "environment",
    "ch/federal/heritage": "heritage",
    "ch/federal/terrain": "environment",
}


@dataclass
class LayerRun:
    ctx: SiteContext
    findings: list[Finding] = field(default_factory=list)
    coverage: list[CoverageEntry] = field(default_factory=list)
    records: dict[str, list[Record]] = field(default_factory=dict)
    timings: list[Timing] = field(default_factory=list)


def resolve_spine(address: str) -> tuple[SiteContext, list[CoverageEntry], list[Timing]]:
    """Steps 1–3: address → site → parcel → buildings, with coverage and timings."""
    coverage: list[CoverageEntry] = []
    timings: list[Timing] = []

    t0 = time.perf_counter()
    site, geo_records = resolve_address(address)
    timings.append(Timing(step="resolve_address", seconds=time.perf_counter() - t0))
    coverage.append(coverage_entry("ch/federal/geocode", geo_records))

    parcel: Parcel | None = None
    buildings: list[Building] = []
    t0 = time.perf_counter()
    try:
        parcel, parcel_records = get_parcel(site)
        coverage.append(coverage_entry("ch/federal/parcel", parcel_records))
    except ParcelNotFoundError as exc:
        coverage.append(coverage_entry("ch/federal/parcel", [], not_available=str(exc)))
    except Exception as exc:
        log.warning("spine.parcel_failed", extra={"error": str(exc)})
        coverage.append(
            coverage_entry("ch/federal/parcel", [], error=f"{type(exc).__name__}: {exc}")
        )
    timings.append(Timing(step="get_parcel", seconds=time.perf_counter() - t0))

    if parcel is not None:
        t0 = time.perf_counter()
        try:
            buildings, b_records = get_buildings(parcel)
            coverage.append(coverage_entry("ch/federal/buildings", b_records))
        except Exception as exc:
            log.warning("spine.buildings_failed", extra={"error": str(exc)})
            coverage.append(
                coverage_entry("ch/federal/buildings", [], error=f"{type(exc).__name__}: {exc}")
            )
        timings.append(Timing(step="get_buildings", seconds=time.perf_counter() - t0))

    return SiteContext(site=site, parcel=parcel, buildings=buildings), coverage, timings


def run_layers(ctx: SiteContext, specs: list[AdapterSpec] | None = None) -> LayerRun:
    """Step 4: run every federal layer adapter; never raise."""
    run = LayerRun(ctx=ctx)
    where = ctx.site.jurisdiction.canton or "CH"
    for spec in specs if specs is not None else all_specs("federal"):
        adapter = spec.adapter
        t0 = time.perf_counter()
        records: list[Record] = []
        category: Category = _CATEGORY_OF.get(adapter.id, "unknown")
        try:
            if spec.needs_parcel and ctx.parcel is None:
                raise LookupError("no parcel geometry")
            records = adapter.fetch(ctx)
            findings = adapter.to_findings(records, ctx)
            run.coverage.append(coverage_entry(adapter.id, records))
            run.findings.extend(validate_all(findings))
        except LookupError as exc:
            run.coverage.append(coverage_entry(adapter.id, records, not_available=str(exc)))
            run.findings.append(
                unknown_finding(adapter.id, category, what=adapter.id, where=where, reason=str(exc))
            )
        except BudgetExceededError as exc:
            run.coverage.append(coverage_entry(adapter.id, records, error=str(exc)))
            run.findings.append(
                unknown_finding(
                    adapter.id,
                    category,
                    what=adapter.id,
                    where=where,
                    reason="call budget exhausted",
                )
            )
        except Exception as exc:
            log.warning("layer.failed", extra={"adapter_id": adapter.id, "error": str(exc)})
            run.coverage.append(
                coverage_entry(adapter.id, records, error=f"{type(exc).__name__}: {exc}")
            )
            run.findings.append(
                unknown_finding(
                    adapter.id,
                    category,
                    what=adapter.id,
                    where=where,
                    reason=f"{type(exc).__name__}",
                )
            )
        run.records[adapter.id] = records
        run.timings.append(Timing(step=adapter.id, seconds=time.perf_counter() - t0))
    return run


def audit_layers(address: str) -> tuple[LayerRun, list[CoverageEntry], list[Timing]]:
    """Convenience: spine + layers for one address (``topoli layers``)."""
    get_client().reset()
    ctx, spine_cov, spine_timings = resolve_spine(address)
    run = run_layers(ctx)
    return run, spine_cov, spine_timings


__all__ = ["LayerRun", "Site", "audit_layers", "resolve_spine", "run_layers"]
