"""Layer 1 — the 18-section professional audit (PRD §3.4) assembled from an audit run.

Every section is rendered only when data exists; otherwise it carries the localized
"not available — help add it" stub and the coverage reason. Each finding shows its class badge
and a "why" expander (source row); section 18 lists one source row per claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from topoli.core.domain import Finding, Lang
from topoli.core.evidence import AuditResult, CoverageEntry
from topoli.core.i18n import fmt_area, fmt_date, t

SECTION_CATEGORIES: dict[int, tuple[str, ...]] = {
    4: ("zoning.",),
    5: ("regulation.",),
    6: ("potential.",),
    7: ("oereb.",),
    8: ("hazard.",),
    9: ("contamination.",),
    10: ("noise.",),
    11: ("heritage.",),
    12: ("terrain.",),
    13: ("solar.",),
    14: ("activity.",),
}
SECTION_ADAPTERS: dict[int, tuple[str, ...]] = {
    1: ("ch/federal/geocode",),
    2: ("ch/federal/buildings",),
    3: ("ch/federal/parcel",),
    4: ("ch/zh/zoning",),
    5: ("ch/zh/regulation",),
    6: ("ch/zh/regulation",),
    7: ("ch/federal/oereb",),
    8: ("ch/federal/hazards",),
    9: ("ch/federal/contamination",),
    10: ("ch/federal/noise",),
    11: ("ch/federal/heritage", "ch/zh/heritage"),
    12: ("ch/federal/terrain",),
    13: ("ch/federal/solar",),
    14: ("ch/zh/construction_events",),
}


@dataclass
class SourceRow:
    dataset: str
    authority: str
    licence: str
    retrieved_at: str
    url: str
    finding_id: str


@dataclass
class Section:
    number: int
    title: str
    available: bool
    stub: str | None = None
    findings: list[Finding] = field(default_factory=list)
    facts: list[tuple[str, str]] = field(default_factory=list)
    text: list[str] = field(default_factory=list)
    coverage: list[CoverageEntry] = field(default_factory=list)


@dataclass
class Layer1:
    lang: Lang
    sections: list[Section]
    sources: list[SourceRow]
    class_counts: dict[str, int]


def _by_prefix(findings: list[Finding], prefixes: tuple[str, ...]) -> list[Finding]:
    return [f for f in findings if any(f.id.startswith(p) for p in prefixes)]


def _coverage(result: AuditResult, adapter_ids: tuple[str, ...]) -> list[CoverageEntry]:
    return [c for c in result.coverage if c.adapter_id in adapter_ids]


def assemble(  # noqa: PLR0915
    result: AuditResult, lang: Lang, layer0: list[Finding] | None = None
) -> Layer1:
    site = result.site
    parcel = result.parcels[0] if result.parcels else None
    sections: list[Section] = []
    stub = t("layer1.not_available", lang)

    def section(number: int, **kw: Any) -> Section:
        s = Section(number=number, title=t(f"section.{number}", lang), available=True, **kw)
        s.coverage = _coverage(result, SECTION_ADAPTERS.get(number, ()))
        if number in SECTION_CATEGORIES:
            s.findings = _by_prefix(result.findings, SECTION_CATEGORIES[number])
            if not s.findings or all(f.id.startswith("unknown.") for f in s.findings):
                s.available = False
                s.stub = stub
        return s

    identity = section(1)
    identity.facts = [
        ("address", site.address),
        (
            "municipality",
            f"{site.jurisdiction.municipality or '—'} ({site.jurisdiction.bfs_number or '—'})",
        ),
        ("canton", site.jurisdiction.canton or "—"),
        ("egid", site.egid or "—"),
        ("parcel", parcel.local_id if parcel else "—"),
        ("egrid", parcel.national_id if parcel and parcel.national_id else "—"),
    ]
    sections.append(identity)

    buildings = section(2)
    buildings.available = bool(result.buildings)
    buildings.stub = None if result.buildings else t("layer1.no_data", lang)
    for b in result.buildings:
        buildings.facts.append(
            (
                b.id,
                " · ".join(
                    p
                    for p in (
                        f"{b.floors} {t('unit.floors', lang)}" if b.floors is not None else None,
                        fmt_area(b.footprint_m2, lang) if b.footprint_m2 is not None else None,
                        str(b.year) if b.year else None,
                        b.use,
                        b.energy,
                    )
                    if p
                ),
            )
        )
    sections.append(buildings)

    parcel_section = section(3)
    parcel_section.available = parcel is not None
    if parcel is not None:
        parcel_section.facts = [
            ("area", fmt_area(parcel.area_m2, lang) if parcel.area_m2 else "—"),
            ("zone", f"{parcel.zoning_code or '—'} {parcel.zoning_name or ''}".strip()),
            ("neighbours", ", ".join(parcel.adjacent_parcel_ids) or "—"),
        ]
    else:
        parcel_section.stub = t("layer1.no_data", lang)
    sections.append(parcel_section)

    for n in range(4, 15):
        s = section(n)
        if n == 5 and result.regulations:
            reg = result.regulations[0]
            s.facts = [
                (
                    r.key,
                    f"{r.value} {r.unit or ''} — {r.evidence_spans[0].article}: "
                    f"«{r.evidence_spans[0].text[:120]}»",
                )
                for r in reg.rules
            ]
            if reg.unresolved:
                s.text.append(", ".join(reg.unresolved))
        if n == 14 and result.events:
            s.facts = [
                (
                    e.publication_date.isoformat(),
                    f"{e.distance_m:.0f} m · {e.type} · {e.description[:100]}",
                )
                for e in result.events
            ]
        sections.append(s)

    unknowns = section(15)
    unknowns.available = True
    unknowns.stub = None
    unknowns.findings = [f for f in result.findings if f.cls == "D"]
    unknowns.coverage = [c for c in result.coverage if c.status != "ok"]
    sections.append(unknowns)

    summary = section(16)
    summary.available = True
    summary.stub = None
    summary.text = [t("layer1.decision_intro", lang)] + [
        f"[{f.cls}] {f.title.get(lang)} {f.consequence.get(lang)}"
        for f in (layer0 or result.findings[:5])
    ]
    sections.append(summary)

    checks = section(17)
    checks.available = True
    checks.stub = None
    checks.text = [t("layer1.checks_intro", lang)] + [
        t(f"layer1.check_{k}", lang)
        for k in ("architect", "planning", "heritage", "hazard", "notary", "engineer")
    ]
    sections.append(checks)

    rows: list[SourceRow] = []
    seen: set[tuple[str, str]] = set()
    for f in result.findings:
        key = (f.source.dataset, f.source.url or "")
        if key in seen or not f.source.url:
            continue
        seen.add(key)
        rows.append(
            SourceRow(
                dataset=f.source.dataset,
                authority=f.source.authority,
                licence=f.source.licence,
                retrieved_at=fmt_date(f.source.retrieved_at, lang)
                if f.source.retrieved_at
                else "—",
                url=f.source.url,
                finding_id=f.id,
            )
        )
    sources = section(18)
    sources.available = bool(rows)
    sources.stub = None if rows else t("layer1.no_data", lang)
    sections.append(sources)

    return Layer1(lang=lang, sections=sections, sources=rows, class_counts=result.class_counts())
