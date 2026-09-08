# 010 — Share card: pure-Python renderer (Pillow + bundled OFL font), no browser

**Status:** decided · 2026-09-08 · WO-09

PRD §7 requires `card.png` (1200×630 and 1080×1080) on every run without adding an install step. Options:

1. **Pillow + a bundled font** — no extra dependency beyond `pillow` (already needed for the hazard masks). Chosen.
2. Playwright/Chromium screenshot of the report — pixel-perfect and emoji-capable, but a 150 MB browser download the user must trigger; would need an HTML-only degrade path. Rejected for Phase 1.
3. `cairosvg`/`resvg` SVG rasterisation — native library wheels are fragile across platforms. Rejected.

Consequences:
- The font is **Inter** (static Regular + Bold, SIL Open Font License 1.1, `ui/local-report/card/fonts/OFL.txt`), which covers all Latin diacritics used in FR/DE/IT.
- No colour emoji on the card: findings carry a class badge (A/B/C/D) and a severity colour bar instead; the star line uses "★" from the font.
- Text auto-shrinks (`card._fit`) down to a minimum size and truncates with "…" only past that; the regression test renders the longest German strings and checks nothing is cut.
- The map thumbnail reuses the report's `map.jpg` when tiles were fetched; otherwise a neutral placeholder keeps the layout.
- Both sizes plus `summary.txt` are written by `topoli audit` next to `index.html`; links carry only `src` and `lang`.
