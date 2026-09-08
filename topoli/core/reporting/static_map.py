"""Map for the report: swisstopo WMTS tiles (EPSG:2056) at view time, a static PNG at build time.

WMTS read on 2026-09-08 (``https://wmts.geo.admin.ch/EPSG/2056/1.0.0/WMTSCapabilities.xml``):
tile matrix set ``2056_27`` for ``ch.swisstopo.pixelkarte-farbe`` (JPEG), origin top-left
(2420000, 1350000), 256 px tiles, resolutions 1 m/px at zoom 25, 0.5 at 26, 0.25 at 27.
URL template ``https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/2056/
{TileMatrix}/{TileCol}/{TileRow}.jpeg`` (column **before** row). Terms: geo.admin.ch general terms
of use (attribution "© swisstopo").

The static fallback (``map.jpg``) is composed at build time from ≤ 12 tiles with the parcel
outline drawn on top; if the tiles cannot be fetched (offline, tests) the report shows the inline
SVG outline alone. Tile requests are not counted against the data-call budget (separate client).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw
from shapely.geometry import MultiPolygon, Polygon

from topoli.core.domain import Geometry
from topoli.core.geospatial import from_geojson

log = logging.getLogger("topoli.map")

ORIGIN_E = 2420000.0
ORIGIN_N = 1350000.0
TILE = 256
RESOLUTIONS = {24: 1.5, 25: 1.0, 26: 0.5, 27: 0.25}
TILE_URL = (
    "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/2056/"
    "{z}/{col}/{row}.jpeg"
)
ATTRIBUTION = "© swisstopo"
MAX_TILES = 12


@dataclass(frozen=True)
class MapFrame:
    zoom: int
    resolution: float
    minx: float
    maxy: float  # top-left corner of the frame in LV95
    width_px: int
    height_px: int
    tiles: list[dict[str, Any]]
    parcel_path: str  # SVG path in pixel coordinates
    buildings: list[tuple[float, float]]
    events: list[tuple[float, float, str]]


def _zoom_for(width_m: float) -> int:
    for zoom in (27, 26, 25, 24):
        if width_m / RESOLUTIONS[zoom] <= 900:
            return zoom
    return 24


def frame_for(
    parcel_lv95: Geometry,
    buildings_lv95: list[tuple[float, float]],
    events_lv95: list[tuple[float, float, str]],
    *,
    pad_ratio: float = 0.6,
) -> MapFrame:
    geom = from_geojson(parcel_lv95)
    minx, miny, maxx, maxy = geom.bounds
    w, h = maxx - minx, maxy - miny
    pad = max(w, h) * pad_ratio + 20
    fminx, fmaxx = minx - pad, maxx + pad
    fminy, fmaxy = miny - pad, maxy + pad
    zoom = _zoom_for(max(fmaxx - fminx, fmaxy - fminy))
    res = RESOLUTIONS[zoom]
    width_px = int((fmaxx - fminx) / res)
    height_px = int((fmaxy - fminy) / res)

    def px(x: float, y: float) -> tuple[float, float]:
        return (round((x - fminx) / res, 1), round((fmaxy - y) / res, 1))

    col0 = int((fminx - ORIGIN_E) // (res * TILE))
    col1 = int((fmaxx - ORIGIN_E) // (res * TILE))
    row0 = int((ORIGIN_N - fmaxy) // (res * TILE))
    row1 = int((ORIGIN_N - fminy) // (res * TILE))
    tiles = []
    for col in range(col0, col1 + 1):
        for row in range(row0, row1 + 1):
            tx = ORIGIN_E + col * res * TILE
            ty = ORIGIN_N - row * res * TILE
            x, y = px(tx, ty)
            tiles.append(
                {"url": TILE_URL.format(z=zoom, col=col, row=row), "x": x, "y": y, "size": TILE}
            )
    polys: list[Polygon] = (
        list(geom.geoms)
        if isinstance(geom, MultiPolygon)
        else [geom]
        if isinstance(geom, Polygon)
        else []
    )
    parts = []
    for poly in polys:
        coords = [px(x, y) for x, y in poly.exterior.coords]
        parts.append("M " + " L ".join(f"{x} {y}" for x, y in coords) + " Z")
    return MapFrame(
        zoom=zoom,
        resolution=res,
        minx=fminx,
        maxy=fmaxy,
        width_px=width_px,
        height_px=height_px,
        tiles=tiles[:MAX_TILES] if len(tiles) <= MAX_TILES else [],
        parcel_path=" ".join(parts),
        buildings=[px(x, y) for x, y in buildings_lv95],
        events=[(*px(x, y), kind) for x, y, kind in events_lv95],
    )


def render_static_png(frame: MapFrame, out: Path, *, timeout: float = 8.0) -> Path | None:
    """Compose the tiles + outline into ``out``; ``None`` when tiles are unavailable."""
    if not frame.tiles:
        return None
    canvas = Image.new("RGB", (frame.width_px, frame.height_px), (240, 240, 236))
    try:
        with httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "topoli (+https://github.com/suchipizza/Topoli)"},
        ) as client:
            for tile in frame.tiles:
                r = client.get(tile["url"])
                r.raise_for_status()
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                canvas.paste(img, (int(tile["x"]), int(tile["y"])))
    except (httpx.HTTPError, OSError) as exc:
        log.info("map.tiles_unavailable", extra={"error": str(exc)})
        return None
    draw = ImageDraw.Draw(canvas, "RGBA")
    for part in frame.parcel_path.split("Z"):
        pts = [
            tuple(map(float, p.strip().split()))
            for p in part.replace("M", "").split("L")
            if p.strip()
        ]
        if len(pts) >= 3:
            draw.polygon(pts, outline=(15, 107, 92, 255), fill=(15, 107, 92, 60), width=3)
    for x, y in frame.buildings:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(27, 31, 30, 255))
    for x, y, _kind in frame.events:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(184, 50, 50, 255), width=2)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, format="JPEG", quality=82, optimize=True, progressive=True)
    return out
