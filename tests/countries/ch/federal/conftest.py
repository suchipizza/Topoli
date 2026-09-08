from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from pathlib import Path

import pytest
import vcr

from topoli.core.adapters import get_client

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "ch" / "federal"


@pytest.fixture
def cassette(record_mode: str) -> Callable[[str], AbstractContextManager[object]]:
    """``with cassette("slug"):`` replays ``tests/fixtures/ch/federal/<slug>.yaml``.

    Offline by default (``record_mode`` = ``none`` from pytest-recording); re-record with
    ``--record-mode=once`` (missing cassettes) or ``--record-mode=all`` (everything).
    """
    recorder = vcr.VCR(
        cassette_library_dir=str(FIXTURES),
        record_mode=record_mode,
        filter_headers=["user-agent"],
        match_on=["method", "scheme", "host", "path", "query"],
        decode_compressed_response=True,
    )

    def _use(slug: str) -> AbstractContextManager[object]:
        manager: AbstractContextManager[object] = recorder.use_cassette(f"{slug}.yaml")
        return manager

    return _use


@pytest.fixture(autouse=True)
def _reset_budget() -> Iterator[None]:
    get_client().reset()
    yield
