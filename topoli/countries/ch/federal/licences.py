"""Licence objects for federal sources; every one has a row in ``LICENCES.md``."""

from __future__ import annotations

from topoli.core.domain import Licence
from topoli.countries.ch.federal.geoadmin import TERMS_URL

SWISSTOPO_AV = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office of Topography swisstopo, cadastral surveying (OpenData-AV)",
    redistribution_allowed=False,  # fetched on demand; never redistributed by Topoli
)

SWISSTOPO_SEARCH = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office of Topography swisstopo, geo.admin.ch search service",
    redistribution_allowed=False,
)

BFS_GWR = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution=(
        "Source: Federal Statistical Office (FSO), "
        "Federal Register of Buildings and Dwellings (GWR/RegBL)"
    ),
    redistribution_allowed=False,
)
