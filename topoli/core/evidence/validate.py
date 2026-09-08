"""Abstention rules (PRD §3.6, §5) applied to every finding before it is shown.

* Class A/B without ``source.url`` **and** ``source.retrieved_at`` → cloned as class D,
  caveat ``caveat.downgraded_missing_source``.
* A finding that relies on a regulation rule (``rule_ref`` set) but has no evidence span →
  class D, caveat ``caveat.downgraded_missing_span``.
* Two findings from conflicting sources → one class-D finding listing both sources
  (``merge_conflicting``), caveat ``caveat.conflicting_sources``.
* A source served stale from cache keeps its class but gets the ``caveat.stale_as_of`` marker.

Every downgrade emits a structured warning on the ``topoli.evidence`` logger so that
``--stats`` and the regression suite can count them. Nothing here ever *upgrades* a class.
"""

from __future__ import annotations

import logging
from typing import Literal

from topoli.core.domain import LANGS, Finding, LocalizedText
from topoli.core.i18n import fmt_date, t

log = logging.getLogger("topoli.evidence")

DowngradeReason = Literal["missing_source", "missing_span", "conflicting_sources"]

CAVEAT_KEYS: dict[DowngradeReason, str] = {
    "missing_source": "caveat.downgraded_missing_source",
    "missing_span": "caveat.downgraded_missing_span",
    "conflicting_sources": "caveat.conflicting_sources",
}


def _localized(key: str, **slots: object) -> LocalizedText:
    return LocalizedText(**{lang: t(key, lang, **slots) for lang in LANGS})


def _join_caveat(existing: LocalizedText, extra: LocalizedText) -> LocalizedText:
    values = {}
    for lang in LANGS:
        base = existing.get(lang).strip()
        values[lang] = f"{base} {extra.get(lang)}".strip() if base else extra.get(lang)
    return LocalizedText(**values)


def _downgrade(finding: Finding, reason: DowngradeReason, **slots: object) -> Finding:
    log.warning(
        "finding.downgraded",
        extra={
            "finding_id": finding.id,
            "from_class": finding.cls,
            "to_class": "D",
            "reason": reason,
            "adapter_id": finding.source.adapter_id,
        },
    )
    caveat = _join_caveat(finding.caveat, _localized(CAVEAT_KEYS[reason], **slots))
    notes = [*finding.validation_notes, f"downgraded:{reason}:{finding.cls}->D"]
    return finding.model_copy(update={"cls": "D", "caveat": caveat, "validation_notes": notes})


def validate(finding: Finding) -> Finding:
    """Return the finding as it may be shown: same object if valid, else a class-D clone."""
    result = finding

    if result.cls in ("A", "B") and not result.source.is_complete:
        result = _downgrade(result, "missing_source")

    if result.rule_ref is not None and not result.evidence_spans and result.cls != "D":
        result = _downgrade(result, "missing_span", rule=result.rule_ref)

    stale_as_of = result.source.stale_as_of
    if stale_as_of is not None and "stale" not in result.validation_notes:
        marker = _localized_stale(result)
        result = result.model_copy(
            update={
                "caveat": _join_caveat(result.caveat, marker),
                "validation_notes": [*result.validation_notes, "stale"],
            }
        )
        log.warning(
            "finding.stale",
            extra={
                "finding_id": result.id,
                "adapter_id": result.source.adapter_id,
                "stale_as_of": stale_as_of.isoformat(),
            },
        )

    return result


def _localized_stale(finding: Finding) -> LocalizedText:
    assert finding.source.stale_as_of is not None
    stale = finding.source.stale_as_of
    return LocalizedText(
        **{lang: t("caveat.stale_as_of", lang, date=fmt_date(stale, lang)) for lang in LANGS}
    )


def validate_all(findings: list[Finding]) -> list[Finding]:
    return [validate(f) for f in findings]


def merge_conflicting(primary: Finding, other: Finding) -> Finding:
    """Two sources disagree about the same thing → one class-D finding naming both.

    The primary finding's texts are kept; ``other.source`` is added to ``alternatives`` and
    the conflict caveat names both datasets. Never pick one silently.
    """
    merged = primary.model_copy(
        update={
            "alternatives": [*primary.alternatives, other.source, *other.alternatives],
        }
    )
    return _downgrade(
        merged,
        "conflicting_sources",
        source_a=f"{primary.source.authority} – {primary.source.dataset}",
        source_b=f"{other.source.authority} – {other.source.dataset}",
    )
