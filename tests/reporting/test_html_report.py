"""Report + evidence.json (WO-08): renders offline from fixtures, self-contained, four languages."""

from __future__ import annotations

import contextlib
import html
import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from topoli.core.adapters import get_client
from topoli.core.pipeline import build_result
from topoli.core.reporting.evidence_json import load_evidence, write_evidence
from topoli.core.reporting.html import normalize_for_golden, render_html
from topoli.core.reporting.share import run_link, waitlist_link
from topoli.core.reporting.static_map import frame_for

ADAPTERS = [
    "ch/federal/hazards",
    "ch/federal/noise",
    "ch/federal/contamination",
    "ch/federal/oereb",
    "ch/federal/solar",
    "ch/federal/heritage",
    "ch/federal/terrain",
    "ch/zh/zoning",
    "ch/zh/regulation",
    "ch/zh/heritage",
    "ch/zh/construction_events",
]


@pytest.fixture
def report(replay: Callable[[str, str], int], tmp_path: Path):  # type: ignore[no-untyped-def]
    for adapter_id in ADAPTERS:
        with contextlib.suppress(AssertionError):
            replay(adapter_id, "zurich-badenerstrasse-171")
    get_client().reset()
    result, run = build_result("Badenerstrasse 171, 8003 Zürich", lang="de")
    out = write_evidence(result, run.records, root=tmp_path / "reports")
    path, layer0 = render_html(result, out, lang="de", fetch_tiles=False)
    return result, out, path, layer0


def test_evidence_json_round_trips(report) -> None:  # type: ignore[no-untyped-def]
    result, out, _, _ = report
    assert (out / "evidence.json").is_file() and (out / "geometry.geojson").is_file()
    loaded = load_evidence(out)
    assert loaded.site.id == result.site.id
    assert len(loaded.findings) == len(result.findings)
    assert all(f.cls in "ABCD" for f in loaded.findings)
    raw = sorted(p.name for p in (out / "raw").glob("*.json"))
    assert "ch__federal__hazards.json" in raw and "ch__zh__construction_events.json" in raw
    geo = json.loads((out / "geometry.geojson").read_text(encoding="utf-8"))
    kinds = {f["properties"]["kind"] for f in geo["features"]}
    assert {"parcel", "building", "event"} <= kinds
    assert out.name == "zurich-AU6979"


def test_html_is_self_contained_and_multilingual(report) -> None:  # type: ignore[no-untyped-def]
    _, _out, path, layer0 = report
    page = path.read_text(encoding="utf-8")
    assert page.startswith("<!doctype html>")
    assert 'lang="de"' in page
    # no external scripts/styles; only swisstopo tiles (view time) and site links are external
    assert not re.search(r"<script[^>]+src=", page)
    assert not re.search(r"<link[^>]+stylesheet", page)
    assert "window.TOPOLI" in page
    data = json.loads(re.search(r"window\.TOPOLI = (\{.*?\});</script>", page, re.S).group(1))  # type: ignore[union-attr]
    assert set(data["i18n"]) == {"fr", "de", "it", "en"}
    for lang in ("fr", "de", "it", "en"):
        assert data["i18n"][lang]["section.7"] and data["i18n"][lang]["layer0.header"]
        assert "__TODO__" not in json.dumps(data["i18n"][lang])
    assert len(data["map"]["tiles"]) >= 4
    assert all(
        t["url"].startswith("https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/")
        for t in data["map"]["tiles"]
    )
    for f in layer0.findings:  # the five cards, each with its four-language texts
        assert (
            f.title.fr in page.replace("&#39;", "'")
            or json.dumps(f.title.fr, ensure_ascii=False)[1:-1] in page
        )
    assert page.count('class="sec"') == 18
    assert 'aria-expanded="false"' in page and "prefers-color-scheme" in page and "@page" in page
    assert "map.jpg" not in page, "no static map when tiles were not fetched"
    assert html.escape(run_link("report", "de")) in page
    assert html.escape(waitlist_link("report", "de")) in page


def test_share_links_carry_no_address() -> None:
    for src in ("card", "report", "readme", "summary"):
        url = run_link(src, "fr")
        assert "Badenerstrasse" not in url and "AU6979" not in url
        assert url.endswith(f"/run?src={src}&lang=fr")
    with pytest.raises(ValueError, match="src"):
        run_link("evil", "fr")
    assert "vote=monitor%2Cscan" in waitlist_link("report", "fr", ["monitor", "scan"])


def test_render_offline_from_evidence(report, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    _, out, _, _ = report
    result = load_evidence(out)
    path, layer0 = render_html(result, out, lang="fr", fetch_tiles=False)
    page = path.read_text(encoding="utf-8")
    assert 'lang="fr"' in page and "CHECK IMMOBILIER" in json.dumps(page, ensure_ascii=False)
    assert get_client().calls == 0
    assert layer0.lang == "fr"


def test_map_frame_math() -> None:
    square = {
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
    frame = frame_for(square, [(2681650, 1247650)], [(2681620, 1247620, "conversion")])
    assert frame.zoom in (26, 27) and frame.resolution in (0.5, 0.25)
    assert (
        frame.width_px > 0
        and frame.parcel_path.startswith("M ")
        and frame.parcel_path.endswith("Z")
    )
    assert 1 <= len(frame.tiles) <= 12
    tile = frame.tiles[0]
    assert re.match(
        r"https://wmts\.geo\.admin\.ch/1\.0\.0/ch\.swisstopo\.pixelkarte-farbe/default/current/2056/\d+/\d+/\d+\.jpeg",
        tile["url"],
    )
    assert len(frame.buildings) == 1 and frame.events[0][2] == "conversion"


def test_golden_normalization_is_stable(report) -> None:  # type: ignore[no-untyped-def]
    _, _, path, _ = report
    a = normalize_for_golden(path.read_text(encoding="utf-8"))
    assert ("VERSION" in a and "TIMESTAMP" not in a) or "DATE" in a
    assert normalize_for_golden(a) == a
