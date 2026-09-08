"""Federal (all-of-Switzerland) adapters built on the geo.admin.ch REST/WMS services.

Importing this package registers the federal adapters in ``topoli.core.adapters.registry``:
the *spine* (geocode, parcel, buildings) and the seven constraint *layers*.
"""

from __future__ import annotations

from topoli.core.adapters.registry import register
from topoli.countries.ch.federal.buildings import BuildingsAdapter
from topoli.countries.ch.federal.contamination import ContaminationAdapter
from topoli.countries.ch.federal.geocode import GeocodeAdapter
from topoli.countries.ch.federal.hazards import HazardsAdapter
from topoli.countries.ch.federal.heritage import HeritageAdapter
from topoli.countries.ch.federal.noise import NoiseAdapter
from topoli.countries.ch.federal.oereb import OerebAdapter
from topoli.countries.ch.federal.parcel import ParcelAdapter
from topoli.countries.ch.federal.solar import SolarAdapter
from topoli.countries.ch.federal.terrain import TerrainAdapter

register(GeocodeAdapter(), tier="spine", needs_parcel=False)
register(ParcelAdapter(), tier="spine", needs_parcel=False)
register(BuildingsAdapter(), tier="spine", needs_parcel=True)
register(HazardsAdapter(), tier="federal")
register(NoiseAdapter(), tier="federal")
register(ContaminationAdapter(), tier="federal")
register(OerebAdapter(), tier="federal")
register(SolarAdapter(), tier="federal")
register(HeritageAdapter(), tier="federal")
register(TerrainAdapter(), tier="federal")
