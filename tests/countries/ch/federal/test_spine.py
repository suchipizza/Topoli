"""Federal spine on five recorded sites (2× City of Zürich, Winterthur, Genève, Lugano).

Fixtures live in ``tests/fixtures/<adapter_id>/<slug>/`` (recorded cache files). Re-record with
``uv run topoli fixtures record --adapter ch/federal/buildings --address "<addr>" --slug <slug>``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from topoli.core.adapters import get_client
from topoli.core.domain import Building, Parcel, Site
from topoli.countries.ch.federal.geocode import ResolveError, resolve_address

Spine = tuple[Site, Parcel, list[Building]]
RunSpine = Callable[[str, str], Spine]


@dataclass(frozen=True)
class SiteCase:
    slug: str
    address: str
    canton: str
    bfs: int
    municipality: str
    lang: str
    parcel: str
    egrid: str


CASES = [
    SiteCase(
        "zurich-badenerstrasse-171",
        "Badenerstrasse 171, 8003 Zürich",
        "ZH",
        261,
        "Zürich",
        "de",
        "AU6979",
        "CH527182999120",
    ),
    SiteCase(
        "zurich-seefeldstrasse-80",
        "Seefeldstrasse 80 8008 Zürich",
        "ZH",
        261,
        "Zürich",
        "de",
        "",
        "",
    ),
    SiteCase(
        "winterthur-technikumstrasse-9",
        "Technikumstrasse 9, 8400 Winterthur",
        "ZH",
        230,
        "Winterthur",
        "de",
        "ST9255",
        "CH427786200879",
    ),
    SiteCase(
        "geneve-rue-du-rhone-14",
        "Rue du Rhône 14, 1204 Genève",
        "GE",
        6621,
        "Genève",
        "fr",
        "7013",
        "CH296589536314",
    ),
    SiteCase(
        "lugano-via-nassa-5",
        "Via Nassa 5, 6900 Lugano",
        "TI",
        5192,
        "Lugano",
        "it",
        "191",
        "CH987802070993",
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.slug for c in CASES])
def test_spine(case: SiteCase, run_spine: RunSpine) -> None:
    site, parcel, buildings = run_spine(case.slug, case.address)

    assert site.jurisdiction.canton == case.canton
    assert site.jurisdiction.bfs_number == case.bfs
    assert site.jurisdiction.municipality == case.municipality
    assert site.lang_default == case.lang
    assert site.resolve_confidence >= 0.7
    assert site.coordinates.east > 2_400_000 and site.coordinates.north > 1_000_000
    assert 45 < site.coordinates.lat < 48 and 5 < site.coordinates.lon < 11
    assert site.egid
    assert site.sources and all(s.is_complete for s in site.sources)

    if case.parcel:
        assert parcel.local_id == case.parcel
        assert parcel.national_id == case.egrid
    assert parcel.national_id and parcel.national_id.startswith("CH")
    assert parcel.geometry_lv95 and parcel.geometry_wgs84
    assert parcel.area_m2 and 20 < parcel.area_m2 < 200_000
    assert parcel.adjacent_parcel_ids, "urban parcels always have neighbours"
    assert parcel.national_id not in parcel.adjacent_parcel_ids
    assert all(s.is_complete for s in parcel.sources)

    assert buildings, "expected ≥ 1 building on the parcel"
    for b in buildings:
        assert b.id.isdigit()
        assert b.sources and b.sources[0].is_complete
    assert any(b.floors for b in buildings)
    assert get_client().calls == 0, "replayed tests must not touch the network"
    assert get_client().cache_hits >= 4


def test_badenerstrasse_details(run_spine: RunSpine) -> None:
    case = CASES[0]
    site, parcel, buildings = run_spine(case.slug, case.address)
    assert site.id == "261-AU6979"
    assert site.egid == "302060629"
    main = next(b for b in buildings if b.id == "302060629")
    assert main.floors == 9
    assert main.year == 2014
    assert main.footprint_m2 == 5565
    assert main.use and "1122" in main.use
    assert main.energy and "7410" in main.energy
    assert not main.missing_attributes
    assert parcel.slug == "zurich-AU6979"


def test_parcel_and_coordinate_inputs(replay: Callable[[str, str], int]) -> None:
    replay("ch/federal/geocode", "inputs-parcel")
    replay("ch/federal/geocode", "inputs-wgs84")
    replay("ch/federal/geocode", "inputs-lv95")
    by_parcel, _ = resolve_address("Parcel Zürich AU6979")
    by_wgs84, _ = resolve_address("47.3745, 8.5206")
    by_lv95, _ = resolve_address("2681718 1247636")
    assert by_parcel.parcel_ids == ["CH527182999120"]
    assert by_parcel.jurisdiction.bfs_number == 261
    assert by_wgs84.jurisdiction.municipality == "Zürich"
    assert abs(by_wgs84.coordinates.east - 2681718) < 30
    assert by_lv95.address.startswith("Badenerstrasse 171")


def test_fuzzy_wrong_postcode_lowers_confidence(replay: Callable[[str, str], int]) -> None:
    replay("ch/federal/geocode", "fuzzy-bern")
    site, _ = resolve_address("Bundesplatz 3, 3005 Bern")
    assert site.jurisdiction.municipality == "Bern"
    assert site.resolve_confidence < 0.7


def test_unresolvable_input_raises() -> None:
    with pytest.raises(ResolveError):
        resolve_address("   ")
    with pytest.raises(ResolveError):
        resolve_address("10.0, 10.0")
