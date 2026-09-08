"""Canton of Zürich adapters (Phase 1 deep canton). Importing registers them."""

from __future__ import annotations

from topoli.core.adapters.registry import register
from topoli.countries.ch.zh.construction_events import ConstructionEventsAdapter
from topoli.countries.ch.zh.heritage import ZhHeritageAdapter
from topoli.countries.ch.zh.regulation.adapter import RegulationAdapter
from topoli.countries.ch.zh.zoning import ZoningAdapter

register(ZoningAdapter(), tier="cantonal")
register(RegulationAdapter(), tier="cantonal")
register(ZhHeritageAdapter(), tier="cantonal")
register(ConstructionEventsAdapter(), tier="events")
