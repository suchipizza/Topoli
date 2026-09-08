"""Live contract tests: mark each test with ``@pytest.mark.adapter("<adapter_id>")``.

At session end the per-adapter outcome is written to ``tests/source-contracts/last_run.json``;
``nightly.yml`` uploads it and opens one ``source-degraded: <adapter_id>`` issue per failure.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

from topoli.core.adapters import HttpClient, set_client
from topoli.core.scoring.coverage import write_last_run

_RESULTS: dict[str, dict[str, Any]] = defaultdict(lambda: {"ok": True, "failed": [], "passed": 0})


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "adapter(id): adapter this live contract test covers")


@pytest.fixture(autouse=True)
def _online_client() -> None:
    # Contract tests hit the network on purpose and must never read the cache.
    set_client(HttpClient(use_cache=False, budget=1000))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):  # type: ignore[no-untyped-def]
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    for marker in item.iter_markers("adapter"):
        entry = _RESULTS[str(marker.args[0])]
        if report.failed:
            entry["ok"] = False
            entry["failed"].append(item.nodeid)
        elif report.passed:
            entry["passed"] += 1


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _RESULTS:
        write_last_run({k: dict(v) for k, v in _RESULTS.items()})
