#!/usr/bin/env python3
"""Single entry point the skill runs.

``python audit.py "<address>" [--lang xx] [--goal ...] [--depth quick|full] [--json]``

Runs the whole deterministic pipeline (resolve → parcel → buildings → federal layers → Zürich
zoning/regulation/heritage → construction events → ranking), prints progress lines, then the
layer-0 text verbatim and the report path. Claude presents the output unchanged.

Works from a checkout (``uv run python skills/property-audit/scripts/audit.py …``) or wherever
the ``topoli`` package is installed (``python audit.py …``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap() -> None:
    """Make ``topoli`` importable when run straight from the skill folder of a checkout."""
    try:
        import topoli  # noqa: F401
    except ImportError:
        root = Path(__file__).resolve().parents[3]
        if (root / "topoli" / "__init__.py").is_file():
            sys.path.insert(0, str(root))


def main(argv: list[str] | None = None) -> int:
    _bootstrap()
    from topoli.core.adapters import get_client
    from topoli.core.i18n import t
    from topoli.core.pipeline import build_result
    from topoli.core.reporting.card import render_cards
    from topoli.core.reporting.evidence_json import write_evidence
    from topoli.core.reporting.html import render_html
    from topoli.core.reporting.layer0 import render_layer0
    from topoli.core.reporting.summary import summary_text, write_summary
    from topoli.countries.ch.federal.geocode import ResolveError

    parser = argparse.ArgumentParser(description="Topoli property audit")
    parser.add_argument("address")
    parser.add_argument("--lang", choices=["fr", "de", "it", "en"], default=None)
    parser.add_argument("--goal", default=None)
    parser.add_argument("--depth", choices=["quick", "full"], default="quick")
    parser.add_argument("--json", action="store_true", help="print the AuditResult JSON")
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--stats", action="store_true", help="print timings and call counts")
    args = parser.parse_args(argv)

    try:
        result, run = build_result(args.address, lang=args.lang, goal=args.goal)
    except ResolveError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 2
    lang = result.lang
    cov = {c.adapter_id: c for c in result.coverage}

    def line(text: str) -> None:
        print(text, flush=True)

    line(t("progress.resolved", lang))
    parcel = result.parcels[0] if result.parcels else None
    if parcel:
        line(t("progress.parcel", lang, parcel=parcel.local_id))
    line(t("progress.buildings", lang, n=len(result.buildings)))
    federal = [
        a
        for a in cov
        if a.startswith("ch/federal/")
        and a not in ("ch/federal/geocode", "ch/federal/parcel", "ch/federal/buildings")
    ]
    line(t("progress.layers", lang, n=sum(1 for a in federal if cov[a].status == "ok")))
    if "ch/zh/regulation" in cov and cov["ch/zh/regulation"].status == "ok":
        line(t("progress.regulation", lang))
    if "ch/zh/construction_events" in cov and cov["ch/zh/construction_events"].status == "ok":
        line(t("progress.events", lang))
    where = result.site.jurisdiction.municipality or result.site.jurisdiction.canton or "CH"
    for c in result.coverage:
        if c.status in ("not_available", "not_contributed"):
            line(t("progress.not_available", lang, what=c.adapter_id, where=where))
        elif c.status == "degraded":
            line(t("progress.degraded", lang, what=c.adapter_id, date=c.detail or "—"))
    line("")

    if args.json:
        print(result.model_dump_json(by_alias=True, indent=1))
        return 0

    oereb = cov.get("ch/federal/oereb")
    oereb_ok = bool(oereb and oereb.status == "ok")
    report_path = "./index.html"
    if not args.no_report:
        out_dir = write_evidence(result, run.records)
        report_path = str(out_dir / "index.html")
    layer0 = render_layer0(
        result.site,
        result.findings,
        lang,
        goal=args.goal,
        regulations=result.regulations,
        oereb_available=oereb_ok,
        report_path=report_path,
        card_path=report_path.replace("index.html", "card.png"),
    )
    if not args.no_report:
        write_summary(layer0, out_dir)
        render_html(
            result,
            out_dir,
            lang=lang,
            goal=args.goal,
            fetch_tiles=True,
            summary_text=summary_text(layer0),
            card_png="card.png",
        )
        map_img = out_dir / "map.jpg"
        render_cards(layer0, out_dir, map_image=map_img if map_img.is_file() else None)
    print(layer0.text)

    if args.depth == "full":
        from topoli.core.reporting.assemble import assemble

        layer1 = assemble(result, lang, layer0.findings)
        for s in layer1.sections:
            print(f"\n{s.number}. {s.title}")
            if not s.available:
                print(f"   {s.stub}")
                continue
            for k, v in s.facts:
                print(f"   {k}: {v}")
            for tline in s.text:
                print(f"   {tline}")
            for f in s.findings:
                print(f"   [{f.cls}] {f.title.get(lang)}")
                print(f"       {f.consequence.get(lang)}")
        print("\n18. sources")
        for r in layer1.sources:
            print(f"   {r.dataset} · {r.authority} · {r.retrieved_at} · {r.url}")

    if args.stats:
        client = get_client()
        print(f"\ncalls: {client.calls} network · {client.cache_hits} cache", file=sys.stderr)
        for tm in result.timings:
            print(f"  {tm.step}: {tm.seconds:.2f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
