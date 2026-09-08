"""Layer 0 contract (PRD §3.3) for every recorded site and every language:
3–5 findings, no jargon, one next step, confidence counts match the shown classes,
numbers rounded to two significant figures."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable

import pytest

from topoli.core.adapters import get_client
from topoli.core.domain import LANGS, Lang
from topoli.core.pipeline import build_result
from topoli.core.reporting.assemble import assemble
from topoli.core.reporting.layer0 import render_layer0, round_sig, round_sig_text
from topoli.core.scoring.rank import goal_profile, rank, select_layer0

SITES = [
    ("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich"),
    ("zurich-limmatquai-1", "Limmatquai 1, 8001 Zürich"),
    ("bern-bundesplatz-3", "Bundesplatz 3, 3011 Bern"),
    ("lugano-via-nassa-5", "Via Nassa 5, 6900 Lugano"),
]
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
def audited(replay: Callable[[str, str], int]):  # type: ignore[no-untyped-def]
    def _run(slug: str, address: str, lang: Lang, goal: str | None = None):  # type: ignore[no-untyped-def]
        for adapter_id in ADAPTERS:
            # not every site has every adapter recorded (e.g. no ZH data for Bern)
            with contextlib.suppress(AssertionError):
                replay(adapter_id, slug)
        get_client().reset()
        result, _ = build_result(address, lang=lang, goal=goal)
        return result

    return _run


@pytest.mark.parametrize("lang", LANGS)
@pytest.mark.parametrize(("slug", "address"), SITES, ids=[s[0] for s in SITES])
def test_layer0_contract(audited, slug: str, address: str, lang: Lang) -> None:  # type: ignore[no-untyped-def]
    from tests.i18n.test_jargon import assert_no_jargon

    result = audited(slug, address, lang)
    assert get_client().calls == 0
    layer0 = render_layer0(result.site, result.findings, lang, regulations=result.regulations)
    assert 3 <= len(layer0.findings) <= 5, [f.id for f in layer0.findings]
    families = [f.id.split(".")[0] for f in layer0.findings]
    assert len(families) == len(set(families)), "one finding per family on layer 0"
    for _icon, title, consequence in layer0.lines:
        assert_no_jargon(title, lang)
        assert_no_jargon(consequence, lang)
        assert "__TODO__" not in title + consequence
        for num in re.findall(r"(?<![\w.,/-])(\d{3,})(?![\w.-])", title + " " + consequence):
            if not 1800 <= int(num) <= 2100:
                assert round_sig(int(num)) == int(num), f"{num} not rounded in {lang}: {title}"
    assert layer0.text.count(layer0.next_step.text) == 1
    assert layer0.confidence in layer0.text
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for f in layer0.findings:
        counts[f.cls] += 1
    assert counts == layer0.counts
    assert layer0.header.startswith(
        ("PROPERTY CHECK", "CHECK IMMOBILIER", "IMMOBILIEN-CHECK", "CHECK IMMOBILIARE")
    )
    layer1 = assemble(result, lang, layer0.findings)
    assert len(layer1.sections) == 18
    assert layer1.sources or not layer1.sections[17].available


def test_goal_changes_ranking(audited) -> None:  # type: ignore[no-untyped-def]
    result = audited("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich", "de")
    assert goal_profile("Ich will 12 Wohnungen bauen")[0] == "build"
    assert goal_profile("acheter pour rénover")[0] in ("buy", "renovate")
    assert goal_profile(None)[0] == "balanced"
    build = [f.id for f in select_layer0(result.findings, "de", goal="bauen")]
    buy = [f.id for f in select_layer0(result.findings, "de", goal="kaufen")]
    assert build != buy or len(result.findings) < 8
    ranked = rank(result.findings, "bauen")
    assert ranked == sorted(ranked, key=lambda f: (-f.rank_score, f.id))


def test_round_sig_text() -> None:
    assert round_sig_text("about 1388 m² and 2136 m²") == "about 1400 m² and 2100 m²"
    assert round_sig_text("built in 1928, 4 floors") == "built in 1928, 4 floors"
    assert round_sig_text("zone W4 parcel AU6979, Art. 13") == "zone W4 parcel AU6979, Art. 13"
    assert round_sig_text("14% of the plot, 62 dB") == "14% of the plot, 62 dB"
    assert round_sig(1388) == 1400 and round_sig(0.453, 2) == 0.45 and round_sig(95267) == 95000


@pytest.mark.parametrize("lang", LANGS)
def test_pinned_top_findings_badenerstrasse(audited, lang: Lang) -> None:  # type: ignore[no-untyped-def]
    result = audited("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich", lang)
    top = [f.id for f in select_layer0(result.findings, lang)]
    assert "activity.nearby" in top and "hazard.runoff" in top
    assert top[0] in ("activity.nearby", "hazard.runoff", "noise.road", "solar.best_roof")
