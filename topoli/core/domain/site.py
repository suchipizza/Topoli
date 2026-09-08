"""The resolved site: what an address became after geocoding."""

from __future__ import annotations

from pydantic import Field

from topoli.core.domain.common import Coordinates, Jurisdiction, Lang, StrictModel
from topoli.core.domain.evidence import Source


class Site(StrictModel):
    id: str = Field(
        description="Stable id, e.g. '<bfs>-<parcel>' or a geohash for parcel-less sites"
    )
    input_address: str = Field(description="Exactly what the user typed")
    address: str = Field(description="Formatted address as returned by the resolver")
    coordinates: Coordinates
    jurisdiction: Jurisdiction
    parcel_ids: list[str] = Field(default_factory=list)
    egid: str | None = Field(default=None, description="Federal building id at the address")
    resolve_confidence: float = Field(ge=0, le=1)
    lang_default: Lang
    sources: list[Source] = Field(default_factory=list)
