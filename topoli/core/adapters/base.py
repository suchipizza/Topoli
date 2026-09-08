"""The contract every data adapter satisfies (PRD §4.3).

An adapter turns a resolved ``Site`` into raw ``Record`` objects (one per request, each with
``url`` and ``retrieved_at``) and then into localized ``Finding`` objects. It never reasons; it
fetches, intersects and maps published attributes to templates.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Protocol, runtime_checkable

from pydantic import Field

from topoli.core.domain import Finding, Jurisdiction, Lang, Licence, Site, StrictModel


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


class HealthStatus(StrictModel):
    adapter_id: str
    ok: bool
    detail: str
    checked_at: datetime


@runtime_checkable
class Adapter(Protocol):
    """See PRD §4.3. ``ttl`` is the cache lifetime for this adapter's records (WO-04)."""

    id: str
    jurisdiction: Jurisdiction
    licence: Licence
    ttl: timedelta

    def fetch(self, site: Site) -> list[Record]: ...

    def to_findings(self, records: list[Record], site: Site, lang: Lang) -> list[Finding]: ...

    def health(self) -> HealthStatus: ...
