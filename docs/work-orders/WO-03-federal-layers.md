# WO-03 — Federal constraint layers

**Read first:** PRD (repo) §4.1, §3.4 sections 7–13.
**Depends on:** WO-02 (and WO-04 for the fixture recorder; can start in parallel with WO-04 using pytest-recording directly).

## Objective
Seven adapters that turn a parcel geometry into class A/B findings: hazards, noise, contamination, ÖREB, solar, heritage, terrain. Coverage is explicit — an unavailable layer for a canton yields a `not_available` coverage entry and a class-D "unknown" finding, never silence.

## Tasks (one adapter each, same pattern)
For each: identify the official federal layer(s) on geo.admin.ch (or the ÖREB extract API for ÖREB), read the layer docs, record licensing, implement `fetch` (identify/intersect with the parcel geometry), `to_findings` (localized templates with slots via `t()`), fixtures for 3 sites incl. one negative case, source-contract test.

1. `hazards.py` — flood, landslide, avalanche, rockfall hazard maps; per hazard: level (none/low/medium/high/residual) and intersection area/fraction (class B). Finding severity maps from level.
2. `noise.py` — road and rail noise exposure (day/night bands) and, where available, the noise sensitivity level assigned to the zone; exposure is class A/B, "affects apartment layout" consequence is a fixed consequence string, not reasoning.
3. `contamination.py` — cadastre of polluted sites (KbS) intersections; status classes as published.
4. `oereb.py` — ÖREB/RDPPF extract for the parcel (XML/JSON): list restriction themes touching the parcel with responsible authority and legal provisions; per-canton availability recorded in `coverage`. Do not parse legal text into rules here — that is WO-05's job for Zürich only.
5. `solar.py` — Sonnendach suitability class per building footprint; finding is per building, aggregated to the best roof on layer 0.
6. `heritage.py` — ISOS and federal inventories (listed objects/areas) — status only, class A.
7. `terrain.py` — elevation at parcel centroid and corners via the height service; slope estimate (class B) with the method stated in `derivation`.
8. `core/scoring/coverage.py` — computes the per-adapter coverage status and the canton coverage percentages consumed later by the README/website bars; writes `coverage.json` (per canton: federal %, cantonal %, events %).

## Done when
`uv run topoli layers "<Zürich address>"` prints ≥ 7 findings with sources; each adapter has 3 fixtures and a live contract test; `coverage.json` generates; `LICENCES.md` covers every layer. A Valais address yields correct `not_available` entries where cantonal ÖREB is missing rather than an exception.
