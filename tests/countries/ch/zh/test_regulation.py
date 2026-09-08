"""BZO 2016 parser on the recorded ordinance text, zones.yaml drift check, potential calc."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from topoli.core.adapters import Record
from topoli.core.domain import (
    Building,
    EvidenceSpan,
    Jurisdiction,
    Parcel,
    Regulation,
    Rule,
    Source,
)
from topoli.core.scoring.potential import compute_potential
from topoli.countries.ch.zh.regulation.generate import GENERATED, render
from topoli.countries.ch.zh.regulation.parser import PARSER_VERSION, parse_bzo
from topoli.countries.ch.zh.regulation.source import bzo_text, bzo_version

SHARED = Path(__file__).resolve().parents[3] / "fixtures" / "ch" / "zh" / "regulation" / "_shared"


@pytest.fixture(scope="module")
def bzo() -> Record:
    meta = json.loads((SHARED / "meta.json").read_text(encoding="utf-8"))
    return Record.model_validate_json(
        (SHARED / meta["requests"][0]["file"]).read_text(encoding="utf-8")
    )


def test_recorded_text_is_the_consolidated_bzo(bzo: Record) -> None:
    text = bzo_text(bzo)
    assert "Bau- und Zonenordnung (BZO 2016)" in text
    assert bzo.payload["pages"] >= 50
    assert bzo_version(bzo).startswith("mit Änderungen bis")


@pytest.mark.parametrize(
    ("zone", "expected"),
    [
        (
            "W2",
            {
                "max_full_floors": 2,
                "max_building_height_m": 9.0,
                "floor_area_ratio": 60.0,
                "min_boundary_setback_m": 5.0,
                "max_boundary_setback_with_length_m": 10.0,
            },
        ),
        ("W3", {"max_full_floors": 3, "max_building_height_m": 9.5, "floor_area_ratio": 90.0}),
        (
            "W4",
            {
                "max_full_floors": 4,
                "max_building_height_m": 12.5,
                "floor_area_ratio": 120.0,
                "max_basement_floors": 0,
            },
        ),
        ("W5", {"max_full_floors": 5, "max_building_height_m": 15.5, "floor_area_ratio": 165.0}),
        (
            "W6",
            {
                "max_full_floors": 6,
                "max_building_height_m": 18.5,
                "floor_area_ratio": 205.0,
                "max_boundary_setback_with_length_m": 13.0,
            },
        ),
        ("W2bI", {"max_full_floors": 2, "floor_area_ratio": 40.0}),
        (
            "Z5",
            {
                "max_full_floors": 5,
                "max_building_height_m": 19.0,
                "floor_area_ratio": 200.0,
                "min_boundary_setback_m": 3.5,
            },
        ),
        ("Z7", {"max_full_floors": 7, "max_building_height_m": 25.0, "floor_area_ratio": 260.0}),
        (
            "IG III",
            {
                "max_full_floors": 7,
                "floor_area_ratio_commercial": 150.0,
                "building_mass_ratio": 12.0,
                "min_open_space_ratio": 15.0,
            },
        ),
        (
            "QI/5",
            {
                "max_full_floors": 5,
                "max_building_height_m": 18.0,
                "max_ridge_height_m": 5.0,
                "max_attic_floors": 2,
            },
        ),
        ("QI/7", {"max_full_floors": 7, "max_building_height_m": 25.0}),
        ("QII/3", {"max_full_floors": 3, "max_building_height_m": 11.5, "max_attic_floors": 1}),
        ("QIII/4", {"max_full_floors": 4, "max_building_height_m": 14.7}),
    ],
)
def test_extracted_values_match_the_ordinance(
    bzo: Record, zone: str, expected: dict[str, float]
) -> None:
    parsed = parse_bzo(bzo_text(bzo))
    rules = {r.key: r for r in parsed.zones[zone].rules}
    for key, value in expected.items():
        assert key in rules, f"{zone}: {key} unresolved ({parsed.zones[zone].unresolved})"
        assert float(rules[key].value) == value, (zone, key)
        span = rules[key].evidence_spans[0]
        assert span.article.startswith("Art. ") and span.text and span.url
        assert rules[key].parser_version == PARSER_VERSION


def test_industrial_has_no_general_floor_area_ratio(bzo: Record) -> None:
    parsed = parse_bzo(bzo_text(bzo))
    keys = {r.key for r in parsed.zones["IG II"].rules}
    assert "floor_area_ratio" not in keys and "floor_area_ratio_commercial" in keys


def test_plan_specific_zones_are_unresolved(bzo: Record) -> None:
    parsed = parse_bzo(bzo_text(bzo))
    for code in ("K", "F", "E", "Oe", "L"):
        assert not parsed.zones[code].rules and parsed.zones[code].unresolved


def test_zone_code_lookup(bzo: Record) -> None:
    parsed = parse_bzo(bzo_text(bzo))
    assert parsed.for_code("QI/5a") is parsed.zones["QI/5"]
    assert parsed.for_code("QIII/3b") is parsed.zones["QIII/3"]
    assert parsed.for_code("W4") is parsed.zones["W4"]
    assert parsed.for_code("Oe3") is None  # public-building zones carry their floors in the plan


def test_generated_zones_yaml_matches_a_fresh_parse(bzo: Record) -> None:
    """Drift check: regenerate with `python -m topoli.countries.ch.zh.regulation.generate`."""
    fresh = render(parse_bzo(bzo_text(bzo)), bzo_version(bzo))
    assert GENERATED.read_text(encoding="utf-8") == fresh


def _reg(zone: str, far: float | None) -> Regulation:
    src = Source(
        adapter_id="ch/zh/regulation",
        authority="Stadt Zürich",
        dataset="BZO 2016",
        licence="official-publication",
        url="https://oerebdocs.zh.ch/getDoc?docid=6",
        retrieved_at=None,
    )
    rules = []
    if far is not None:
        rules.append(
            Rule(
                key="floor_area_ratio",
                value=far,
                unit="%",
                evidence_spans=[
                    EvidenceSpan(document="BZO", article="Art. 13", text="Ausnützungsziffer max. …")
                ],
                parser_version="t",
            )
        )
    return Regulation(
        jurisdiction=Jurisdiction(country="CH", canton="ZH"),
        zone_code=zone,
        source_document=src,
        rules=rules,
        unresolved=[] if far else ["floor_area_ratio"],
        parser_version="t",
    )


def test_potential_headroom() -> None:
    parcel = Parcel(local_id="1", municipality="Zürich", area_m2=1000.0)
    buildings = [Building(id="1", floors=3, footprint_m2=200.0, floor_area_m2=400.0)]
    result = compute_potential(parcel, buildings, _reg("W4", 120.0))
    assert result.determined
    assert result.allowed_floor_area_m2 == 1200 and result.existing_floor_area_m2 == 400
    assert result.utilisation_pct == 33 and result.headroom_m2 == 800
    assert "120 % × 1000 m²" in result.derivation and "gebf" in result.inputs[2]
    # no energy reference area → storeys × footprint as an explicit upper bound
    gross = compute_potential(
        parcel, [Building(id="2", floors=3, footprint_m2=200.0)], _reg("W4", 120.0)
    )
    assert gross.determined and gross.existing_floor_area_m2 == 600
    assert "upper bound" in gross.inputs[2] and "upper bound" in gross.derivation


def test_potential_undetermined_cases() -> None:
    parcel = Parcel(local_id="1", municipality="Zürich", area_m2=1000.0)
    assert not compute_potential(parcel, [], None).determined
    q = compute_potential(parcel, [], _reg("QI/5a", None))
    assert not q.determined and "not set by a floor-area ratio" in q.reason
    missing = compute_potential(
        parcel, [Building(id="9", floors=None, footprint_m2=100.0)], _reg("W4", 120.0)
    )
    assert not missing.determined and "lacks floor area" in missing.reason
    assert missing.allowed_floor_area_m2 == 1200  # inputs still shown for layer 1
