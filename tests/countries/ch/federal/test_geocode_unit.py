from __future__ import annotations

from topoli.countries.ch.federal.geocode import _coords_from_pair, _pick


def test_pick_prefers_postcode_match() -> None:
    hits = [
        {"attrs": {"detail": "bahnhofstrasse 1 8001 zuerich 261 zuerich ch zh"}},
        {"attrs": {"detail": "bahnhofstrasse 1 8400 winterthur 230 winterthur ch zh"}},
    ]
    best, conf = _pick("Bahnhofstrasse 1 8400 Winterthur", hits, fuzzy=False)
    assert "winterthur" in best["attrs"]["detail"]
    assert conf == 0.95


def test_pick_penalises_fuzzy_and_missing_postcode() -> None:
    hits = [{"attrs": {"detail": "bundesplatz 3 3011 bern 351 bern ch be"}}]
    _, conf = _pick("Bundesplatz 3 3005 Bern", hits, fuzzy=True)
    assert conf == 0.5


def test_coords_from_pair_accepts_both_crs() -> None:
    e, n = _coords_from_pair(47.3745, 8.5206)
    assert abs(e - 2681718) < 30 and abs(n - 1247636) < 30
    assert _coords_from_pair(2681718, 1247636) == (2681718, 1247636)
