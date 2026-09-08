"""CRS transforms and geometry operations. Areas are always computed in LV95 (EPSG:2056)."""

from topoli.core.geospatial.crs import lv95_to_wgs84, transform_geojson, wgs84_to_lv95
from topoli.core.geospatial.ops import (
    area_m2,
    buffer_m,
    contains_point,
    from_geojson,
    intersect,
    simplify_for_url,
    to_esri_rings,
    to_geojson,
)

__all__ = [
    "area_m2",
    "buffer_m",
    "contains_point",
    "from_geojson",
    "intersect",
    "lv95_to_wgs84",
    "simplify_for_url",
    "to_esri_rings",
    "to_geojson",
    "transform_geojson",
    "wgs84_to_lv95",
]
