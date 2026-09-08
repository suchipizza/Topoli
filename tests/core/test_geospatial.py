from __future__ import annotations

import json

from topoli.core.geospatial import (
    area_m2,
    buffer_m,
    contains_point,
    intersect,
    lv95_to_wgs84,
    simplify_for_url,
    to_esri_rings,
    transform_geojson,
    wgs84_to_lv95,
)

SQUARE = {"type": "Polygon", "coordinates": [[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]]}
SQUARE_LV95 = {
    "type": "Polygon",
    "coordinates": [
        [
            [2681600, 1247600],
            [2681700, 1247600],
            [2681700, 1247700],
            [2681600, 1247700],
            [2681600, 1247600],
        ]
    ],
}


def test_crs_round_trip() -> None:
    # Bern, Bundesplatz: LV95 2600423 / 1199521 ≈ 46.9466 N, 7.4443 E
    lon, lat = lv95_to_wgs84(2600423.0, 1199521.0)
    assert abs(lat - 46.9466) < 0.001 and abs(lon - 7.4443) < 0.001
    e, n = wgs84_to_lv95(lon, lat)
    assert abs(e - 2600423.0) < 0.01 and abs(n - 1199521.0) < 0.01


def test_transform_geojson_polygon() -> None:
    wgs = transform_geojson(SQUARE_LV95, to="wgs84")
    assert wgs["type"] == "Polygon"
    back = transform_geojson(wgs, to="lv95")
    assert abs(area_m2(back) - 10_000) < 1


def test_area_intersect_contains_buffer() -> None:
    assert area_m2(SQUARE) == 10_000
    half = {"type": "Polygon", "coordinates": [[[0, 0], [50, 0], [50, 100], [0, 100], [0, 0]]]}
    inter = intersect(SQUARE, [half, half])  # union, not double counting
    assert inter.area_m2 == 5_000 and inter.fraction == 0.5
    assert intersect(SQUARE, []).fraction == 0
    assert contains_point(SQUARE, 10, 10) and not contains_point(SQUARE, 200, 10)
    assert area_m2(buffer_m(SQUARE, 10)) > 10_000


def test_esri_rings_and_simplify() -> None:
    rings = json.loads(to_esri_rings(SQUARE))
    assert rings["spatialReference"]["wkid"] == 2056
    assert rings["rings"][0][0] == [0, 0]
    dense = {
        "type": "Polygon",
        "coordinates": [[[i, (i % 2) * 0.01] for i in range(400)] + [[399, 50], [0, 50], [0, 0]]],
    }
    simple = simplify_for_url(dense, max_points=50)
    assert len(simple["coordinates"][0]) <= 50
