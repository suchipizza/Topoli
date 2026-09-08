"""Cache, stale-but-served, budget and offline behaviour of the shared client (WO-04)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx

from topoli.core.adapters import BudgetExceededError, HttpClient, OfflineError, set_client
from topoli.core.adapters import cache as cache_mod
from topoli.core.adapters.base import Record
from topoli.core.scoring.coverage import coverage_entry, degraded_from_last_run, write_last_run

URL = "https://api3.geo.admin.ch/rest/services/height"


@pytest.fixture
def client(tmp_path: Path) -> HttpClient:
    c = HttpClient(cache_root=tmp_path / "cache", budget=5)
    set_client(c)
    return c


@respx.mock
def test_second_call_is_served_from_cache(client: HttpClient) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={"height": "412.1"}))
    first = client.get_json("t/height", URL, {"easting": 1, "northing": 2})
    second = client.get_json("t/height", URL, {"easting": 1, "northing": 2})
    assert route.call_count == 1
    assert client.calls == 1 and client.cache_hits == 1
    assert first.payload == second.payload == {"height": "412.1"}
    assert not first.from_cache and second.from_cache
    assert second.url == first.url
    assert cache_mod.cache_path("t/height", first.url, client.cache_root).is_file()


@respx.mock
def test_param_order_does_not_change_the_key(client: HttpClient) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={}))
    client.get_json("t", URL, {"a": 1, "b": 2})
    client.get_json("t", URL, {"b": 2, "a": 1})
    assert route.call_count == 2, "httpx keeps param order, so the URL differs — documented"


@respx.mock
def test_expired_entry_is_refetched(client: HttpClient) -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(200, json={"v": 1}))
    rec = client.get_json("t", URL, {"x": 1}, ttl=timedelta(days=30))
    old = rec.model_copy(update={"retrieved_at": datetime.now(tz=UTC) - timedelta(days=31)})
    cache_mod.write(old, client.cache_root)
    client.get_json("t", URL, {"x": 1}, ttl=timedelta(days=30))
    assert route.call_count == 2


@respx.mock
def test_stale_served_when_refetch_fails(client: HttpClient) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json={"v": 1}))
    rec = client.get_json("t", URL, {"x": 1})
    stale_time = datetime.now(tz=UTC) - timedelta(days=40)
    cache_mod.write(rec.model_copy(update={"retrieved_at": stale_time}), client.cache_root)
    respx.get(URL).mock(return_value=httpx.Response(503))
    served = client.get_json("t", URL, {"x": 1})
    assert served.from_cache and served.stale_as_of is not None
    assert abs((served.stale_as_of - stale_time).total_seconds()) < 1
    entry = coverage_entry("t", [served])
    assert entry.status == "degraded"
    assert entry.detail and "as of" in entry.detail
    assert entry.calls == 0 and entry.from_cache


@respx.mock
def test_failure_without_cache_raises_and_error_becomes_degraded(client: HttpClient) -> None:
    respx.get(URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        client.get_json("t", URL, {"x": 1})
    entry = coverage_entry("t", [], error="HTTP 500")
    assert entry.status == "degraded" and entry.detail == "HTTP 500"


@respx.mock
def test_budget_exceeded(client: HttpClient) -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json={}))
    for i in range(5):
        client.get_json("t", URL, {"i": i})
    with pytest.raises(BudgetExceededError):
        client.get_json("t", URL, {"i": 99})


def test_offline_client_raises_without_cache(tmp_path: Path) -> None:
    c = HttpClient(offline=True, cache_root=tmp_path)
    with pytest.raises(OfflineError):
        c.get_json("t", URL, {"x": 1})


def test_offline_client_serves_stale_cache(tmp_path: Path) -> None:
    c = HttpClient(offline=True, cache_root=tmp_path)
    old = Record(
        adapter_id="t",
        url=cache_mod.canonical_url(URL, {"x": 1}),
        retrieved_at=datetime.now(tz=UTC) - timedelta(days=90),
        payload={"v": "old"},
    )
    cache_mod.write(old, tmp_path)
    served = c.get_json("t", URL, {"x": 1}, ttl=timedelta(days=30))
    assert served.payload == {"v": "old"} and served.stale_as_of is not None


def test_no_cache_flag_skips_read_and_write(tmp_path: Path) -> None:
    with respx.mock:
        route = respx.get(URL).mock(return_value=httpx.Response(200, json={}))
        c = HttpClient(use_cache=False, cache_root=tmp_path)
        c.get_json("t", URL, {"x": 1})
        c.get_json("t", URL, {"x": 1})
    assert route.call_count == 2
    assert cache_mod.stats(tmp_path).files == 0


def test_stats_and_clear(tmp_path: Path) -> None:
    for i in range(3):
        cache_mod.write(
            Record(
                adapter_id="a/b", url=f"{URL}?i={i}", retrieved_at=datetime.now(tz=UTC), payload={}
            ),
            tmp_path,
        )
    cache_mod.write(
        Record(adapter_id="c", url=URL, retrieved_at=datetime.now(tz=UTC), payload={}), tmp_path
    )
    st = cache_mod.stats(tmp_path)
    assert st.files == 4 and st.adapters == {"a/b": 3, "c": 1}
    assert cache_mod.clear(tmp_path, adapter_id="a/b") == 3
    assert cache_mod.stats(tmp_path).files == 1
    assert cache_mod.clear(tmp_path) == 1


def test_coverage_entry_statuses() -> None:
    rec = Record(adapter_id="a", url=URL, retrieved_at=datetime.now(tz=UTC), payload={})
    assert coverage_entry("a", [rec]).status == "ok"
    assert coverage_entry("a", [rec]).calls == 1
    assert coverage_entry("a", [], not_available="no ÖREB for VS").status == "not_available"
    assert coverage_entry("a", [], not_contributed="Winterthur BZO").status == "not_contributed"


def test_last_run_round_trip(tmp_path: Path) -> None:
    path = write_last_run(
        {
            "ch/federal/parcel": {"ok": True, "failed": []},
            "ch/federal/noise": {"ok": False, "failed": ["x"]},
        },
        tmp_path / "last_run.json",
    )
    assert degraded_from_last_run(path) == ["ch/federal/noise"]
    assert degraded_from_last_run(tmp_path / "missing.json") == []
