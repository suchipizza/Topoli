"""``topoli`` command-line interface.

Phase 1 commands are added work order by work order. This module ships
``--version`` and ``doctor`` (WO-00); later WOs add ``resolve``, ``parcel``,
``buildings``, ``layers``, ``audit``, ``render``, ``fixtures``, ``cache``, ``coverage``.
"""

from __future__ import annotations

import os
import platform
import sys
import tempfile
from dataclasses import dataclass

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


if __name__ == "__main__":  # pragma: no cover
    os.environ.setdefault("TERM", "dumb")
    app()
