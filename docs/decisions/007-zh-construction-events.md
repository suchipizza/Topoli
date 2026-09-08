# 007 — Zürich construction events: go, via the cantonal Baugesuche register + parcel matching

**Status:** decided (go) · 2026-09-08 · WO-06

## Sources investigated

| Source | Format | Licence | Fields | Cadence | Verdict |
|---|---|---|---|---|---|
| City of Zürich open-data portal | — | CC0 | no building-application dataset exists (only zoning, 3D buildings) | — | no |
| **Amtsblattportal API** (`https://www.amtsblattportal.ch/api/v1`, the platform behind amtsblatt.zh.ch) | JSON list, XML/JSON detail per publication | "freely accessible for anyone"; only the signed PDF is legally binding | rubric `BP-ZH` / `BP-ZH01` "Bauprojekt": title, dates, registration office (municipality id), detail XML with project location, cadastre numbers, contractor, project author, description | continuous; 6,743 ZH publications online | yes for detail links; listing needs one call per publication for details |
| **Baugesuche im Kanton Zürich** (Statistisches Amt / FK OGD, opendata.swiss, `daten.statistik.zh.ch/…/KTZH_00002982_00006183.csv`) | CSV, 22,600 rows since 2022-06, 9 MB | opendata.swiss "Freie Nutzung" (OPEN) | one row per publication × address/parcel: id, publication number/date, objection deadline, `bfs_nr`, municipality, project description, address, cadastre numbers, anonymised contractor / project-author metadata (legal form, town) | daily | **yes** — the machine-readable aggregation of the Amtsblatt publications |
| Geneva SITG "Autorisation de construire – Dossier" (fallback per WO-06) | ESRI REST / WFS, daily | SITG open data | dossier type, status, applicant, mandatary | daily | not needed (kept as the Phase 2 reference) |

## Design

Publications carry **no coordinates**, and geocoding each one would blow the 25-call budget. Instead:

1. One download of the cantonal CSV per day (cache TTL 24 h), reduced at fetch time to the 20 columns used and the last 400 days, gzipped (≈ 1 MB instead of 9 MB).
2. One WFS call for the cantonal parcel-number points (`ms:ogd-0404_arv_basis_avzh_liegenschaften_pos_p`) inside the search radius (≈ 1,300 points per km² in the city, ≈ 40 KB reduced).
3. Publications of the site's municipality whose cadastre numbers (`'3147, 3148 und 4620'` or `'AU6979'`) resolve to a point inside the radius become `ConstructionEvent`s with the parcel point as location, distance, a keyword-classified type (new_building / extension / conversion / demolition / energy / signage / antenna / other), publication date, status (objection period open or published), and anonymised applicant / author. Publications whose numbers do not resolve are counted in the derivation, never guessed.

Two calls per audit → 24 of 25. Works for every Zürich municipality, not only the city.

## Limits (stated in caveats)

- Register starts June 2022; "since 12 months" is measured from the CSV retrieval date so replayed fixtures stay deterministic.
- Persons are anonymised at the source ("Privatperson"); companies show legal form and town only. No value estimates (PRD §4.2).
- The municipality filter uses the site's BFS number; publications of neighbouring municipalities inside the radius are not included in Phase 1.
