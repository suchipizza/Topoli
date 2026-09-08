"""Build a report from recorded fixtures without network (CI, examples, Lighthouse).

    uv run python scripts/build_report_offline.py <slug> "<address>" <out_dir> [--lang xx]

Seeds a temporary cache from ``tests/fixtures/*/<slug>`` (+ ``_shared``), runs the pipeline
offline and writes ``<out_dir>/<municipality>-<parcel>/{index.html,evidence.json,…}``.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from topoli.core.adapters import HttpClient, set_client
from topoli.core.adapters.fixtures import fixture_folders, seed_cache
from topoli.core.adapters.registry import all_ids
from topoli.core.pipeline import build_result
from topoli.core.reporting.evidence_json import write_evidence
from topoli.core.reporting.html import render_html


def build(slug: str, address: str, out_dir: Path, lang: str | None = None) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        client = HttpClient(offline=True, cache_root=Path(tmp) / "cache")
        set_client(client)
        for adapter_id in all_ids():
            folders = fixture_folders(adapter_id, slug)
            if folders:
                seed_cache(Path(tmp) / "cache", *folders)
        result, run = build_result(address, lang=lang)  # type: ignore[arg-type]
        folder = write_evidence(result, run.records, root=out_dir)
        path, _ = render_html(result, folder, lang=result.lang, fetch_tiles=False)
        assert client.calls == 0, "offline build made a network call"
        return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("address")
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--lang", default=None)
    args = parser.parse_args(argv)
    path = build(args.slug, args.address, args.out_dir, args.lang)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
