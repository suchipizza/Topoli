"""Construction event (permit publication, project announcement)."""

from __future__ import annotations

from datetime import date

from pydantic import Field

from topoli.core.domain.common import Coordinates, StrictModel
from topoli.core.domain.evidence import Source


class ConstructionEvent(StrictModel):
    id: str
    location: Coordinates | None = None
    parcels: list[str] = Field(default_factory=list)
    type: str = Field(
        description="Normalized type, e.g. 'new_building', 'conversion', 'demolition'"
    )
    description: str
    applicant: str | None = None
    project_author: str | None = None
    publication_date: date
    status: str | None = None
    expected_trades: list[str] = Field(default_factory=list)
    distance_m: float | None = Field(default=None, ge=0, description="From the audited site")
    sources: list[Source] = Field(min_length=1)
