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

BAFU_HAZARDS = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office for the Environment FOEN (BAFU) — Aquaprotect, surface-runoff hazard map, SilvaProtect-CH",
    redistribution_allowed=False,
)

BAFU_NOISE = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office for the Environment FOEN (BAFU) — road and rail noise (sonBASE)",
    redistribution_allowed=False,
)

FEDERAL_KBS = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: BAV / BAZL / VBS — federal cadastres of polluted sites (KbS)",
    redistribution_allowed=False,
)

SWISSTOPO_OEREB_STATUS = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office of Topography swisstopo — availability of the ÖREB cadastre",
    redistribution_allowed=False,
)

OEREB_CANTONAL = Licence(
    id="oereb-cantonal",
    name="Cantonal ÖREB-Kataster web service (federal directive V2.0)",
    url="https://www.cadastre.ch/de/oereb-webservice",
    attribution="Source: cantonal ÖREB-Kataster (Kataster der öffentlich-rechtlichen Eigentumsbeschränkungen), extract as published by the canton",
    redistribution_allowed=False,
)

BFE_SOLAR = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Swiss Federal Office of Energy SFOE (BFE) — Sonnendach.ch roof suitability",
    redistribution_allowed=False,
)

FEDERAL_HERITAGE = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office for Civil Protection FOCP (BABS) — KGS inventory; Federal Office of Culture (BAK) — UNESCO World Heritage",
    redistribution_allowed=False,
)

SWISSTOPO_ALTI = Licence(
    id="geoadmin-terms",
    name="geo.admin.ch general terms of use (FSDI)",
    url=TERMS_URL,
    attribution="Source: Federal Office of Topography swisstopo — swissALTI3D (profile service)",
    redistribution_allowed=False,
)
