"""Evidence primitives: where a claim comes from and how it was derived."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from topoli.core.domain.common import StrictModel


class Source(StrictModel):
    """Provenance of a record or finding (PRD §5 ``source``)."""

    adapter_id: str = Field(description="e.g. 'ch/federal/hazards'")
    authority: str = Field(description="Publishing authority as named by the source")
    dataset: str = Field(description="Dataset / layer name as published")
    licence: str = Field(description="Licence id matching a row in LICENCES.md")
    retrieved_at: datetime | None = Field(default=None, description="When we fetched it (UTC)")
    url: str | None = Field(default=None, description="URL of the exact request or record")
    stale_as_of: datetime | None = Field(
        default=None,
        description="Set when served from cache after a failed refetch (PRD §3.6 'as of <date>')",
    )

    @property
    def is_complete(self) -> bool:
        """A class A/B finding needs both a URL and a retrieval time."""
        return bool(self.url) and self.retrieved_at is not None


class EvidenceSpan(StrictModel):
    """A verbatim span from a source document backing a regulatory claim."""

    document: str = Field(description="Document identifier, e.g. 'BZO Zürich 2016'")
    article: str = Field(description="Article / section reference, e.g. 'Art. 13 Abs. 2'")
    text: str = Field(min_length=1, description="Verbatim span, source language")
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    url: str | None = None


class GeometryIntersection(StrictModel):
    """Result of intersecting a parcel with a constraint layer (computed in LV95)."""

    area_m2: float = Field(ge=0)
    fraction: float = Field(ge=0, le=1, description="Share of the parcel area covered")
