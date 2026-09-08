"""The ``Finding`` — the unit of output. Everything a user sees is a finding or derived from one."""

from __future__ import annotations

from typing import Any, Literal, get_args

from pydantic import Field

from topoli.core.domain.common import LocalizedText, StrictModel
from topoli.core.domain.evidence import EvidenceSpan, GeometryIntersection, Source

FindingClass = Literal["A", "B", "C", "D"]
CLASSES: tuple[FindingClass, ...] = get_args(FindingClass)

Severity = Literal["info", "low", "medium", "high"]
SEVERITIES: tuple[Severity, ...] = get_args(Severity)

Category = Literal[
    "potential",
    "hazard",
    "noise",
    "heritage",
    "environment",
    "zoning",
    "activity",
    "identity",
    "unknown",
]
CATEGORIES: tuple[Category, ...] = get_args(Category)


class Finding(StrictModel):
    """One claim with its evidence (PRD §5).

    Four classes (spec §10): **A** official fact · **B** deterministic derived fact ·
    **C** heuristic estimate · **D** professional judgment required.
    ``topoli.core.evidence.validate`` downgrades A/B findings whose source is incomplete.
    """

    id: str = Field(min_length=1)
    title: LocalizedText
    consequence: LocalizedText
    cls: FindingClass = Field(alias="class")
    severity: Severity = "info"
    category: Category
    source: Source
    geometry_intersection: GeometryIntersection | None = None
    derivation: str | None = Field(
        default=None, description="Formula or rule text for class B/C; every input value named"
    )
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    caveat: LocalizedText
    rank_score: float = 0.0

    # --- fields beyond PRD §5, recorded in docs/decisions/002-domain-model.md ---
    template_key: str | None = Field(
        default=None,
        description="Layer-0 template id '(category).(outcome)', e.g. 'hazard.flood.none'",
    )
    slots: dict[str, Any] = Field(
        default_factory=dict, description="Slot values used to fill the localized templates"
    )
    icon: str | None = Field(default=None, description="Emoji shown on layer 0")
    rule_ref: str | None = Field(
        default=None,
        description="Regulation rule this finding relies on; if set, evidence_spans must be set",
    )
    alternatives: list[Source] = Field(
        default_factory=list,
        description="Other sources that conflict with `source`; non-empty only on class D",
    )
    validation_notes: list[str] = Field(
        default_factory=list, description="Machine-readable notes added by validate()"
    )

    def model_dump_json_ready(self) -> dict[str, Any]:
        """Dump with the ``class`` alias so evidence.json matches PRD §5."""
        return self.model_dump(mode="json", by_alias=True)
