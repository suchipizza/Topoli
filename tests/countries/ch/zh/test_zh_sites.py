"""Zürich adapters replayed from fixtures: zoning (5+ families), rules, potential, heritage."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from topoli.core.adapters import get_client
from topoli.core.pipeline import LayerRun, resolve_spine, run_cantonal

ZH_IDS = ["ch/zh/zoning", "ch/zh/regulation", "ch/zh/heritage"]

SITES: list[tuple[str, str, str, str | None]] = [
    # slug, address, expected zone code, expected potential template (None = no regulation)
    (
        "zurich-badenerstrasse-171",
        "Badenerstrasse 171, 8003 Zürich",
        "QI/5a",
        "potential.undetermined",
    ),
    (
        "zurich-seefeldstrasse-80",
        "Seefeldstrasse 80 8008 Zürich",
        "QI/5a",
        "potential.undetermined",
    ),
    ("zurich-limmatquai-1", "Limmatquai 1, 8001 Zürich", "K", "potential.undetermined"),
    ("zurich-bahnhofstrasse-25", "Bahnhofstrasse 25, 8001 Zürich", "K", "potential.undetermined"),
    ("zurich-hardturmstrasse-181", "Hardturmstrasse 181, 8005 Zürich", "Z6", None),
    ("zurich-dolderstrasse-40", "Dolderstrasse 40, 8032 Zürich", "W4", None),
    ("zurich-schaffhauserstrasse-59", "Schaffhauserstrasse 59, 8057 Zürich", "W6", None),
    (
        "zurich-albisriederstrasse-200",
        "Albisriederstrasse 200, 8047 Zürich",
        "Oe3",
        "potential.undetermined",
    ),
    ("zurich-bergstrasse-100", "Bergstrasse 100, 8032 Zürich", "QII/3", "potential.undetermined"),
    ("zurich-zuerichbergstrasse-50", "Zürichbergstrasse 50, 8044 Zürich", "W2", None),
    ("zurich-kalchbuehlstrasse-60", "Kalchbühlstrasse 60, 8038 Zürich", "W4", None),
    ("zurich-witikonerstrasse-250", "Witikonerstrasse 250, 8053 Zürich", "W2bI", None),
    ("zurich-witikonerstrasse-330", "Witikonerstrasse 330, 8053 Zürich", "W3", None),
]


@pytest.fixture
def run_zh(replay: Callable[[str, str], int]) -> Callable[[str, str], LayerRun]:
    def _run(slug: str, address: str) -> LayerRun:
        for adapter_id in ZH_IDS:
            replay(adapter_id, slug)
        get_client().reset()
        ctx, _, _ = resolve_spine(address)
        run = LayerRun(ctx=ctx)
        return run_cantonal(run)

    return _run


@pytest.mark.parametrize(("slug", "address", "zone", "potential"), SITES, ids=[s[0] for s in SITES])
def test_city_of_zurich_site(
    run_zh: Callable[[str, str], LayerRun],
    slug: str,
    address: str,
    zone: str,
    potential: str | None,
) -> None:
    run = run_zh(slug, address)
    assert get_client().calls == 0
    assert run.ctx.parcel is not None and run.ctx.parcel.zoning_code == zone
    assert {c.adapter_id for c in run.coverage} == set(ZH_IDS)
    assert all(c.status == "ok" for c in run.coverage), [
        (c.adapter_id, c.detail) for c in run.coverage
    ]
    zoning = next(f for f in run.findings if f.id == "zoning.zone")
    assert zoning.cls == "A" and zoning.slots["code"] == zone and zoning.source.url
    assert run.regulations and run.regulations[0].zone_code == zone
    reg = run.regulations[0]
    assert reg.parser_version.startswith("bzo2016-parser/")
    rules_finding = next(f for f in run.findings if f.id == "regulation.rules")
    if reg.rules:
        assert rules_finding.cls == "A" and rules_finding.evidence_spans
        assert all(r.evidence_spans[0].article.startswith("Art.") for r in reg.rules)
    else:
        assert rules_finding.cls == "D" and reg.unresolved
    pot = next(f for f in run.findings if f.id == "potential.headroom")
    if potential is None:
        assert pot.template_key in ("potential.headroom", "potential.full"), pot.template_key
        assert pot.cls == "C" and pot.derivation and "inputs:" in pot.derivation
        assert pot.evidence_spans and pot.rule_ref == "floor_area_ratio"
        assert run.potential and run.potential.determined
    else:
        assert pot.template_key == potential and pot.cls == "D"


def test_zone_families_covered() -> None:
    families = {z.rstrip("0123456789abI/").rstrip("/") for _, _, z, _ in SITES}
    assert {"Q", "K", "Z", "W", "Oe"} <= {f[:2] if f.startswith("Oe") else f[0] for f in families}
    assert len({z for _, _, z, _ in SITES}) >= 8


def test_winterthur_zone_code_but_rules_not_contributed(
    run_zh: Callable[[str, str], LayerRun],
) -> None:
    run = run_zh("winterthur-technikumstrasse-9", "Technikumstrasse 9, 8400 Winterthur")
    assert run.ctx.parcel is not None and run.ctx.parcel.zoning_code == "Oe"
    cov = {c.adapter_id: c for c in run.coverage}
    assert cov["ch/zh/zoning"].status == "ok"
    assert cov["ch/zh/regulation"].status == "not_contributed"
    assert cov["ch/zh/regulation"].detail and "Winterthur" in cov["ch/zh/regulation"].detail
    stub = next(f for f in run.findings if f.id == "unknown.ch.zh.regulation")
    assert stub.cls == "D" and "not yet contributed" in stub.slots["reason"]
    assert run.potential is None


def test_bahnhofstrasse_listed_building(run_zh: Callable[[str, str], LayerRun]) -> None:
    run = run_zh("zurich-bahnhofstrasse-25", "Bahnhofstrasse 25, 8001 Zürich")
    listed = [
        f for f in run.findings if f.id.startswith("heritage.zh.") and f.id != "heritage.zh.none"
    ]
    assert listed, "Credit Suisse building at Paradeplatz is a cantonal protected object"
    assert listed[0].cls == "A" and listed[0].severity == "high"
    assert listed[0].slots["level"] in ("kantonal", "kommunal")


def test_unlisted_parcel_reports_none(run_zh: Callable[[str, str], LayerRun]) -> None:
    run = run_zh("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich")
    assert any(f.id == "heritage.zh.none" for f in run.findings)
