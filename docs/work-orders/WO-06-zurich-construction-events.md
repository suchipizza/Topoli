# WO-06 — Zürich construction events (nearby activity)

**Read first:** PRD (repo) §4.2, §3.4 section 14, open question 3; spec Phase 2 (`construction_event`).
**Depends on:** WO-04.

## Objective
Section 14 and the layer-0 "n permits within 500 m in the last 12 months" finding for the City of Zürich, using official construction publications. If the source is not machine-readable enough, produce the decision note and a minimal viable version rather than a scraper that will break.

## Tasks
1. Investigate the official City of Zürich / Canton ZH construction publication sources (Bauausschreibungen / Baugesuche in the Amtsblatt or open-data portal). Write `docs/decisions/00x-zh-construction-events.md` with: source URL, format, licence, fields available, update cadence, and a go/no-go for P1. If no-go, implement steps 2–3 against Geneva's construction authorization API instead as the reference implementation and mark ZH events `not_contributed`.
2. `countries/ch/zh/construction_events.py` — fetch publications within a bounding box/radius (500 m default, `--since 12m`), normalize to `ConstructionEvent` (type, description, applicant, project author, publication date, status, parcels/coordinates, source URL). No value estimates in P1.
3. `core/scoring/activity.py` — count, distance, recency; layer-0 template fires only with ≥ 1 event; layer-1 timeline data (sorted, deduplicated by publication id).
4. Fixtures for 3 sites (dense, quiet, edge-of-city); TTL 24 h in cache.

## Done when
`topoli events "<Zürich address>" --radius 500` prints normalized events with source URLs, or the decision note explains why the finding is stubbed for P1 and the Geneva reference adapter passes its fixtures.
