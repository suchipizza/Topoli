"""``AuditResult`` — everything one run produced; serialized as ``evidence.json`` (layer 2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, get_args

from pydantic import Field

from topoli import __version__
from topoli.core.domain import (
    Building,
    ConstructionEvent,
    Finding,
    Lang,
    Parcel,
    Regulation,
    Site,
    StrictModel,
)

CoverageStatus = Literal["ok", "degraded", "not_available", "not_contributed"]
COVERAGE_STATUSES: tuple[CoverageStatus, ...] = get_args(CoverageStatus)


class CoverageEntry(StrictModel):
    """Per-adapter outcome for this audit (PRD §3.2 progress lines, §6 coverage notice)."""

    adapter_id: str
    status: CoverageStatus
    detail: str | None = Field(
        default=None, description="Short reason, e.g. 'HTTP 503', 'no ÖREB for VS'"
    )
    calls: int = Field(default=0, ge=0, description="External HTTP calls made by this adapter")
    from_cache: bool = False


class Timing(StrictModel):
    step: str
    seconds: float = Field(ge=0)


class AuditResult(StrictModel):
    site: Site
    parcels: list[Parcel] = Field(default_factory=list)
    buildings: list[Building] = Field(default_factory=list)
    regulations: list[Regulation] = Field(default_factory=list)
    events: list[ConstructionEvent] = Field(default_factory=list)
    findings: list[Finding] = Field(
        default_factory=list, description="All validated findings, shown or not, ranked"
    )
    coverage: list[CoverageEntry] = Field(default_factory=list)
    timings: list[Timing] = Field(default_factory=list)
    lang: Lang
    goal: str | None = None
    generated_at: datetime
    topoli_version: str = __version__
    parser_versions: dict[str, str] = Field(
        default_factory=dict, description="adapter/parser id → version string"
    )

    @property
    def total_calls(self) -> int:
        return sum(c.calls for c in self.coverage)

    def coverage_for(self, adapter_id: str) -> CoverageEntry | None:
        return next((c for c in self.coverage if c.adapter_id == adapter_id), None)

    def class_counts(self, findings: list[Finding] | None = None) -> dict[str, int]:
        pool = self.findings if findings is None else findings
        counts = {"A": 0, "B": 0, "C": 0, "D": 0}
        for f in pool:
            counts[f.cls] += 1
        return counts
