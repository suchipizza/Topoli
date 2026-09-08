# WO-09 — Share artefacts: property card and summary text

**Read first:** PRD (repo) §7; PRD (website) §5–6.
**Depends on:** WO-08.

## Objective
Every audit also yields `card.png` (1200×630 and 1080×1080) and `summary.txt`, each carrying the project name, the `topoli.<tld>/run?src=card&lang=xx` link and the star CTA. Card generation must not add an install step for the user.

## Tasks
1. Decide renderer: try a pure-Python path first (`Pillow` + bundled OFL font + the SVG map thumbnail rasterized via `cairosvg` or resvg wheel). Only fall back to Playwright if quality is unacceptable; in that case degrade gracefully (HTML-only + notice) when the browser is absent. Record the decision in `docs/decisions/`.
2. `ui/local-report/card/` — layout: address line, five findings with emoji + one sentence each (consequence dropped), map thumbnail, confidence line, project wordmark, `Run this yourself in 3 steps → topoli.<tld>/run`, `⭐ Star on GitHub`. Localized. Text auto-shrinks to fit; test with the longest DE strings.
3. `summary.txt`: layer 0 verbatim + the run link + star line.
4. Share link builder: `core/reporting/share.py` — `TOPOLI_SITE_URL` constant (the public site URL; the site itself is a separate repo); params only `src` and `lang`, never address or IDs. Test asserts no address substring in any URL.
5. Add "Share" button behaviour in the report: download `card.png`, copy `summary.txt`, "copy link" (to the report's own path — local file — with a note that the HTML file itself is the shareable artefact).

## Done when
`topoli audit …` produces both PNG sizes and `summary.txt` in all four languages on a machine without a browser installed; the URL test passes; a DE card with the longest fixture strings has no overflow.
