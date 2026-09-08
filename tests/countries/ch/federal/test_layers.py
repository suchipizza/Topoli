"""Federal constraint layers replayed from recorded fixtures (WO-03).

Sites: Zürich Badenerstrasse 171 (runoff, ÖREB), Bern Bundesplatz 3 (KGS + UNESCO heritage,
noise sensitivity via ÖREB), Lugano Via Nassa 5 (ÖREB not introduced → not_available),
Zürich Limmatquai 1 (flood 100-year positive).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from topoli.core.adapters import get_client
from topoli.core.adapters.registry import all_specs
from topoli.core.pipeline import LayerRun, resolve_spine, run_layers

LAYER_IDS = [
    "ch/federal/hazards",
    "ch/federal/noise",
    "ch/federal/contamination",
    "ch/federal/oereb",
    "ch/federal/solar",
    "ch/federal/heritage",
    "ch/federal/terrain",
]


@pytest.fixture
def run_site(replay: Callable[[str, str], int]) -> Callable[[str, str], LayerRun]:
    def _run(slug: str, address: str) -> LayerRun:
        for adapter_id in LAYER_IDS:
            replay(adapter_id, slug)
        get_client().reset()
        ctx, _, _ = resolve_spine(address)
        return run_layers(ctx)

    return _run


def test_registry_has_seven_federal_layers() -> None:
    assert [s.id for s in all_specs("federal")] == LAYER_IDS


def test_zurich_badenerstrasse(run_site: Callable[[str, str], LayerRun]) -> None:
    run = run_site("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich")
    assert get_client().calls == 0
    assert {c.adapter_id for c in run.coverage} == set(LAYER_IDS)
    assert all(c.status == "ok" for c in run.coverage), [
        (c.adapter_id, c.detail) for c in run.coverage
    ]
    assert len(run.findings) >= 7
    for f in run.findings:
        assert f.source.url and f.source.retrieved_at, f.id
        assert f.title.en and f.consequence.en and f.caveat.en
        assert f.cls in ("A", "B")
    by_id = {f.id: f for f in run.findings}
    assert by_id["hazard.flood"].template_key == "hazard.flood.none"
    runoff = by_id["hazard.runoff"]
    assert runoff.template_key == "hazard.runoff.low" and runoff.cls == "B"
    assert runoff.geometry_intersection and 0.05 < runoff.geometry_intersection.fraction < 0.5
    assert by_id["noise.road"].template_key.startswith("noise.road.")  # type: ignore[union-attr]
    assert by_id["contamination.federal"].template_key == "contamination.none"
    oereb = [f for f in run.findings if f.id.startswith("oereb.")]
    assert len(oereb) >= 5
    assert any("Nutzungsplanung" in f.slots["theme"] for f in oereb)
    assert all(f.evidence_spans for f in oereb), "every ÖREB theme carries legal provisions"
    assert by_id["solar.best_roof"].slots["klasse"] in {"1", "2", "3", "4", "5"}
    assert by_id["terrain.slope"].template_key == "terrain.flat"


def test_bern_bundesplatz_heritage_and_noise_sensitivity(
    run_site: Callable[[str, str], LayerRun],
) -> None:
    run = run_site("bern-bundesplatz-3", "Bundesplatz 3, 3011 Bern")
    assert get_client().calls == 0
    ids = {f.id for f in run.findings}
    assert "heritage.kgs.KGS_NR615" in ids, "Bundeshaus is KGS object 615"
    assert any(i.startswith("heritage.unesco.") for i in ids)
    kgs = next(f for f in run.findings if f.id == "heritage.kgs.KGS_NR615")
    assert kgs.severity == "high" and kgs.slots["category"].startswith("A")
    assert any("Lärmempfindlichkeitsstufen" in f.slots.get("theme", "") for f in run.findings)
    assert next(f for f in run.findings if f.id == "terrain.slope").template_key == "terrain.sloped"


def test_lugano_oereb_not_available(run_site: Callable[[str, str], LayerRun]) -> None:
    run = run_site("lugano-via-nassa-5", "Via Nassa 5, 6900 Lugano")
    assert get_client().calls == 0
    oereb = next(c for c in run.coverage if c.adapter_id == "ch/federal/oereb")
    assert oereb.status == "not_available"
    assert oereb.detail and "geplant" in oereb.detail
    unknown = next(f for f in run.findings if f.id == "unknown.ch.federal.oereb")
    assert unknown.cls == "D" and unknown.slots["where"] == "TI"
    others = [c for c in run.coverage if c.adapter_id != "ch/federal/oereb"]
    assert all(c.status == "ok" for c in others)
    flood = next(f for f in run.findings if f.id == "hazard.flood")
    assert flood.template_key == "hazard.flood.low"


def test_limmatquai_flood_positive(run_site: Callable[[str, str], LayerRun]) -> None:
    run = run_site("zurich-limmatquai-1", "Limmatquai 1, 8001 Zürich")
    flood = next(f for f in run.findings if f.id == "hazard.flood")
    assert flood.template_key == "hazard.flood.medium"
    assert flood.cls == "B" and flood.severity == "high"
    assert flood.geometry_intersection and flood.geometry_intersection.fraction > 0.01
    assert "Aquaprotect" in (flood.derivation or "")


def test_call_budget_per_audit_is_documented(run_site: Callable[[str, str], LayerRun]) -> None:
    run = run_site("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich")
    # spine 5 + layers 14 = 19 ≤ 25 (decision 004); counted from cache hits since we are offline
    assert get_client().cache_hits <= 25
    assert sum(len(v) for v in run.records.values()) == 14
