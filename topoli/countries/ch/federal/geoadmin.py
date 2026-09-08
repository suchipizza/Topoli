"""Thin, documented wrappers around the geo.admin.ch REST API (FSDI).

Documentation read on 2026-09-08:

* Search:   https://docs.geo.admin.ch/access-data/search.html
            ``GET https://api3.geo.admin.ch/rest/services/api/SearchServer``
            params ``searchText, type=locations, origins, sr, limit``. Location results carry
            ``attrs.lat/lon`` (WGS84) and — **note the swap** — ``attrs.x`` = northing,
            ``attrs.y`` = easting in the requested ``sr``. ``fuzzy: "true"`` at the top level
            means the service relaxed the match.
* Identify: https://docs.geo.admin.ch/access-data/identify-features.html
            ``GET https://api3.geo.admin.ch/rest/services/all/MapServer/identify``
            params ``geometry, geometryType (esriGeometryPoint|Envelope|Polygon),
            geometryFormat=geojson, layers=all:<id>, sr=2056, tolerance, mapExtent,
            imageDisplay, returnGeometry, limit (≤200)``.
            Polygon input must be ESRI JSON (``{"rings": …}``); GeoJSON input is rejected (tested).
* Height:   https://docs.geo.admin.ch/access-data/get-point-height.html
            ``GET https://api3.geo.admin.ch/rest/services/height?easting&northing&sr=2056``
            → ``{"height": "412.1"}`` (swissALTI3D inside Switzerland).
* Terms:    https://www.geo.admin.ch/en/general-terms-of-use-fsdi — free, no registration,
            fair use ("maximum number of requests per time unit"), source must be credited.

Layers used by the federal spine (metadata: ``/rest/services/api/MapServer/<layer>``):

* ``ch.swisstopo-vd.amtliche-vermessung`` (OpenData-AV, cadastral parcels; attributes
  ``egris_egrid, number, identnd, bfsnr, ak, realestate_type, geoportal_url``; polygon geometry).
* ``ch.kantone.cadastralwebmap-farbe`` (CadastralWebMap, fallback; same attributes minus ``bfsnr``).
* ``ch.bfs.gebaeude_wohnungs_register`` (GWR/RegBL; one point per building entrance with
  ``egid, edid, egrid, lparz, ggdename, ggdenr, gdekt, gstat, gkat, gklas, gbauj, gbaup, gastw,
  garea, gvol, gebf, ganzwhg, gwaerzh1, genh1, …``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from topoli.core.adapters import Record, get_client

BASE = "https://api3.geo.admin.ch/rest/services"
SEARCH_URL = f"{BASE}/api/SearchServer"
IDENTIFY_URL = f"{BASE}/all/MapServer/identify"
HEIGHT_URL = f"{BASE}/height"
TERMS_URL = "https://www.geo.admin.ch/en/general-terms-of-use-fsdi"

LAYER_AV = "ch.swisstopo-vd.amtliche-vermessung"
LAYER_CADASTRAL_WEBMAP = "ch.kantone.cadastralwebmap-farbe"
LAYER_GWR = "ch.bfs.gebaeude_wohnungs_register"

LV95 = 2056


def search_locations(
    adapter_id: str,
    text: str,
    *,
    origins: str | None = None,
    limit: int = 10,
) -> Record:
    params: dict[str, Any] = {"searchText": text, "type": "locations", "sr": LV95, "limit": limit}
    if origins:
        params["origins"] = origins
    return get_client().get_json(adapter_id, SEARCH_URL, params)


def identify(
    adapter_id: str,
    layer: str,
    geometry: str,
    geometry_type: str,
    *,
    tolerance: int = 0,
    return_geometry: bool = True,
    limit: int = 200,
    extra: Mapping[str, Any] | None = None,
) -> Record:
    params: dict[str, Any] = {
        "geometry": geometry,
        "geometryType": geometry_type,
        "geometryFormat": "geojson",
        "layers": f"all:{layer}",
        "sr": LV95,
        "tolerance": tolerance,
        "returnGeometry": "true" if return_geometry else "false",
        "limit": limit,
    }
    if tolerance > 0:
        # Required by the API when tolerance > 0; a 1 km window at 96 dpi ≈ 1 m per pixel.
        east, north = (float(v) for v in geometry.split(",")[:2])
        params["mapExtent"] = f"{east - 500},{north - 500},{east + 500},{north + 500}"
        params["imageDisplay"] = "1000,1000,96"
    if extra:
        params.update(extra)
    return get_client().get_json(adapter_id, IDENTIFY_URL, params)


def identify_point(
    adapter_id: str, layer: str, east: float, north: float, *, tolerance: int = 0, **kw: Any
) -> Record:
    return identify(
        adapter_id, layer, f"{east},{north}", "esriGeometryPoint", tolerance=tolerance, **kw
    )


def identify_polygon(adapter_id: str, layer: str, esri_rings: str, **kw: Any) -> Record:
    return identify(adapter_id, layer, esri_rings, "esriGeometryPolygon", **kw)


def height(adapter_id: str, east: float, north: float) -> Record:
    return get_client().get_json(
        adapter_id, HEIGHT_URL, {"easting": east, "northing": north, "sr": LV95}
    )


def results(record: Record) -> list[dict[str, Any]]:
    payload = record.payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return [r for r in payload["results"] if isinstance(r, dict)]
    return []
