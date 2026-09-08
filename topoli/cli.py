"""``topoli`` command-line interface.

Phase 1 commands are added work order by work order. This module ships
``--version`` and ``doctor`` (WO-00); later WOs add ``resolve``, ``parcel``,
``buildings``, ``layers``, ``audit``, ``render``, ``fixtures``, ``cache``, ``coverage``.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

from topoli import __version__
from topoli.paths import cache_dir

app = typer.Typer(
    name="topoli",
    help="Open-source construction intelligence for AI agents.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

MIN_PYTHON = (3, 11)
# Reachability probe only; adapters document their exact endpoints in their own docstrings.
GEOADMIN_PROBE_URL = "https://api3.geo.admin.ch/rest/services/api/SearchServer"


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"topoli {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show the Topoli version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Bypass the local cache in ~/.topoli/cache for this run."
    ),
) -> None:
    """Topoli command-line interface."""
    if no_cache:
        from topoli.core.adapters import HttpClient, set_client

        set_client(HttpClient(use_cache=False))


@app.command()
def layers(
    address: str = typer.Argument(..., help="Address, 'Parcel <municipality> <no>' or 'lat,lon'"),
    lang: str | None = typer.Option(None, "--lang", help="fr|de|it|en (default: canton)"),
) -> None:
    """Run the federal spine + the seven federal constraint layers and print the findings."""
    from topoli.core.pipeline import audit_layers
    from topoli.countries.ch.federal.geocode import ResolveError

    try:
        run, spine_cov, _ = audit_layers(address)
    except ResolveError as exc:
        console.print(f"[red]Could not resolve:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    out_lang = lang or run.ctx.site.lang_default
    console.print(f"[bold]{run.ctx.site.address}[/bold] · {run.ctx.site.jurisdiction.canton}")
    for f in run.findings:
        badge = {"A": "green", "B": "cyan", "C": "yellow", "D": "magenta"}[f.cls]
        console.print(f"{f.icon or '•'} [{badge}]{f.cls}[/{badge}] {f.title.get(out_lang)}")  # type: ignore[arg-type]
        console.print(f"    {f.consequence.get(out_lang)}")  # type: ignore[arg-type]
        when = f.source.retrieved_at.strftime("%Y-%m-%d") if f.source.retrieved_at else "—"
        url = (f.source.url or "—")[:90]
        console.print(f"    [dim]{f.source.dataset[:60]} · {when} · {url}[/dim]")
    table = Table(title="coverage")
    for col in ("adapter", "status", "calls", "detail"):
        table.add_column(col)
    for c in [*spine_cov, *run.coverage]:
        table.add_row(c.adapter_id, c.status, str(c.calls), c.detail or "")
    console.print(table)
    console.print(_calls_line())


@app.command()
def regulation(
    address: str = typer.Argument(..., help="Address in the Canton of Zürich"),
) -> None:
    """Zone, extracted building rules with article spans, and the development-potential estimate."""
    from topoli.core.pipeline import audit_layers
    from topoli.countries.ch.federal.geocode import ResolveError

    try:
        run, _, _ = audit_layers(address)
    except ResolveError as exc:
        console.print(f"[red]Could not resolve:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    parcel = run.ctx.parcel
    console.print(
        f"[bold]{run.ctx.site.address}[/bold] · parcel {parcel.local_id if parcel else '–'}"
    )
    code = parcel.zoning_code if parcel else "–"
    name = parcel.zoning_name if parcel else ""
    console.print(f"zone: [bold]{code}[/bold] — {name}")
    for reg in run.regulations:
        title = f"rules for {reg.zone_code} · {reg.source_document.dataset} · {reg.parser_version}"
        table = Table(title=title)
        for col in ("rule", "value", "unit", "article", "span"):
            table.add_column(col, overflow="fold")
        for r in reg.rules:
            sp = r.evidence_spans[0]
            table.add_row(r.key, str(r.value), r.unit or "", sp.article, sp.text[:90])
        console.print(table)
        if reg.unresolved:
            console.print(f"[yellow]unresolved (class D):[/yellow] {', '.join(reg.unresolved)}")
    cov = {c.adapter_id: c for c in run.coverage}
    for aid in ("ch/zh/zoning", "ch/zh/regulation", "ch/zh/heritage"):
        if aid in cov:
            console.print(f"{aid}: {cov[aid].status} {cov[aid].detail or ''}")
    if run.potential:
        p = run.potential
        console.print(
            "[bold]potential[/bold]:",
            "determined" if p.determined else f"undetermined — {p.reason}",
        )
        if p.derivation:
            console.print(f"  {p.derivation}")
        for line in p.inputs:
            console.print(f"  · {line}")
    console.print(_calls_line())


@app.command()
def events(
    address: str = typer.Argument(..., help="Address in the Canton of Zürich"),
    radius: float = typer.Option(500.0, "--radius", help="Search radius in metres"),
    since: int = typer.Option(12, "--since", help="Months back"),
) -> None:
    """Building publications near the address, normalized, newest first."""
    from topoli.core.adapters import get_client
    from topoli.core.adapters.base import SiteContext
    from topoli.core.pipeline import resolve_spine
    from topoli.core.scoring.activity import summarize
    from topoli.countries.ch.federal.geocode import ResolveError
    from topoli.countries.ch.zh.construction_events import ConstructionEventsAdapter, portal_page

    get_client().reset()
    try:
        ctx, _, _ = resolve_spine(address)
    except ResolveError as exc:
        console.print(f"[red]Could not resolve:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    adapter = ConstructionEventsAdapter()
    adapter.radius_m = radius
    adapter.since_months = since
    records = adapter.fetch(SiteContext(site=ctx.site, parcel=ctx.parcel, buildings=ctx.buildings))
    found, stats = adapter.events(records, ctx)
    summary = summarize(found, radius_m=radius, since=None)
    console.print(
        f"[bold]{ctx.site.address}[/bold] · {summary.count} events within {radius:.0f} m · {stats}"
    )
    table = Table(title="construction publications")
    for col in ("date", "m", "type", "description", "applicant", "author", "source"):
        table.add_column(col, overflow="fold")
    for e in found:
        table.add_row(
            e.publication_date.isoformat(),
            f"{e.distance_m:.0f}" if e.distance_m else "",
            e.type,
            e.description[:70],
            e.applicant or "",
            e.project_author or "",
            portal_page(e),
        )
    console.print(table)
    console.print(_calls_line())


review_app = typer.Typer(help="Professional review harness (PRD §10).")
app.add_typer(review_app, name="review")


@review_app.command("export")
def review_export(
    addresses: Path = typer.Option(  # noqa: B008
        ..., "--addresses", help="Text file, one address per line"
    ),
    out: Path = typer.Option(  # noqa: B008
        Path("tests/review/export.csv"), "--out", help="CSV to write"
    ),
) -> None:
    """Audit every address and write a spreadsheet-friendly CSV for the reviewing architect."""
    import csv

    from topoli.core.pipeline import audit_layers

    rows: list[dict[str, object]] = []
    for line in addresses.read_text(encoding="utf-8").splitlines():
        address = line.strip()
        if not address or address.startswith("#"):
            continue
        try:
            run, _, _ = audit_layers(address)
        except Exception as exc:
            rows.append({"address": address, "error": f"{type(exc).__name__}: {exc}"})
            continue
        parcel = run.ctx.parcel
        reg = run.regulations[0] if run.regulations else None
        rules = {r.key: r for r in reg.rules} if reg else {}
        pot = run.potential
        row: dict[str, object] = {
            "address": address,
            "error": "",
            "parcel": parcel.local_id if parcel else "",
            "egrid": parcel.national_id if parcel else "",
            "parcel_area_m2": f"{parcel.area_m2:.0f}" if parcel and parcel.area_m2 else "",
            "zone": parcel.zoning_code if parcel else "",
            "zone_name": parcel.zoning_name if parcel else "",
            "max_full_floors": rules["max_full_floors"].value if "max_full_floors" in rules else "",
            "max_building_height_m": rules["max_building_height_m"].value
            if "max_building_height_m" in rules
            else "",
            "floor_area_ratio_pct": rules["floor_area_ratio"].value
            if "floor_area_ratio" in rules
            else "",
            "min_boundary_setback_m": rules["min_boundary_setback_m"].value
            if "min_boundary_setback_m" in rules
            else "",
            "unresolved": ", ".join(reg.unresolved) if reg else "",
            "buildings": "; ".join(
                f"{b.id}: {b.floors} fl × {b.footprint_m2} m²" for b in run.ctx.buildings
            ),
            "allowed_floor_area_m2": pot.allowed_floor_area_m2 if pot else "",
            "existing_floor_area_m2": pot.existing_floor_area_m2 if pot else "",
            "utilisation_pct": pot.utilisation_pct if pot else "",
            "potential_reason": pot.reason if pot else "",
            "findings": " | ".join(f"[{f.cls}] {f.title.en}" for f in run.findings),
            "sources": " | ".join(sorted({f.source.url for f in run.findings if f.source.url})),
            "reviewer_verdict": "",
            "reviewer_comment": "",
        }
        rows.append(row)
    fieldnames = list(rows[0].keys()) if rows else ["address"]
    for r in rows:
        for k in fieldnames:
            r.setdefault(k, "")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    console.print(f"wrote {out} ({len(rows)} rows)")


@app.command()
def audit(  # noqa: PLR0917
    address: str = typer.Argument(..., help="Address, 'Parcel <municipality> <no>' or 'lat,lon'"),
    lang: str | None = typer.Option(None, "--lang", help="fr|de|it|en (default: the canton's)"),
    goal: str | None = typer.Option(None, "--goal", help="Free text, e.g. 'build 12 apartments'"),
    depth: str = typer.Option("quick", "--depth", help="quick = layer 0 only; full = + layer 1"),
    as_json: bool = typer.Option(False, "--json", help="Print the AuditResult as JSON instead"),
    no_report: bool = typer.Option(False, "--no-report", help="Skip writing ./reports/<id>/"),
) -> None:
    """Run the whole deterministic pipeline and print layer 0 (and layer 1 with --depth full)."""
    from topoli.core.pipeline import build_result
    from topoli.core.reporting.assemble import assemble
    from topoli.core.reporting.layer0 import render_layer0
    from topoli.countries.ch.federal.geocode import ResolveError

    try:
        result, run = build_result(address, lang=lang, goal=goal)  # type: ignore[arg-type]
    except ResolveError as exc:
        console.print(f"[red]Could not resolve:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    if as_json:
        print(result.model_dump_json(by_alias=True, indent=1))
        return
    oereb = result.coverage_for("ch/federal/oereb")
    layer0 = render_layer0(
        result.site,
        result.findings,
        result.lang,
        goal=goal,
        regulations=result.regulations,
        oereb_available=bool(oereb and oereb.status == "ok"),
    )
    print(layer0.text)
    if not no_report:
        from topoli.core.reporting.card import render_cards
        from topoli.core.reporting.evidence_json import write_evidence
        from topoli.core.reporting.html import render_html
        from topoli.core.reporting.summary import summary_text, write_summary

        out_dir = write_evidence(result, run.records)
        card_layer0 = render_layer0(
            result.site,
            result.findings,
            result.lang,
            goal=goal,
            regulations=result.regulations,
            oereb_available=bool(oereb and oereb.status == "ok"),
            report_path="./index.html",
            card_path="./card.png",
        )
        write_summary(card_layer0, out_dir)
        html_path, _ = render_html(
            result,
            out_dir,
            lang=result.lang,
            goal=goal,
            fetch_tiles=True,
            summary_text=summary_text(card_layer0),
            card_png="card.png",
        )
        map_img = out_dir / "map.jpg"
        cards = render_cards(card_layer0, out_dir, map_image=map_img if map_img.is_file() else None)
        console.print(
            f"[dim]report: {html_path} · evidence: {out_dir / 'evidence.json'} · "
            f"{' · '.join(c.name for c in cards)} · summary.txt[/dim]"
        )
    if depth == "full":
        layer1 = assemble(result, result.lang, layer0.findings)
        for s in layer1.sections:
            console.rule(f"{s.number}. {s.title}")
            if not s.available:
                console.print(f"[dim]{s.stub}[/dim]")
                for c in s.coverage:
                    console.print(f"[dim]  {c.adapter_id}: {c.status} {c.detail or ''}[/dim]")
                continue
            for k, v in s.facts:
                console.print(f"  {k}: {v}")
            for line in s.text:
                console.print(f"  {line}")
            for f in s.findings:
                console.print(f"  [{f.cls}] {f.title.get(result.lang)}")
                console.print(f"      {f.consequence.get(result.lang)}")
                console.print(f"      [dim]{f.caveat.get(result.lang)}[/dim]")
            if s.number == 18:
                for row in layer1.sources:
                    console.print(
                        f"  {row.dataset} · {row.authority} · {row.retrieved_at} · {row.url[:80]}"
                    )
    console.print(_calls_line())


@app.command()
def render(
    evidence: Path = typer.Argument(..., help="Path to evidence.json or its report folder"),  # noqa: B008
    lang: str | None = typer.Option(None, "--lang", help="fr|de|it|en (default: as audited)"),
    tiles: bool = typer.Option(False, "--tiles", help="Fetch swisstopo tiles for the static map"),
) -> None:
    """Re-render index.html offline from an existing evidence.json."""
    from topoli.core.reporting.evidence_json import load_evidence
    from topoli.core.reporting.html import render_html

    result = load_evidence(evidence)
    out_dir = evidence if evidence.is_dir() else evidence.parent
    path, _ = render_html(result, out_dir, lang=lang, fetch_tiles=tiles)  # type: ignore[arg-type]
    console.print(f"wrote {path}")


@app.command()
def coverage(
    write: bool = typer.Option(False, "--write", help="Also write coverage.json at the repo root"),
) -> None:
    """Print the canton coverage table (federal / cantonal / events %) for README and website."""
    from topoli.core.scoring.coverage import build_coverage, write_coverage_json

    data = build_coverage()
    table = Table(title="coverage by canton")
    for col in ("canton", "lang", "federal", "cantonal", "events"):
        table.add_column(col)
    for canton, row in data["cantons"].items():
        table.add_row(
            canton,
            row["lang"],
            f"{row['federal_pct']}%",
            f"{row['cantonal_pct']}%",
            f"{row['events_pct']}%",
        )
    console.print(table)
    if data["degraded_adapters"]:
        console.print(f"[yellow]degraded:[/yellow] {', '.join(data['degraded_adapters'])}")
    if write:
        console.print(f"wrote {write_coverage_json()}")


fixtures_app = typer.Typer(help="Record and list test fixtures (recorded source responses).")
cache_app = typer.Typer(help="Inspect or clear the local cache.")
app.add_typer(fixtures_app, name="fixtures")
app.add_typer(cache_app, name="cache")


@fixtures_app.command("record")
def fixtures_record(
    adapter: str = typer.Option(..., "--adapter", help="Adapter id, e.g. ch/federal/parcel"),
    address: str = typer.Option(..., "--address", help="Address to record"),
    slug: str | None = typer.Option(None, "--slug", help="Folder name (default: from address)"),
) -> None:
    """Fetch live and store the adapter's raw responses under tests/fixtures/<adapter>/<slug>/."""
    from topoli.core.adapters.fixtures import record_fixture

    folder = record_fixture(adapter, address, slug=slug)
    files = [p.name for p in sorted(folder.glob("*.json")) if p.name != "meta.json"]
    console.print(f"[green]Recorded[/green] {len(files)} responses → {folder}")


