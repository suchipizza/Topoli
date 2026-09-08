from __future__ import annotations

from datetime import UTC, datetime

import pytest

from topoli.core.domain import Finding, LocalizedText, Source


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
