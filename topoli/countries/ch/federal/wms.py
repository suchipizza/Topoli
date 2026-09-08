"""WMS access to geo.admin.ch **raster** layers, which ``identify`` cannot query.

Documentation read on 2026-09-08: https://docs.geo.admin.ch/visualize-data/wms.html
(``https://wms.geo.admin.ch/``, WMS 1.3.0, ``CRS=EPSG:2056``, ``FORMAT=image/png``,
``TRANSPARENT=TRUE``; GetFeatureInfo with ``INFO_FORMAT=application/json``, one queryable
layer per request — several ``QUERY_LAYERS`` in one JSON request raise a service exception).

Two access patterns:

* :func:`get_feature_info` — pixel value at a point (noise levels in dB, ``value_0``).
* :func:`get_map_mask` — a small transparent PNG of the layer over the parcel's bounding box;
  the parcel outline is rasterised on the same grid and the overlap is counted. This yields
  a deterministic coverage estimate (class B) for presence-only rasters such as the
  Aquaprotect flood maps, the surface-runoff hazard map and the SilvaProtect process areas.
  Resolution is stated in ``derivation`` (``<size>×<size>`` pixels over the bbox).
"""

from __future__ import annotations

import base64
import io
from datetime import UTC, datetime
from typing import Any

import httpx
from PIL import Image, ImageDraw
from shapely.geometry import MultiPolygon, Polygon

from topoli.core.adapters import Record, get_client
from topoli.core.domain import Geometry, GeometryIntersection
from topoli.core.geospatial import from_geojson

WMS_URL = "https://wms.geo.admin.ch/"
MASK_SIZE = 64


def get_feature_info(
    adapter_id: str, layer: str, east: float, north: float, *, lang: str = "de"
) -> Record:
    half = 5.0
    params: dict[str, Any] = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer,
        "QUERY_LAYERS": layer,
        "CRS": "EPSG:2056",
        "BBOX": f"{east - half},{north - half},{east + half},{north + half}",
        "WIDTH": 10,
        "HEIGHT": 10,
        "I": 5,
        "J": 5,
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": 10,
        "LANG": lang,
    }
    return get_client().get_json(adapter_id, WMS_URL, params)


def feature_values(record: Record, key: str = "value_0") -> list[float]:
    payload = record.payload
    values: list[float] = []
    if isinstance(payload, dict):
        for feature in payload.get("features", []) or []:
            props = feature.get("properties", {}) if isinstance(feature, dict) else {}
            raw = props.get(key)
            if raw is None:
                continue
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue
    return values


def get_map_mask(
    adapter_id: str, layers: str, bbox: tuple[float, float, float, float], *, size: int = MASK_SIZE
) -> Record:
    """Fetch a transparent PNG of ``layers`` over ``bbox``; payload carries it base64-encoded."""
    params: dict[str, Any] = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": layers,
        "STYLES": "",
        "CRS": "EPSG:2056",
        "BBOX": ",".join(f"{v:.1f}" for v in bbox),
        "WIDTH": size,
        "HEIGHT": size,
        "FORMAT": "image/png",
        "TRANSPARENT": "TRUE",
    }
    return get_client().get_bytes(
        adapter_id,
        WMS_URL,
        params,
        wrap=lambda data: {"png_base64": base64.b64encode(data).decode()},
    )


def mask_coverage(record: Record, parcel_lv95: Geometry) -> GeometryIntersection:
    """Share of the parcel covered by non-transparent pixels of the fetched map."""
    payload = record.payload
    bbox = _bbox_from_url(record.url)
    png = base64.b64decode(payload["png_base64"]) if isinstance(payload, dict) else b""
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    width, height = image.size
    minx, miny, maxx, maxy = bbox
    sx = width / (maxx - minx)
    sy = height / (maxy - miny)

    mask = Image.new("1", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    geom = from_geojson(parcel_lv95)
    polygons: list[Polygon] = (
        list(geom.geoms)
        if isinstance(geom, MultiPolygon)
        else [geom]
        if isinstance(geom, Polygon)
        else []
    )
    for poly in polygons:
        pts = [((x - minx) * sx, (maxy - y) * sy) for x, y in poly.exterior.coords]
        draw.polygon(pts, fill=1)
        for hole in poly.interiors:
            draw.polygon([((x - minx) * sx, (maxy - y) * sy) for x, y in hole.coords], fill=0)

    alpha = image.getchannel("A").tobytes()
    mask_l = mask.convert("L").tobytes()
    parcel_px = 0
    hit_px = 0
    for a, m in zip(alpha, mask_l, strict=True):
        if m:
            parcel_px += 1
            if a > 0:
                hit_px += 1
    if parcel_px == 0:
        return GeometryIntersection(area_m2=0.0, fraction=0.0)
    fraction = hit_px / parcel_px
    return GeometryIntersection(
        area_m2=round(float(geom.area) * fraction, 1), fraction=round(fraction, 3)
    )


def _bbox_from_url(url: str) -> tuple[float, float, float, float]:
    raw = str(httpx.URL(url).params.get("BBOX", ""))
    parts = [float(v) for v in raw.split(",")]
    if len(parts) != 4:
        msg = f"record URL has no valid BBOX: {url}"
        raise ValueError(msg)
    return parts[0], parts[1], parts[2], parts[3]


def parcel_bbox(parcel_lv95: Geometry, pad_m: float = 2.0) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = from_geojson(parcel_lv95).bounds
    # keep the grid square-ish so pixels are ~isotropic
    return (minx - pad_m, miny - pad_m, maxx + pad_m, maxy + pad_m)


def now() -> datetime:
    return datetime.now(tz=UTC)
