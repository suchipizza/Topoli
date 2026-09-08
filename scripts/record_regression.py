"""Record fixtures for the 200-address regression set (WO-11), one full audit per address.

    uv run python scripts/record_regression.py [--limit N] [--only-missing]

Runs the real pipeline online with a fresh cache (shared records such as the BZO text and the
Baugesuche CSV are fetched once), then stores every record of the audit under
``tests/fixtures/<adapter_id>/<slug>/`` gzipped, skipping URLs already in ``_shared``.
Writes ``tests/regression/recorded.json`` with the recording date per address.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from topoli import __version__
from topoli.core.adapters import HttpClient, cache, set_client
from topoli.core.adapters.fixtures import fixtures_root, slugify
from topoli.core.pipeline import build_result

ADDRESSES = Path("tests/regression/addresses.csv")
RECORDED = Path("tests/regression/recorded.json")


def shared_urls(adapter_id: str) -> set[str]:
    meta = fixtures_root() / adapter_id / "_shared" / "meta.json"
    if not meta.is_file():
        return set()
    return {e["url"] for e in json.loads(meta.read_text(encoding="utf-8")).get("requests", [])}


def record_one(client: HttpClient, address: str, slug: str) -> dict[str, object]:
    client.recorded = []
    client.reset()
    t0 = time.perf_counter()
    result, _run = build_result(address)
    elapsed = time.perf_counter() - t0
    by_adapter: dict[str, list[dict[str, str]]] = {}
    for rec in client.recorded:
        if rec.url in shared_urls(rec.adapter_id):
            continue
        folder = fixtures_root() / rec.adapter_id / slug
        folder.mkdir(parents=True, exist_ok=True)
        path = cache.write(rec, root=fixtures_root() / "_tmp", compress=True)
        target = folder / path.name
        path.replace(target)
        by_adapter.setdefault(rec.adapter_id, []).append({"file": target.name, "url": rec.url})
    for adapter_id, requests in by_adapter.items():
        meta = {
            "adapter_id": adapter_id,
            "address": address,
            "site_id": result.site.id,
            "recorded_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "topoli_version": __version__,
            "requests": requests,
        }
        (fixtures_root() / adapter_id / slug / "meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return {
        "address": address,
        "slug": slug,
        "site_id": result.site.id,
        "canton": result.site.jurisdiction.canton,
        "calls": client.calls,
        "seconds": round(elapsed, 1),
        "adapters": sorted(by_adapter),
        "findings": len(result.findings),
        "coverage": {c.adapter_id: c.status for c in result.coverage},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only-missing", action="store_true")
    args = parser.parse_args(argv)
    rows = list(csv.DictReader(ADDRESSES.open(encoding="utf-8")))[: args.limit]
    done: dict[str, dict[str, object]] = (
        json.loads(RECORDED.read_text(encoding="utf-8")) if RECORDED.is_file() else {}
    )
    with tempfile.TemporaryDirectory() as tmp:
        client = HttpClient(cache_root=Path(tmp) / "cache", budget=100)
        set_client(client)
        for i, row in enumerate(rows, 1):
            address = row["address"]
            slug = slugify(address)
            if args.only_missing and slug in done:
                continue
            try:
                info = record_one(client, address, slug)
                done[slug] = info
                print(
                    f"[{i}/{len(rows)}] {address} → {info['calls']} calls, "
                    f"{info['seconds']}s, {info['findings']} findings",
                    flush=True,
                )
            except Exception as exc:
                done[slug] = {
                    "address": address,
                    "slug": slug,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                print(
                    f"[{i}/{len(rows)}] {address} → ERROR {type(exc).__name__}: {exc}", flush=True
                )
            RECORDED.write_text(
                json.dumps(done, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            time.sleep(0.2)
    shutil.rmtree(fixtures_root() / "_tmp", ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
