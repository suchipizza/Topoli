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
from topoli.core.domain import (
    Building,
    Category,
    ConstructionEvent,
    Finding,
    Parcel,
    Regulation,
    Site,
)
from topoli.core.evidence import CoverageEntry, Timing, validate_all
from topoli.core.scoring.coverage import coverage_entry
from topoli.core.scoring.potential import PotentialResult, compute_potential
from topoli.countries.ch.federal.buildings import get_buildings
from topoli.countries.ch.federal.findings import make_finding, unknown_finding
from topoli.countries.ch.federal.geocode import resolve_address
from topoli.countries.ch.federal.parcel import ParcelNotFoundError, get_parcel
from topoli.countries.ch.zh.regulation.adapter import NotContributedError, RegulationAdapter

log = logging.getLogger("topoli.pipeline")

_CATEGORY_OF: dict[str, Category] = {
    "ch/zh/zoning": "zoning",
    "ch/zh/regulation": "zoning",
    "ch/zh/heritage": "heritage",
    "ch/zh/construction_events": "activity",
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
    regulations: list[Regulation] = field(default_factory=list)
    potential: PotentialResult | None = None
    events: list[ConstructionEvent] = field(default_factory=list)


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


def _run_one(run: LayerRun, spec: AdapterSpec) -> list[Record]:
    """Run one adapter into ``run``; never raise. Returns the records (possibly empty)."""
    adapter = spec.adapter
    ctx = run.ctx
    where = ctx.site.jurisdiction.municipality or ctx.site.jurisdiction.canton or "CH"
    t0 = time.perf_counter()
    records: list[Record] = []
    category: Category = _CATEGORY_OF.get(adapter.id, "unknown")
    try:
        if spec.needs_parcel and ctx.parcel is None:
            raise LookupError("no parcel geometry")
        records = adapter.fetch(ctx)
        enrich = getattr(adapter, "enrich", None)
        if callable(enrich):
            run.ctx = enrich(records, ctx)
        if isinstance(adapter, RegulationAdapter):
            reg = adapter.regulation(records, run.ctx)
            if reg is not None:
                run.regulations.append(reg)
        events_of = getattr(adapter, "events", None)
        if callable(events_of):
            found, _ = events_of(records, run.ctx)
            run.events.extend(found)
        findings = adapter.to_findings(records, run.ctx)
        run.coverage.append(coverage_entry(adapter.id, records))
        run.findings.extend(validate_all(findings))
    except NotContributedError as exc:
        run.coverage.append(coverage_entry(adapter.id, records, not_contributed=str(exc)))
        run.findings.append(
            unknown_finding(adapter.id, category, what=adapter.id, where=where, reason=str(exc))
        )
    except LookupError as exc:
        run.coverage.append(coverage_entry(adapter.id, records, not_available=str(exc)))
        run.findings.append(
            unknown_finding(adapter.id, category, what=adapter.id, where=where, reason=str(exc))
        )
    except BudgetExceededError as exc:
        run.coverage.append(coverage_entry(adapter.id, records, error=str(exc)))
        run.findings.append(
            unknown_finding(
                adapter.id, category, what=adapter.id, where=where, reason="call budget exhausted"
            )
        )
    except Exception as exc:
        log.warning("layer.failed", extra={"adapter_id": adapter.id, "error": str(exc)})
        run.coverage.append(
            coverage_entry(adapter.id, records, error=f"{type(exc).__name__}: {exc}")
        )
        run.findings.append(
            unknown_finding(
                adapter.id, category, what=adapter.id, where=where, reason=f"{type(exc).__name__}"
            )
        )
    run.records[adapter.id] = records
    run.timings.append(Timing(step=adapter.id, seconds=time.perf_counter() - t0))
    return records


def run_layers(ctx: SiteContext, specs: list[AdapterSpec] | None = None) -> LayerRun:
    """Step 4: run every federal layer adapter; never raise."""
    run = LayerRun(ctx=ctx)
    for spec in specs if specs is not None else all_specs("federal"):
        _run_one(run, spec)
    return run


def run_cantonal(run: LayerRun) -> LayerRun:
    """Steps 5–6: the site's canton adapters (zoning → regulation → heritage), then potential."""
    canton = run.ctx.site.jurisdiction.canton
    specs = [s for s in all_specs("cantonal") if s.adapter.jurisdiction.canton == canton]
    if not specs:
        return run
    for spec in specs:
        _run_one(run, spec)
    run.potential = _potential_finding(run)
    return run


def run_events(run: LayerRun) -> LayerRun:
    """Step 7: construction-event adapters of the site's canton (nearby activity)."""
    canton = run.ctx.site.jurisdiction.canton
    for spec in all_specs("events"):
        if spec.adapter.jurisdiction.canton == canton:
            _run_one(run, spec)
    return run


def _potential_finding(run: LayerRun) -> PotentialResult | None:
    ctx = run.ctx
    if ctx.parcel is None:
        return None
    reg = run.regulations[0] if run.regulations else None
    if reg is None:
        return None
    result = compute_potential(ctx.parcel, ctx.buildings, reg)
    source = reg.source_document
    if not result.determined:
        run.findings.append(
            make_finding(
                finding_id="potential.headroom",
                template_key="potential.undetermined",
                cls="D",
                severity="info",
                category="potential",
                source=source,
                icon="🏗",
                slots={"reason": result.reason, "code": reg.zone_code},
                derivation=result.derivation or None,
            )
        )
        return result
    assert result.utilisation is not None and result.headroom_m2 is not None
    pct = result.utilisation_pct or 0
    template = "potential.headroom" if result.utilisation < 0.8 else "potential.full"
    run.findings.append(
        make_finding(
            finding_id="potential.headroom",
            template_key=template,
            cls="C",
            severity="medium" if template == "potential.headroom" else "info",
            category="potential",
            source=source,
            icon="🏗",
            slots={
                "pct": str(pct),
                "headroom": f"{max(0, result.headroom_m2):.0f}",
                "allowed": f"{result.allowed_floor_area_m2:.0f}",
                "existing": f"{result.existing_floor_area_m2:.0f}",
                "code": reg.zone_code,
            },
            derivation=result.derivation + "\ninputs: " + "; ".join(result.inputs),
            evidence_spans=[
                s for r in reg.rules if r.key == "floor_area_ratio" for s in r.evidence_spans
            ],
            rule_ref="floor_area_ratio",
        )
    )
    return result


def audit_layers(address: str) -> tuple[LayerRun, list[CoverageEntry], list[Timing]]:
    """Convenience: spine + layers for one address (``topoli layers``)."""
    get_client().reset()
    ctx, spine_cov, spine_timings = resolve_spine(address)
    run = run_layers(ctx)
    run_cantonal(run)
    run_events(run)
    return run, spine_cov, spine_timings


__all__ = [
    "LayerRun",
    "Site",
    "audit_layers",
    "resolve_spine",
    "run_cantonal",
    "run_events",
    "run_layers",
]
