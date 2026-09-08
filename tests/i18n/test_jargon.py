"""Jargon ban for layer 0. ``assert_no_jargon`` is re-exported here for later layer-0 tests."""

from __future__ import annotations

import pytest

from topoli.core.domain import LANGS
from topoli.core.i18n import assert_no_jargon, find_jargon, jargon_entries

__all__ = ["assert_no_jargon"]


def test_entries_have_all_explanations_and_seed_terms() -> None:
    entries = jargon_entries()
    ids = {e.id for e in entries}
    for required in [
        "ausnuetzungsziffer",
        "baumassenziffer",
        "ueberbauungsziffer",
        "empfindlichkeitsstufe",
        "oereb",
        "density_indices_fr",
        "zone_codes",
        "isos",
        "kbs",
        "gestaltungsplan",
        "kernzone",
        "bzo",
        "pbg",
    ]:
        assert required in ids
    for e in entries:
        for lang in LANGS:
            assert e.explain(lang).strip(), f"{e.id} explanation missing for {lang}"
            assert "__TODO__" not in e.explain(lang)


@pytest.mark.parametrize(
    "text",
    [
        "Die Ausnützungsziffer beträgt 0.9.",
        "Zone W3, quatre niveaux.",
        "Le COS est de 0.4.",
        "Parcel lies in an ES III area.",
        "Extrait RDPPF disponible.",
        "Objekt im ISOS-Inventar",
        "Der KbS-Eintrag besteht.",
        "Ein Gestaltungsplan gilt.",
        "Das PBG regelt dies.",
        "The ÖREB extract lists three themes.",
    ],
)
def test_detects_jargon(text: str) -> None:
    assert find_jargon(text, "en"), text
    with pytest.raises(AssertionError, match="banned jargon"):
        assert_no_jargon(text, "en")


@pytest.mark.parametrize(
    "text",
    [
        "You could probably build more here.",
        "Flood risk: none identified in federal hazard layers.",
        "Sie könnten hier wahrscheinlich mehr bauen.",
        "Le bruit est élevé : la parcelle est dans une zone de bruit routier.",
        "Il rumore è alto lungo la ferrovia.",
        "Dieses Haus steht im kommunalen Inventar.",  # 'im' is not the FR index 'IM'
        "Wir wohnen im Zentrum, Westseite.",
        "The best W3C standards do not matter here.",  # W3C ≠ W3
        "Cost 1'234 CHF is never shown anyway.",
        "azimuth of the roof",  # not 'AZ'
    ],
)
def test_passes_plain_language(text: str) -> None:
    assert find_jargon(text, "en") == [], find_jargon(text, "en")
    assert_no_jargon(text, "de")


def test_hits_are_sorted_and_named() -> None:
    hits = find_jargon("W3 zone with Ausnützungsziffer 0.9 and ÖREB", "de")
    assert [h.entry_id for h in hits] == ["zone_codes", "ausnuetzungsziffer", "oereb"]
    assert hits[0].matched == "W3"
