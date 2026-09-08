# 009 — The local HTML report: self-contained, server-rendered, JS only for switching

**Status:** decided · 2026-09-08 · WO-08

- **One file, no dependencies.** `index.html` inlines `tokens.css`, `report.css`, `report.js`, the four i18n dictionaries (the subset the page uses) and every finding in all four languages. No external script or stylesheet; the only requests a viewer's browser may make are swisstopo map tiles (at view time, WMTS `2056_27`, © swisstopo) and the waitlist POST when the visitor submits it. Both degrade: offline, the static `map.jpg` composed at build time stays visible; without JavaScript, the waitlist link opens the website form.
- **Server-rendered first paint.** Every visible string is rendered in the audited language by Jinja; `report.js` only swaps texts when the visitor changes language (values in `data-i18n` / `data-l10n` attributes). This removed the layout shift that JS-filled text caused (Lighthouse CLS 0.35 → 0) and keeps the page readable with scripts disabled.
- **Map.** Inline SVG (parcel outline, building points, nearby publications) over a tile grid computed in Python (`static_map.frame_for`), rendered client-side from the same frame; the static fallback is a JPEG (quality 82, ≈ 140 KB instead of a 700 KB PNG).
- **Layer 2 on disk.** `evidence.json` (= `AuditResult`), `raw/<adapter>.json`, `geometry.geojson` (WGS84 with LV95 copies). `topoli render <folder> --lang xx` re-renders offline.
- **Quality gates.** Lighthouse mobile on the golden example in CI (`report-quality` job): performance ≥ 0.90, accessibility ≥ 0.90, best practices ≥ 0.90 (measured 2026-09-08: 96 / 100 / 100). Golden byte-compare of three reports modulo dates/versions (`tests/golden/`).
- **Print.** A4 `@page`, sections expanded, links printed with their URL, page numbers in the footer.
