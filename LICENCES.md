# Data source licences

Code in this repository is Apache-2.0 (see `LICENSE`). Data is **never redistributed**: every adapter fetches from the official source on demand and caches locally on the user's machine.

No adapter ships without a row here (`CLAUDE.md`, non-negotiable 6). Attribution text is reproduced in the report's sources panel exactly as written in this table.

| Source (authority) | Dataset | Licence | Attribution text | Redistribution allowed | Adapter id |
|---|---|---|---|---|---|
| Federal Office of Topography swisstopo (geo.admin.ch / FSDI) | `SearchServer` locations (addresses, parcels, municipalities) | [geo.admin.ch general terms of use](https://www.geo.admin.ch/en/general-terms-of-use-fsdi) — free, no registration, fair use, source must be credited | Source: Federal Office of Topography swisstopo, geo.admin.ch search service | n — fetched on demand, never redistributed | `ch/federal/geocode` |
| swisstopo / cantons — cadastral surveying (OpenData-AV) | `ch.swisstopo-vd.amtliche-vermessung` (fallback `ch.kantone.cadastralwebmap-farbe`) | geo.admin.ch general terms of use (as above) | Source: Federal Office of Topography swisstopo, cadastral surveying (OpenData-AV) | n — fetched on demand | `ch/federal/parcel` |
| Federal Statistical Office (FSO/BFS) — Federal Register of Buildings and Dwellings (GWR/RegBL) | `ch.bfs.gebaeude_wohnungs_register` via geo.admin.ch identify | geo.admin.ch general terms of use (as above); codes per [Merkmalskatalog 4.2](https://www.housing-stat.ch/files/881-2200.pdf) | Source: Federal Statistical Office (FSO), Federal Register of Buildings and Dwellings (GWR/RegBL) | n — fetched on demand | `ch/federal/buildings`, `ch/federal/geocode` |
