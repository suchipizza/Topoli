"""Shapely helpers. Inputs/outputs are GeoJSON dicts in LV95 unless stated otherwise."""

from __future__ import annotations

import json
from typing import Any

from shapely.geometry import MultiPolygon, Point, Polygon, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from topoli.core.domain import Geometry, GeometryIntersection


def from_geojson(geometry: Geometry) -> BaseGeometry:
    geom: BaseGeometry = shape(geometry)
    if not geom.is_valid:
        geom = geom.buffer(0)
    return geom


def to_geojson(geom: BaseGeometry, precision: int = 2) -> Geometry:
    raw: dict[str, Any] = dict(mapping(geom))
    rounded: Geometry = json.loads(
        json.dumps(raw), parse_float=lambda s: round(float(s), precision)
    )
    return rounded


def area_m2(geometry: Geometry) -> float:
    """Area in m² of an LV95 geometry."""
    return float(from_geojson(geometry).area)


def contains_point(geometry: Geometry, east: float, north: float) -> bool:
    return bool(from_geojson(geometry).covers(Point(east, north)))


def intersect(parcel: Geometry, others: list[Geometry]) -> GeometryIntersection:
    """Area and fraction of ``parcel`` covered by the union of ``others`` (all LV95)."""
    p = from_geojson(parcel)
    if p.area <= 0 or not others:
        return GeometryIntersection(area_m2=0.0, fraction=0.0)
    union = unary_union([from_geojson(g) for g in others])
    inter = float(p.intersection(union).area)
    return GeometryIntersection(area_m2=inter, fraction=min(1.0, inter / float(p.area)))


def buffer_m(geometry: Geometry, radius_m: float) -> Geometry:
    return to_geojson(from_geojson(geometry).buffer(radius_m))


def simplify_for_url(geometry: Geometry, max_points: int = 150) -> Geometry:
    """Douglas–Peucker simplify until the outline has ≤ ``max_points`` vertices (for GET URLs)."""
    geom = from_geojson(geometry)
    tolerance = 0.25
    while _vertex_count(geom) > max_points:
        geom = geom.simplify(tolerance, preserve_topology=True)
        tolerance *= 2
    return to_geojson(geom)


def _vertex_count(geom: BaseGeometry) -> int:
    if isinstance(geom, Polygon):
        return len(geom.exterior.coords)
    if isinstance(geom, MultiPolygon):
        return sum(len(p.exterior.coords) for p in geom.geoms)
    return 0


def to_esri_rings(geometry: Geometry, wkid: int = 2056) -> str:
    """ESRI JSON polygon string accepted by geo.admin.ch ``identify`` (GeoJSON input is not)."""
    if geometry["type"] == "Polygon":
        rings = geometry["coordinates"]
    elif geometry["type"] == "MultiPolygon":
        rings = [ring for poly in geometry["coordinates"] for ring in poly]
    else:
        msg = f"cannot build rings from {geometry['type']}"
        raise ValueError(msg)
    return json.dumps({"rings": rings, "spatialReference": {"wkid": wkid}}, separators=(",", ":"))
