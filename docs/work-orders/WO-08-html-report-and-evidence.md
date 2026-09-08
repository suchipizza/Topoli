# WO-08 — Local HTML report and evidence.json

**Read first:** PRD (repo) §3.5, §6; PRD (website) §9 (shared visual motif).
**Depends on:** WO-07.

## Objective
`./reports/<municipality>-<parcel>/index.html` — self-contained, four-language, mobile-friendly, printable, Lighthouse ≥ 90 — plus `evidence.json` and `raw/`.

## Tasks
1. `core/reporting/evidence_json.py` — write `evidence.json` (all findings incl. unshown, coverage, timings, parser versions) and `raw/<adapter_id>.json`, GeoJSON for parcel, buildings, intersections.
2. `ui/local-report/template.html` (Jinja) + inlined CSS/JS, no external JS deps. Embed all four `i18n` dictionaries and the localized finding texts so the language switcher works client-side without regeneration.
3. Sections per PRD §6: header (address, date, language switcher, star + share buttons), five finding cards (severity colour, class badge, expand to layer-1 detail with "why" reading `evidence.json` data embedded inline), map (Leaflet-free: an inline SVG rendered from GeoJSON in LV95 with swisstopo WMTS tiles fetched at view time and a static fallback PNG generated at build), 18 collapsible sections, nearby timeline component, coverage notice, sources table, trust footer (four classes, "does not replace…", licences), waitlist block posting to `TOPOLI_WAITLIST_URL` (config constant) with no-JS fallback link carrying `?src=report&lang=`.
4. Design: one accent colour (define in `ui/local-report/tokens.css`, reused by the website), system font stack, dark mode via `prefers-color-scheme`, A4 print stylesheet that prints layer 0 + sections in full, page numbers.
5. `topoli render <evidence.json> --lang xx` re-renders offline. `topoli audit` calls it automatically.
6. Accessibility: semantic headings, focus states, `aria-expanded` on sections, alt text on the map fallback.
7. Test: Lighthouse via `playwright` + `lighthouse` in CI for the golden example (perf ≥ 90, a11y ≥ 90); golden byte-compare of 3 example reports modulo timestamps.

## Done when
Opening the generated `index.html` from disk (no server) shows the five findings, switches language, expands to sources, prints to A4 cleanly; Lighthouse thresholds pass in CI.