@fixtures_app.command("list")
def fixtures_list() -> None:
    """List recorded fixtures."""
    from topoli.core.adapters.fixtures import list_fixtures

    table = Table(title="fixtures")
    for col in ("adapter", "slug", "address", "recorded", "requests"):
        table.add_column(col)
    for meta in list_fixtures():
        table.add_row(
            str(meta.get("adapter_id")),
            str(meta["folder"]).split("/")[-1],
            str(meta.get("address")),
            str(meta.get("recorded_at", ""))[:10],
            str(len(meta.get("requests", []))),
        )
    console.print(table)


@cache_app.command("stats")
def cache_stats() -> None:
    """Show cache size per adapter."""
    from topoli.core.adapters import cache

    st = cache.stats()
    table = Table(title=f"cache · {st.root} · {st.files} files · {st.megabytes} MB")
    table.add_column("adapter")
    table.add_column("files", justify="right")
    for adapter_id, n in st.adapters.items():
        table.add_row(adapter_id, str(n))
    console.print(table)


@cache_app.command("clear")
def cache_clear(
    adapter: str | None = typer.Option(None, "--adapter", help="Only this adapter id"),
) -> None:
    """Delete cached responses (all, or one adapter)."""
    from topoli.core.adapters import cache

    n = cache.clear(adapter_id=adapter)
    console.print(f"Removed {n} cached responses.")


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def check_python() -> Check:
    current = sys.version_info[:3]
    ok = current >= MIN_PYTHON
    return Check(
        "Python version",
        ok,
        f"{platform.python_version()} (need ≥ {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
    )


