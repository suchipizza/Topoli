"""Fixture recorder: ``topoli fixtures record --adapter <id> --address "<addr>"``.

Runs the adapter (and the spine it depends on) against the live sources with the cache
bypassed, then stores every record the adapter made under
``tests/fixtures/<adapter_id>/<slug>/<sha>.json`` plus a ``meta.json`` (address, date, endpoints,
Topoli version). Tests seed a temporary cache directory from those files
(:func:`seed_cache`) and run fully offline.
"""

from __future__ import annotations

import contextlib
import json
import re
import shutil
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topoli import __version__
from topoli.core.adapters import cache
from topoli.core.adapters.base import Record
from topoli.core.adapters.http import HttpClient, get_client, set_client
from topoli.core.adapters.registry import all_specs
from topoli.core.adapters.registry import get as get_spec
from topoli.core.domain import Building
from topoli.paths import repo_root


def fixtures_root() -> Path:
    return repo_root() / "tests" / "fixtures"


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "site"


def record_fixture(adapter_id: str, address: str, *, slug: str | None = None) -> Path:
    """Fetch live and write the fixture folder. Returns the folder path."""
    from topoli.core.adapters.base import SiteContext
    from topoli.countries.ch.federal.buildings import get_buildings
    from topoli.countries.ch.federal.geocode import resolve_address
    from topoli.countries.ch.federal.parcel import get_parcel

    spec = get_spec(adapter_id)
    slug = slug or slugify(address)
    folder = fixtures_root() / adapter_id / slug

    previous = get_client()
    client = HttpClient(use_cache=False, budget=100)
    client.recorded = []
    set_client(client)
    try:
        site, _ = resolve_address(address)
        parcel = None
        buildings: list[Building] = []
        if adapter_id != "ch/federal/geocode":
            parcel, _ = get_parcel(site)
        if spec.needs_parcel and adapter_id != "ch/federal/buildings":
            buildings, _ = get_buildings(parcel) if parcel else ([], [])
        ctx = SiteContext(site=site, parcel=parcel, buildings=buildings)
        if spec.tier == "cantonal":
            # Enriching adapters of the same canton (zoning sets the zone code) run first.
            for other in all_specs("cantonal"):
                enrich = getattr(other.adapter, "enrich", None)
                if other.id != adapter_id and callable(enrich):
                    with contextlib.suppress(Exception):
                        ctx = enrich(other.adapter.fetch(ctx), ctx)
        if adapter_id not in ("ch/federal/geocode", "ch/federal/parcel"):
            with contextlib.suppress(LookupError):  # not-available is a fixture too
                spec.adapter.fetch(ctx)
        records = [r for r in client.recorded if r.adapter_id == adapter_id]
    finally:
        set_client(previous)

    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    files = []
    for rec in records:
        path = cache.write(rec, root=fixtures_root() / "_tmp")
        target = folder / path.name
        shutil.move(str(path), target)
        files.append({"file": target.name, "url": rec.url})
    shutil.rmtree(fixtures_root() / "_tmp", ignore_errors=True)
    meta: dict[str, Any] = {
        "adapter_id": adapter_id,
        "address": address,
        "site_id": site.id,
        "recorded_at": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "topoli_version": __version__,
        "requests": files,
    }
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    return folder


def list_fixtures() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = fixtures_root()
    if not root.is_dir():
        return out
    for meta_path in sorted(root.rglob("meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        meta["folder"] = str(meta_path.parent.relative_to(root))
        out.append(meta)
    return out


def seed_cache(cache_root: Path, *folders: Path) -> int:
    """Copy fixture folders into a cache root (``<cache_root>/<adapter_id>/<sha>.json``)."""
    copied = 0
    for folder in folders:
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        target = cache_root / meta["adapter_id"]
        target.mkdir(parents=True, exist_ok=True)
        for entry in meta["requests"]:
            shutil.copy(folder / entry["file"], target / entry["file"])
            copied += 1
    return copied


def fixture_folders(adapter_id: str, slug: str) -> list[Path]:
    """All fixture folders needed to replay ``adapter_id`` for ``slug`` (includes the spine)."""
    needed = ["ch/federal/geocode", "ch/federal/parcel", "ch/federal/buildings", adapter_id]
    seen: list[Path] = []
    for aid in needed:
        for name in (slug, "_shared"):  # ``_shared``: site-independent records (e.g. the BZO text)
            folder = fixtures_root() / aid / name
            if folder.is_dir() and folder not in seen:
                seen.append(folder)
    return seen


def touch_retrieved_at(
    folder: Path, when: datetime
) -> None:  # pragma: no cover - maintenance helper
    """Rewrite ``retrieved_at`` in a fixture folder (e.g. to simulate staleness)."""
    for path in folder.glob("*.json"):
        if path.name == "meta.json":
            continue
        rec = Record.model_validate_json(path.read_text(encoding="utf-8"))
        path.write_text(rec.model_copy(update={"retrieved_at": when}).model_dump_json(indent=1))
