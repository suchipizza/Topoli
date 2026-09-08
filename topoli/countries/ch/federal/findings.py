"""Helpers shared by the federal adapters: sources and localized findings from i18n templates.

Finding texts live in ``i18n/<lang>.json`` under ``finding.<template_key>.{title,consequence,
caveat}``; adapters only choose the template key and provide slot values. FR/DE/IT strings are
written in WO-07; until then ``t()`` falls back to English.
"""

from __future__ import annotations

from typing import Any

from topoli.core.adapters import Record
from topoli.core.domain import (
    LANGS,
    Category,
    EvidenceSpan,
    Finding,
    FindingClass,
    GeometryIntersection,
    Licence,
    LocalizedText,
    Severity,
    Source,
)
from topoli.core.i18n import t


def source_for(
    adapter_id: str, record: Record, *, authority: str, dataset: str, licence: Licence
) -> Source:
    return Source(
        adapter_id=adapter_id,
        authority=authority,
        dataset=dataset,
        licence=licence.id,
        retrieved_at=record.retrieved_at,
        url=record.url,
        stale_as_of=record.stale_as_of,
    )


def localized(template_key: str, part: str, **slots: Any) -> LocalizedText:
    key = f"finding.{template_key}.{part}"
    return LocalizedText(**{lang: t(key, lang, **slots) for lang in LANGS})


def make_finding(
    *,
    finding_id: str,
    template_key: str,
    cls: FindingClass,
    severity: Severity,
    category: Category,
    source: Source,
    icon: str,
    slots: dict[str, Any] | None = None,
    intersection: GeometryIntersection | None = None,
    derivation: str | None = None,
    evidence_spans: list[EvidenceSpan] | None = None,
    rule_ref: str | None = None,
) -> Finding:
    slots = slots or {}
    return Finding.model_validate(
        {
            "id": finding_id,
            "title": localized(template_key, "title", **slots),
            "consequence": localized(template_key, "consequence", **slots),
            "class": cls,
            "severity": severity,
            "category": category,
            "source": source,
            "geometry_intersection": intersection,
            "derivation": derivation,
            "evidence_spans": evidence_spans or [],
            "caveat": localized(template_key, "caveat", **slots),
            "template_key": template_key,
            "slots": slots,
            "icon": icon,
            "rule_ref": rule_ref,
        }
    )


def unknown_finding(
    adapter_id: str, category: Category, *, what: str, where: str, reason: str
) -> Finding:
    """Explicit class-D 'not available' finding (PRD §3.2: partial failure never aborts)."""
    source = Source(
        adapter_id=adapter_id,
        authority="—",
        dataset=what,
        licence="n/a",
        retrieved_at=None,
        url=None,
    )
    return make_finding(
        finding_id=f"unknown.{adapter_id.replace('/', '.')}",
        template_key="unknown.source",
        cls="D",
        severity="info",
        category=category,
        source=source,
        icon="❔",
        slots={"what": what, "where": where, "reason": reason},
    )
