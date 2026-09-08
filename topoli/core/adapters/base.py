"""The contract every data adapter satisfies (PRD §4.3).

An adapter turns a resolved ``Site`` into raw ``Record`` objects (one per request, each with
``url`` and ``retrieved_at``) and then into localized ``Finding`` objects. It never reasons; it
fetches, intersects and maps published attributes to templates.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol, runtime_checkable

from pydantic import Field

from topoli.core.domain import (
    Building,
    Finding,
    Jurisdiction,
    Licence,
    Parcel,
    Site,
    StrictModel,
)


class Record(StrictModel):
    """One raw response from a source, exactly as received, plus provenance."""

    adapter_id: str
    url: str = Field(description="The exact request URL (query string included)")
    retrieved_at: datetime
    payload: Any = Field(description="Parsed JSON body as returned by the source")
    request: dict[str, Any] = Field(
        default_factory=dict, description="Endpoint + parameters, for fixtures and debugging"
    )
    from_cache: bool = False
    stale_as_of: datetime | None = Field(
        default=None, description="Set when served from cache after a failed refetch"
    )


class SiteContext(StrictModel):
    """What the spine resolved before layer adapters run (PRD §3.2 steps 1–3)."""

    site: Site
    parcel: Parcel | None = None
    buildings: list[Building] = Field(default_factory=list)

    @property
    def parcel_geometry(self) -> dict[str, Any] | None:
        return self.parcel.geometry_lv95 if self.parcel else None


class HealthStatus(StrictModel):
    adapter_id: str
    ok: bool
    detail: str
    checked_at: datetime


@runtime_checkable
class Adapter(Protocol):
    """See PRD §4.3 (``fetch``/``to_findings`` take a ``SiteContext`` = site + parcel +
    buildings, because every layer adapter needs the parcel outline; see decision 004).
    ``to_findings`` returns findings localized in all four languages; the caller picks
    the output language. ``ttl`` is the cache lifetime for this adapter's records."""

    id: str
    jurisdiction: Jurisdiction
    licence: Licence
    ttl: timedelta

    def fetch(self, ctx: SiteContext) -> list[Record]: ...

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]: ...

    def health(self) -> HealthStatus: ...
