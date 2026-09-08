"""Live timing run (weekly): audits a few addresses online and writes docs/perf-<date>.md."""

from __future__ import annotations

import statistics
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from topoli.core.adapters import HttpClient, set_client
from topoli.core.pipeline import build_result

ADDRESSES = [
    "Badenerstrasse 171, 8003 Zürich",
    "Limmatquai 1, 8001 Zürich",
    "Technikumstrasse 9, 8400 Winterthur",
    "Bundesplatz 3, 3011 Bern",
    "Rue du Rhône 14, 1204 Genève",
    "Via Nassa 5, 6900 Lugano",
]


def main() -> int:
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for address in ADDRESSES:
            client = HttpClient(cache_root=Path(tmp) / "cache")
            set_client(client)
            t0 = time.perf_counter()
            result, _ = build_result(address)
            seconds = time.perf_counter() - t0
            rows.append((address, seconds, client.calls, len(result.findings)))
            print(f"{address}: {seconds:.1f}s, {client.calls} calls")
    times = [r[1] for r in rows]
    date = datetime.now(tz=UTC).date().isoformat()
    out = Path("docs") / f"perf-{date}.md"
    lines = [
        f"# Live timing run — {date}",
        "",
        "Cold cache, one audit per address, home connection. p50/p95 over the set.",
        "",
        "| Address | seconds | calls | findings |",
        "|---|---|---|---|",
        *[f"| {a} | {s:.1f} | {c} | {n} |" for a, s, c, n in rows],
        "",
        f"p50 = {statistics.median(times):.1f} s · "
        f"p95 = {sorted(times)[int(0.95 * (len(times) - 1))]:.1f} s · "
        f"budget ≤ 25 calls: {'ok' if max(r[2] for r in rows) <= 25 else 'EXCEEDED'}",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
