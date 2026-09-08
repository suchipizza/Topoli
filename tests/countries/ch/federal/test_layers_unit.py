from __future__ import annotations

import base64
import io
from datetime import UTC, datetime
from typing import Any

from PIL import Image

from topoli.core.adapters import Record
from topoli.core.adapters.base import SiteContext
from topoli.core.domain import Coordinates, Jurisdiction, Parcel, Site
from topoli.core.scoring.coverage import build_coverage, canton_coverage
from topoli.countries.ch.federal import oereb, wms
from topoli.countries.ch.federal.noise import band
from topoli.countries.ch.federal.terrain import TerrainAdapter

SQUARE = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]],
}


def _png(size: int, painter) -> str:  # type: ignore[no-untyped-def]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for x in range(size):
        for y in range(size):
            if painter(x, y):
                img.putpixel((x, y), (0, 0, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _mask_record(png_b64: str, bbox: str = "0,0,100,100") -> Record:
    return Record(
        adapter_id="ch/federal/hazards",
        url=f"https://wms.geo.admin.ch/?SERVICE=WMS&REQUEST=GetMap&LAYERS=x&BBOX={bbox}&WIDTH=64&HEIGHT=64",
        retrieved_at=datetime.now(tz=UTC),
        payload={"png_base64": png_b64},
    )


def test_mask_coverage_left_half() -> None:
    rec = _mask_record(_png(64, lambda x, y: x < 32))
    cov = wms.mask_coverage(rec, SQUARE)
    assert abs(cov.fraction - 0.5) < 0.05
    assert abs(cov.area_m2 - 5000) < 500


def test_mask_coverage_outside_parcel_is_ignored() -> None:
    # paint the top-right quadrant; the parcel is only the bottom-left quadrant of the bbox
    rec = _mask_record(_png(64, lambda x, y: x >= 32 and y < 32))
    small = {"type": "Polygon", "coordinates": [[[0, 0], [50, 0], [50, 50], [0, 50], [0, 0]]]}
    assert wms.mask_coverage(rec, small).fraction == 0.0
    full = wms.mask_coverage(rec, SQUARE)
    assert abs(full.fraction - 0.25) < 0.05


def test_noise_bands() -> None:
    assert band(50, night=False) == "low"
    assert band(55, night=False) == "medium"
    assert band(64.9, night=False) == "medium"
    assert band(65, night=False) == "high"
    assert band(44, night=True) == "low"
    assert band(45, night=True) == "medium"
    assert band(55, night=True) == "high"


def test_oereb_parser_tolerates_three_dialects() -> None:
    zh = {
        "GetExtractByIdResponse": {"Extract": {"RealEstate": {"RestrictionOnLandownership": [1]}}}
    }
    be = {
        "GetExtractByIdResponse": {
            "extract": {"RealEstate": {"RestrictionOnLandownership": [1, 2]}}
        }
    }
    ge: dict[str, Any] = {"Item": {"RealEstate": {"RestrictionOnLandownership": []}}}
    for payload, n in ((zh, 1), (be, 2), (ge, 0)):
        root = oereb._extract_root(payload)
        assert root is not None
        assert len(oereb._get(oereb._get(root, "RealEstate"), "RestrictionOnLandownership")) == n
    assert oereb._extract_root({"unexpected": 1}) is None
    assert oereb._text([{"Language": "de", "Text": "Hallo"}]) == "Hallo"
    assert oereb._text({"Text": "x"}) == "x" and oereb._text(None) == ""
    assert oereb._get({"code": "a"}, "Code") == "a" and oereb._get({"Code": "b"}, "code") == "b"
    assert oereb._introduced({"oereb_status_de": "ÖREB-Kataster eingeführt"})
    assert not oereb._introduced({"oereb_status_de": "Einführung geplant 2021"})


def test_terrain_slope_levels() -> None:
    site = Site(
        id="x",
        input_address="x",
        address="x",
        coordinates=Coordinates(lon=8.5, lat=47.4, east=2681700, north=1247600),
        jurisdiction=Jurisdiction(country="CH", canton="ZH"),
        resolve_confidence=1,
        lang_default="de",
    )
    parcel = Parcel(local_id="1", municipality="Zürich", geometry_lv95=SQUARE)
    ctx = SiteContext(site=site, parcel=parcel)
    adapter = TerrainAdapter()

    def rec(alts: list[float]) -> Record:
        return Record(
            adapter_id=adapter.id,
            url="https://api3.geo.admin.ch/rest/services/profile.json?x",
            retrieved_at=datetime.now(tz=UTC),
            payload=[
                {"alts": {"COMB": a}, "dist": i, "easting": 0, "northing": 0}
                for i, a in enumerate(alts)
            ],
        )

    flat = adapter.to_findings([rec([400, 401, 400.5])], ctx)[0]
    assert flat.template_key == "terrain.flat" and flat.cls == "B"
    steep = adapter.to_findings([rec([400, 460])], ctx)[0]  # 60 m over a 141 m diagonal ≈ 42 %
    assert steep.template_key == "terrain.steep" and steep.severity == "medium"
    assert "diagonal" in (steep.derivation or "")


def test_canton_coverage_table() -> None:
    zh = canton_coverage("ZH")
    assert zh["federal_pct"] == 100
    assert zh["cantonal_pct"] == 0 and zh["events_pct"] == 0, (
        "nothing cantonal shipped before WO-05"
    )
    ti = canton_coverage("TI")
    assert ti["federal_pct"] == 90 and ti["federal"]["ch/federal/oereb"] == "not_available"
    assert ti["cantonal_pct"] == 0 and ti["events_pct"] == 0
    degraded = canton_coverage("BE", degraded=["ch/federal/noise"])
    assert degraded["federal_pct"] == 95 and degraded["federal"]["ch/federal/noise"] == "degraded"
    data = build_coverage(degraded=[])
    assert len(data["cantons"]) == 26 and data["cantons"]["GE"]["lang"] == "fr"
