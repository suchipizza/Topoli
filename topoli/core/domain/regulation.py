"""Regulation = rule → source document → article → jurisdiction → dates → parser version.

Never store ``max_height = 15`` alone (spec §8): every ``Rule`` carries the spans it was
extracted from and the parser version that extracted it.
"""

from __future__ import annotations

from datetime import date

from pydantic import Field

from topoli.core.domain.common import Jurisdiction, StrictModel
from topoli.core.domain.evidence import EvidenceSpan, Source
from topoli.core.domain.finding import FindingClass


class Rule(StrictModel):
    key: str = Field(description="Stable rule id, e.g. 'ausnuetzungsziffer', 'max_full_floors'")
    value: float | int | str
    unit: str | None = Field(default=None, description="e.g. 'ratio', 'm', 'floors'")
    definition: str | None = Field(
        default=None, description="Which definition the source uses (e.g. AZ vs BMZ) — verbatim"
    )
    evidence_spans: list[EvidenceSpan] = Field(min_length=1)
    parser_version: str


class Regulation(StrictModel):
    jurisdiction: Jurisdiction
    zone_code: str
    zone_name: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    source_document: Source
    rules: list[Rule] = Field(default_factory=list)
    unresolved: list[str] = Field(
        default_factory=list,
        description="Rule keys the parser could not extract deterministically → class D downstream",
    )
    cls: FindingClass = Field(alias="class", default="A")
    parser_version: str
