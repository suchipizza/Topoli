"""Time-to-first-result (PRD §1): p50 ≤ 60 s, p95 ≤ 90 s, ≤ 25 calls per audit (WO-11).

Network time is replayed from the latencies recorded in each fixture (``request.elapsed_ms``);
compute time is measured offline. The sum per site is the end-to-end estimate.
"""

from __future__ import annotations

import gzip
import json
import statistics
import time
from pathlib import Path

import pytest

from topoli.core.adapters import HttpClient, set_client
from topoli.core.adapters.fixtures import fixture_folders, seed_cache, slugify
from topoli.core.adapters.registry import all_ids
from topoli.core.pipeline import build_result

HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "fixtures"
ADDRESSES = HERE / "regression" / "addresses.csv"


def _recorded_latency_ms(slug: str) -> tuple[float, int]:
    total, calls = 0.0, 0
    for meta in FIXTURES.rglob(f"*/{slug}/meta.json"):
        for entry in json.loads(meta.read_text(encoding="utf-8")).get("requests", []):
            path = meta.parent / entry["file"]
            raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
            rec = json.loads(raw)
            total += float(rec.get("request", {}).get("elapsed_ms", 0))
            calls += 1
    return total, calls


def _sites() -> list[tuple[str, str]]:
    import csv

    rows = list(csv.DictReader(ADDRESSES.open(encoding="utf-8")))
    out = []
    for row in rows:
        slug = slugify(row["address"])
        if (FIXTURES / "ch" / "federal" / "geocode" / slug / "meta.json").is_file():
            out.append((slug, row["address"]))
    return out


def test_time_to_first_result_and_budget(tmp_path: Path) -> None:
    sites = _sites()
    if len(sites) < 20:
        pytest.skip("regression fixtures not recorded")
    totals = []
    worst_calls = 0
    for slug, address in sites:
        client = HttpClient(offline=True, cache_root=tmp_path / slug)
        set_client(client)
        for adapter_id in all_ids():
            folders = fixture_folders(adapter_id, slug)
            if folders:
                seed_cache(tmp_path / slug, *folders)
        t0 = time.perf_counter()
        build_result(address)
        compute = time.perf_counter() - t0
        network_ms, calls = _recorded_latency_ms(slug)
        totals.append(compute + network_ms / 1000)
        worst_calls = max(worst_calls, calls)
    p50 = statistics.median(totals)
    p95 = sorted(totals)[int(0.95 * (len(totals) - 1))]
    print(f"\nsites={len(sites)} p50={p50:.1f}s p95={p95:.1f}s max_calls={worst_calls}")
    assert p50 <= 60, p50
    assert p95 <= 90, p95
    assert worst_calls <= 25, worst_calls
