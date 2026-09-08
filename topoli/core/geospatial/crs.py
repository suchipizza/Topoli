"""WGS84 (EPSG:4326) ⇄ LV95 (EPSG:2056) via pyproj; no GDAL."""

from __future__ import annotations

from functools import cache
from typing import Any

from pyproj import Transformer

from topoli.core.domain import Geometry


@cache
def _to_lv95() -> Transformer:
    return Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)


@cache
def _to_wgs84() -> Transformer:
    return Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)


def wgs84_to_lv95(lon: float, lat: float) -> tuple[float, float]:
    east, north = _to_lv95().transform(lon, lat)
    return float(east), float(north)


def lv95_to_wgs84(east: float, north: float) -> tuple[float, float]:
    lon, lat = _to_wgs84().transform(east, north)
    return float(lon), float(lat)


def transform_geojson(geometry: Geometry, *, to: str) -> Geometry:
    """Reproject a GeoJSON geometry's coordinates; ``to`` is ``"lv95"`` or ``"wgs84"``."""
    fn = wgs84_to_lv95 if to == "lv95" else lv95_to_wgs84
    precision = 2 if to == "lv95" else 7

    def walk(node: Any) -> Any:
        if isinstance(node, list | tuple) and node and isinstance(node[0], int | float):
            x, y = fn(float(node[0]), float(node[1]))
            return [round(x, precision), round(y, precision)]
        if isinstance(node, list | tuple):
            return [walk(n) for n in node]
        return node

    return {"type": geometry["type"], "coordinates": walk(geometry["coordinates"])}
