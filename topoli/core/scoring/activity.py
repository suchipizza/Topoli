"""Nearby construction activity (PRD §3.4 section 14): count, distance, recency, timeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from topoli.core.domain import ConstructionEvent


@dataclass(frozen=True)
class ActivitySummary:
    count: int
    within_m: float
    since: date | None
    nearest_m: float | None
    most_recent: date | None
    by_type: dict[str, int]


def summarize(
    events: list[ConstructionEvent], *, radius_m: float, since: date | None
) -> ActivitySummary:
    events = timeline(events)
    by_type: dict[str, int] = {}
    for e in events:
        by_type[e.type] = by_type.get(e.type, 0) + 1
    distances = [e.distance_m for e in events if e.distance_m is not None]
    return ActivitySummary(
        count=len(events),
        within_m=radius_m,
        since=since,
        nearest_m=min(distances) if distances else None,
        most_recent=max((e.publication_date for e in events), default=None),
        by_type=dict(sorted(by_type.items())),
    )


def timeline(events: list[ConstructionEvent]) -> list[ConstructionEvent]:
    """Deduplicated by publication id, newest first (layer-1 section 14)."""
    seen: dict[str, ConstructionEvent] = {}
    for e in events:
        if e.id not in seen:
            seen[e.id] = e
    return sorted(seen.values(), key=lambda e: (e.publication_date, e.id), reverse=True)