def check_network(url: str = GEOADMIN_PROBE_URL, timeout: float = 10.0) -> Check:
    try:
        response = httpx.get(
            url,
            params={"searchText": "Bern", "type": "locations", "limit": 1},
            timeout=timeout,
            headers={"User-Agent": f"topoli/{__version__} (+https://github.com/suchipizza/Topoli)"},
        )
    except httpx.HTTPError as exc:
        return Check("geo.admin.ch reachable", False, f"{type(exc).__name__}: {exc}")
    ok = response.status_code == 200
    return Check("geo.admin.ch reachable", ok, f"HTTP {response.status_code} from {url}")


def check_cache_dir() -> Check:
    path = cache_dir()
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path, prefix=".doctor-", delete=True):
            pass
    except OSError as exc:
        return Check("cache dir writable", False, f"{path}: {exc}")
    return Check("cache dir writable", True, str(path))


def run_doctor(*, skip_network: bool = False) -> list[Check]:
    checks = [check_python()]
    if not skip_network:
        checks.append(check_network())
    checks.append(check_cache_dir())
    return checks


@app.command()
def doctor(
    skip_network: bool = typer.Option(
        False, "--skip-network", help="Do not probe geo.admin.ch (offline environments, CI)."
    ),
) -> None:
    """Check that this machine can run a property audit."""
    checks = run_doctor(skip_network=skip_network)
    table = Table(title=f"topoli doctor · {__version__}", show_lines=False)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail", overflow="fold")
    for check in checks:
        status = "[green]OK[/green]" if check.ok else "[red]FAIL[/red]"
        table.add_row(check.name, status, check.detail)
    console.print(table)
    if all(c.ok for c in checks):
        console.print("[green]All checks passed.[/green]")
        return
    console.print("[red]Some checks failed.[/red] Open an issue with this output if you are stuck.")
    raise typer.Exit(code=1)


