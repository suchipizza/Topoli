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
) -> None:
    """Topoli command-line interface."""


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
    console.print(f"[dim]{get_client().calls} external calls[/dim]")


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
    console.print(f"[dim]{get_client().calls} external calls[/dim]")


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
    console.print(f"[dim]{len(found)} buildings · {get_client().calls} external calls[/dim]")


if __name__ == "__main__":  # pragma: no cover
    os.environ.setdefault("TERM", "dumb")
    app()
