"""No telemetry: every recorded request targets an official source in allowed_hosts.txt (WO-11)."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest
import respx

from topoli.core.adapters import EgressError, HttpClient, allowed_hosts

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_every_recorded_request_hits_an_allowed_host() -> None:
    hosts = allowed_hosts()
    assert "api3.geo.admin.ch" in hosts
    bad = set()
    for meta in FIXTURES.rglob("meta.json"):
        for entry in json.loads(meta.read_text(encoding="utf-8")).get("requests", []):
            host = urlsplit(entry["url"]).hostname or ""
            if host.lower() not in hosts:
                bad.add(host)
    assert not bad, f"hosts outside the allowlist: {sorted(bad)}"


@respx.mock
def test_client_refuses_unknown_hosts(tmp_path: Path) -> None:
    respx.get("https://telemetry.example.com/x").mock(return_value=httpx.Response(200, json={}))
    client = HttpClient(cache_root=tmp_path)
    with pytest.raises(EgressError):
        client.get_json("t", "https://telemetry.example.com/x")
    assert client.calls == 0
