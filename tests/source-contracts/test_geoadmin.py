"""Live contract tests for geo.admin.ch (nightly). Fail loudly on schema drift."""

from __future__ import annotations

import pytest

from topoli.core.adapters import get_client
from topoli.core.geospatial import simplify_for_url, to_esri_rings
from topoli.countries.ch.federal import geoadmin

pytestmark = pytest.mark.live

_ZH = (2681718.0, 1247636.0)


@pytest.fixture(autouse=True)
def _reset() -> None:
    get_client().reset()


@pytest.mark.adapter("ch/federal/geocode")
def test_search_locations_schema() -> None:
    rec = geoadmin.search_locations(
        "contract", "Badenerstrasse 171 8003 Zürich", origins="address", limit=1
    )
    hits = geoadmin.results(rec)
    assert hits, "no address hit"
    attrs = hits[0]["attrs"]
    for key in ("label", "detail", "lat", "lon", "x", "y", "origin", "featureId"):
        assert key in attrs, f"missing attrs.{key}"
    assert attrs["origin"] == "address"
    assert 2_400_000 < attrs["y"] < 2_900_000, "attrs.y must be LV95 easting"
    assert 1_000_000 < attrs["x"] < 1_400_000, "attrs.x must be LV95 northing"


@pytest.mark.adapter("ch/federal/parcel")
def test_parcel_layer_schema() -> None:
    rec = geoadmin.identify_point("contract", geoadmin.LAYER_AV, *_ZH)
    hits = geoadmin.results(rec)
    assert hits
    props = hits[0]["properties"]
    for key in ("egris_egrid", "number", "bfsnr", "ak", "identnd"):
        assert key in props
    assert hits[0]["geometry"]["type"] in ("Polygon", "MultiPolygon")


@pytest.mark.adapter("ch/federal/buildings")
def test_gwr_layer_schema_and_polygon_identify() -> None:
    rec = geoadmin.identify_point("contract", geoadmin.LAYER_AV, *_ZH)
    geom = geoadmin.results(rec)[0]["geometry"]
    gwr = geoadmin.identify_polygon(
        "contract", geoadmin.LAYER_GWR, to_esri_rings(simplify_for_url(geom)), return_geometry=False
    )
    hits = geoadmin.results(gwr)
    assert hits, "polygon identify on GWR returned nothing"
    props = hits[0]["properties"]
    for key in (
        "egid",
        "egrid",
        "lparz",
        "ggdename",
        "ggdenr",
        "gdekt",
        "gstat",
        "gkat",
        "gastw",
        "gbauj",
        "garea",
    ):
        assert key in props


@pytest.mark.adapter("ch/federal/terrain")
def test_height_schema() -> None:
    rec = geoadmin.height("contract", *_ZH)
    assert 300 < float(rec.payload["height"]) < 1000
