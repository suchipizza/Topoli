"""200-address regression (PRD §10, WO-11): every audit completes offline from recorded fixtures.

Per address: no exception, a coverage entry for every registered adapter, layer 0 valid in four
languages, every class-A/B finding sourced, and the layer-0 snapshot (finding ids + classes)
matches ``expected/<slug>.json`` (update with ``TOPOLI_UPDATE_EXPECTED=1``).
Acceptance (asserted once at the end): ≥ 95 % of City of Zürich addresses and ≥ 80 % elsewhere
yield a *complete* layer 0 (3–5 findings, spine + ≥ 6 federal layers ok).
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from topoli.core.adapters import HttpClient, set_client
from topoli.core.adapters.fixtures import fixture_folders, seed_cache, slugify
from topoli.core.adapters.registry import all_ids, all_specs
from topoli.core.domain import LANGS
from topoli.core.i18n import find_jargon
from topoli.core.pipeline import build_result
from topoli.core.reporting.layer0 import render_layer0

HERE = Path(__file__).resolve().parent
ADDRESSES = list(csv.DictReader((HERE / "addresses.csv").open(encoding="utf-8")))
EXPECTED = HERE / "expected"
RESULTS: dict[str, dict[str, object]] = {}
FEDERAL_LAYERS = [s.id for s in all_specs("federal")]


def _recorded(slug: str) -> bool:
    return (Path("tests/fixtures/ch/federal/geocode") / slug / "meta.json").is_file() or (
        HERE.parents[1] / "tests" / "fixtures" / "ch" / "federal" / "geocode" / slug / "meta.json"
    ).is_file()


@pytest.mark.parametrize("row", ADDRESSES, ids=[slugify(r["address"]) for r in ADDRESSES])
def test_audit(row: dict[str, str], tmp_path: Path) -> None:
    address, group = row["address"], row["group"]
    slug = slugify(address)
    if not _recorded(slug):
        pytest.skip("fixtures not recorded yet — run scripts/record_regression.py")
    client = HttpClient(offline=True, cache_root=tmp_path / "cache")
    set_client(client)
    for adapter_id in all_ids():
        folders = fixture_folders(adapter_id, slug)
        if folders:
            seed_cache(tmp_path / "cache", *folders)
    result, _ = build_result(address)
    assert client.calls == 0

    covered = {c.adapter_id: c.status for c in result.coverage}
    expected_adapters = {a for a in all_ids() if a.startswith("ch/federal/")}
    if result.site.jurisdiction.canton == "ZH":
        expected_adapters |= {a for a in all_ids() if a.startswith("ch/zh/")}
    assert expected_adapters <= set(covered), sorted(expected_adapters - set(covered))
    for f in result.findings:
        if f.cls in ("A", "B"):
            assert f.source.url and f.source.retrieved_at, f.id

    layer0_ids: list[tuple[str, str]] = []
    for lang in LANGS:
        layer0 = render_layer0(result.site, result.findings, lang, regulations=result.regulations)
        assert 3 <= len(layer0.findings) <= 5, (lang, [f.id for f in layer0.findings])
        for _icon, title, consequence in layer0.lines:
            assert not find_jargon(title + " " + consequence, lang), (lang, title)
        assert layer0.next_step.text
        if lang == "de":
            layer0_ids = [(f.id, f.cls) for f in layer0.findings]

    spine_ok = all(
        covered.get(a) == "ok"
        for a in ("ch/federal/geocode", "ch/federal/parcel", "ch/federal/buildings")
    )
    federal_ok = sum(1 for a in FEDERAL_LAYERS if covered.get(a) == "ok")
    complete = spine_ok and federal_ok >= 6 and 3 <= len(layer0_ids) <= 5
    RESULTS[slug] = {
        "group": group,
        "complete": complete,
        "federal_ok": federal_ok,
        "calls": len(result.coverage),
    }

    snapshot = json.loads(
        json.dumps({"address": address, "layer0_de": layer0_ids, "coverage": covered})
    )
    path = EXPECTED / f"{slug}.json"
    if os.environ.get("TOPOLI_UPDATE_EXPECTED") == "1" or not path.is_file():
        path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    else:
        expected = json.loads(path.read_text(encoding="utf-8"))
        assert snapshot["layer0_de"] == expected["layer0_de"], (
            f"layer-0 snapshot changed for {address}: {snapshot['layer0_de']} != "
            f"{expected['layer0_de']} (TOPOLI_UPDATE_EXPECTED=1 to accept)"
        )
        assert snapshot["coverage"] == expected["coverage"]


def test_acceptance_rates() -> None:
    if len(RESULTS) < 20:
        pytest.skip("regression fixtures not recorded")
    rates = {}
    for group, minimum in (("zh_city", 0.95), ("zh_other", 0.80), ("other", 0.80)):
        rows = [r for r in RESULTS.values() if r["group"] == group]
        if not rows:
            continue
        rate = sum(1 for r in rows if r["complete"]) / len(rows)
        rates[group] = (rate, len(rows), minimum)
    print("\nacceptance:", {g: f"{r:.0%} of {n} (min {m:.0%})" for g, (r, n, m) in rates.items()})
    for group, (rate, _n, minimum) in rates.items():
        assert rate >= minimum, f"{group}: {rate:.0%} < {minimum:.0%}"
