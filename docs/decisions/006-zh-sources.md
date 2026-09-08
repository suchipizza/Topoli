# 006 — Zürich sources: cantonal WFS for zoning and heritage, ÖREB document server for the BZO

**Status:** decided · 2026-09-08 · WO-05

| Need | Chosen source | Why |
|---|---|---|
| Zone code + name for any parcel in the canton | Canton ZH OGD WFS `ms:ogd-0156_arv_basis_np_gn_zonenflaeche_f` (simplified ÖREB data model, communal zoning of every municipality, with `vollgeschosse_max`, `gebaeudehoehe_max`, `wohnanteil_min`, decision/approval references) | One source covers the City of Zürich **and** the other 159 municipalities (PRD §4.2: zone code for all ZH, rules only for the City). Terms: OGD, free use, no access constraints |
| BZO 2016 consolidated text | `https://oerebdocs.zh.ch/getDoc?docid=6` — the document the zoning layer itself references in its `dokument` attribute | Consolidated (changes to 29 May 2024), text layer extractable with pypdf; official publication (Art. 5 URG: not copyright-protected). The city's own AS PDF URLs return HTML/404 |
| Protected heritage objects | Canton ZH OGD WFS `ms:ogd-0368_giszhpub_arv_kaz_denkmalschutzobjekte_p` (cantonal **and** communal objects, `einstufung`, `schutz`, `katasternummer`, `egid`) | The City of Zürich "Denkmalpflege-Inventar" WFS (`ogd.stadt-zuerich.ch/wfs/geoportal/…`, CC0) answered HTTP 500 to every request on 2026-09-08, as did its zoning WFS. Revisit; the cantonal dataset is the protection register (objects with a decision), the city inventory also lists inventoried-but-not-yet-protected objects |

Matching heritage objects to the parcel: by parcel number (`katasternummer`) or by a building's EGID; points inside the bbox but on other parcels are ignored.

Call budget: zoning 1 + BZO 1 (cached 30 days, shared across audits) + heritage 1 = 3 → 22 of 25 per audit.

## Parser scope and drift protection

`parser.py` extracts only table articles (13, 14, 18, 19, 24g, 24l, 24o). `generated/zones.yaml` is committed; `tests/countries/ch/zh/test_regulation.py` re-parses the recorded text and diff-checks it, and the nightly health check re-parses the live PDF and fails when W4's AZ is no longer found (layout drift).