def _calls_line() -> str:
    from topoli.core.adapters import get_client

    c = get_client()
    return f"[dim]{c.calls} external calls · {c.cache_hits} from cache[/dim]"


def _print_json(model: Any) -> None:
    console.print_json(model.model_dump_json(by_alias=True, exclude_none=False))


@app.command()
def resolve(
    address: str = typer.Argument(
        ..., help="Postal address, 'Parcel <municipality> <no>' or 'lat,lon'"
    ),
) -> None:
    """Resolve an address to a Site (coordinates, municipality, canton, EGID, parcel id)."""
    from topoli.core.adapters import get_client
    from topoli.countries.ch.federal.geocode import ResolveError, resolve_address

    get_client().reset()
    try:
        site, _ = resolve_address(address)
    except ResolveError as exc:
        console.print(f"[red]Could not resolve:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    _print_json(site)
    console.print(_calls_line())


@app.command()
def parcel(
    address: str = typer.Argument(..., help="Address or 'Parcel <municipality> <no>'"),
    neighbours: bool = typer.Option(True, help="Also list adjacent parcels (one extra call)"),
) -> None:
    """Fetch the cadastral parcel (geometry, area, IDs, neighbours) for an address."""
    from topoli.core.adapters import get_client
    from topoli.countries.ch.federal.geocode import ResolveError, resolve_address
    from topoli.countries.ch.federal.parcel import ParcelNotFoundError, get_parcel

    get_client().reset()
    try:
        site, _ = resolve_address(address)
        parcel_obj, _ = get_parcel(site, with_neighbours=neighbours)
    except (ResolveError, ParcelNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    _print_json(parcel_obj)
    console.print(_calls_line())


@app.command()
def buildings(
    address: str = typer.Argument(..., help="Address or 'Parcel <municipality> <no>'"),
) -> None:
    """List the GWR buildings on the parcel at an address."""
    from topoli.core.adapters import get_client
    from topoli.countries.ch.federal.buildings import get_buildings
    from topoli.countries.ch.federal.geocode import ResolveError, resolve_address
    from topoli.countries.ch.federal.parcel import ParcelNotFoundError, get_parcel

    get_client().reset()
    try:
        site, _ = resolve_address(address)
        parcel_obj, _ = get_parcel(site, with_neighbours=False)
    except (ResolveError, ParcelNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    found, _ = get_buildings(parcel_obj)
    console.print_json(json.dumps([b.model_dump(mode="json") for b in found]))
    console.print(f"[dim]{len(found)} buildings · {_calls_line()}[/dim]")


if __name__ == "__main__":  # pragma: no cover
    os.environ.setdefault("TERM", "dumb")
    app()
