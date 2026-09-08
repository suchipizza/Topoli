from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from topoli.core.adapters import HttpClient, set_client
from topoli.core.adapters.fixtures import fixture_folders, seed_cache
from topoli.core.domain import Finding, LocalizedText, Source


@pytest.fixture(autouse=True)
def offline_client(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[HttpClient]:
    """Every test runs offline against a temporary cache unless marked ``live``."""
    if request.node.get_closest_marker("live"):
        client = HttpClient(use_cache=False, budget=1000)
    else:
        client = HttpClient(offline=True, cache_root=tmp_path / "cache")
    set_client(client)
    yield client
    set_client(None)


@pytest.fixture(scope="module")
def replay_module(tmp_path_factory: pytest.TempPathFactory) -> Callable[[str, str], int]:
    """Module-scoped variant of ``replay`` for expensive audits shared by several tests."""
    root = tmp_path_factory.mktemp("cache")
    client = HttpClient(offline=True, cache_root=root)
    set_client(client)

    def _seed(adapter_id: str, slug: str) -> int:
        set_client(client)
        folders = fixture_folders(adapter_id, slug)
        assert folders, f"no fixtures for {adapter_id}/{slug}; run `topoli fixtures record`"
        return seed_cache(root, *folders)

    return _seed


@pytest.fixture
def replay(offline_client: HttpClient) -> Callable[[str, str], int]:
    """``replay("ch/federal/buildings", "zurich-badenerstrasse-171")`` seeds the cache."""

    def _seed(adapter_id: str, slug: str) -> int:
        assert offline_client.cache_root is not None
        folders = fixture_folders(adapter_id, slug)
        assert folders, f"no fixtures for {adapter_id}/{slug}; run `topoli fixtures record`"
        return seed_cache(offline_client.cache_root, *folders)

    return _seed


@pytest.fixture
def complete_source() -> Source:
    return Source(
        adapter_id="ch/federal/hazards",
        authority="Bundesamt für Umwelt BAFU",
        dataset="ch.bafu.gefahren-hochwasser",
        licence="opendata-by",
        retrieved_at=datetime(2026, 9, 8, 9, 30, tzinfo=UTC),
        url="https://api3.geo.admin.ch/rest/services/all/MapServer/identify?layers=all:ch.bafu.gefahren-hochwasser",
    )


@pytest.fixture
def make_finding(complete_source: Source):  # type: ignore[no-untyped-def]
    def _make(**overrides: object) -> Finding:
        base: dict[str, object] = {
            "id": "hazard.flood",
            "title": LocalizedText.same("Flood risk: none identified."),
            "consequence": LocalizedText.same("No flood-related constraint on building."),
            "class": "A",
            "severity": "info",
            "category": "hazard",
            "source": complete_source,
            "caveat": LocalizedText.same(""),
        }
        base.update(overrides)
        return Finding.model_validate(base)

    return _make
