"""Shared value objects: languages, localized text, coordinates, jurisdiction, licence."""

from __future__ import annotations

from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field

Lang = Literal["fr", "de", "it", "en"]
LANGS: tuple[Lang, ...] = get_args(Lang)

#: A GeoJSON geometry object (``{"type": "Polygon", "coordinates": [...]}``).
#: Kept as a plain mapping so evidence.json stays GeoJSON; shapely conversion lives in
#: ``topoli.core.geospatial``.
Geometry = dict[str, Any]


class StrictModel(BaseModel):
    """Base for every domain model: no unknown fields, assignment validated."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, populate_by_name=True)


class LocalizedText(StrictModel):
    """A user-facing string written per language (never machine-translated at runtime)."""

    fr: str
    de: str
    it: str
    en: str

    def get(self, lang: Lang) -> str:
        return str(getattr(self, lang))

    @classmethod
    def same(cls, text: str) -> LocalizedText:
        """One string for all languages — only for language-neutral content (IDs, codes)."""
        return cls(fr=text, de=text, it=text, en=text)


class Coordinates(StrictModel):
    """A point in both CRS we store: WGS84 (EPSG:4326) and LV95 (EPSG:2056)."""

    lon: float = Field(ge=-180, le=180, description="WGS84 longitude")
    lat: float = Field(ge=-90, le=90, description="WGS84 latitude")
    east: float = Field(description="LV95 easting (E), metres")
    north: float = Field(description="LV95 northing (N), metres")


class Jurisdiction(StrictModel):
    country: str = Field(min_length=2, max_length=2, description="ISO 3166-1 alpha-2, e.g. CH")
    canton: str | None = Field(default=None, description="Canton abbreviation, e.g. ZH")
    municipality: str | None = Field(default=None, description="Municipality name as published")
    bfs_number: int | None = Field(default=None, description="Swiss BFS municipality number")

    @property
    def path(self) -> str:
        parts = [self.country.lower()]
        if self.canton:
            parts.append(self.canton.lower())
        if self.municipality:
            parts.append(self.municipality.lower().replace(" ", "-"))
        return "/".join(parts)


class Licence(StrictModel):
    """Data licence of a source, mirrored by a row in ``LICENCES.md``."""

    id: str = Field(description="SPDX-like id, e.g. 'OPEN-BY-ASK' or 'CC-BY-4.0' or 'terms-of-use'")
    name: str
    url: str | None = None
    attribution: str = Field(description="Attribution text reproduced verbatim in the report")
    redistribution_allowed: bool
