"""Parcel and building."""

from __future__ import annotations

import unicodedata

from pydantic import Field

from topoli.core.domain.common import Geometry, StrictModel
from topoli.core.domain.evidence import Source


class Parcel(StrictModel):
    national_id: str | None = Field(default=None, description="EGRID (CH) or national parcel id")
    local_id: str = Field(description="Parcel number as used by the municipality/canton")
    municipality: str
    bfs_number: int | None = None
    canton: str | None = None
    geometry_wgs84: Geometry | None = None
    geometry_lv95: Geometry | None = None
    area_m2: float | None = Field(default=None, ge=0, description="Computed in LV95")
    area_m2_published: float | None = Field(
        default=None, ge=0, description="Area attribute as published by the source, for cross-check"
    )
    zoning_code: str | None = None
    zoning_name: str | None = None
    adjacent_parcel_ids: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)

    @property
    def slug(self) -> str:
        """Folder-safe id used for ``./reports/<municipality>-<parcel>/``."""
        ascii_muni = (
            unicodedata.normalize("NFKD", self.municipality).encode("ascii", "ignore").decode()
        )
        muni = "".join(c if c.isalnum() else "-" for c in ascii_muni.lower())
        while "--" in muni:
            muni = muni.replace("--", "-")
        return f"{muni.strip('-')}-{self.local_id}"


class Building(StrictModel):
    id: str = Field(description="EGID (CH) or building id")
    geometry_wgs84: Geometry | None = None
    geometry_lv95: Geometry | None = None
    footprint_m2: float | None = Field(default=None, ge=0)
    use: str | None = Field(
        default=None, description="Category/use as published (GWR code + label)"
    )
    year: int | None = Field(default=None, ge=1000, le=2200)
    floors: int | None = Field(default=None, ge=0)
    height_m: float | None = Field(default=None, ge=0)
    energy: str | None = Field(default=None, description="Energy carrier/class if public")
    heritage: str | None = Field(default=None, description="Listing status if known")
    missing_attributes: list[str] = Field(
        default_factory=list, description="Attributes the source did not provide (never defaulted)"
    )
    sources: list[Source] = Field(default_factory=list)
