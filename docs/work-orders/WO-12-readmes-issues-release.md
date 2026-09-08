# WO-12 — READMEs in four languages, seeded issues, release v0.1.0

**Read first:** PRD (repo) §9 (README, hygiene), §13; spec §12.
**Depends on:** WO-09, WO-10, WO-11.

## Objective
Launch-ready repository surface: four READMEs written per language, social preview, topics, ten seeded issues, tagged release with the website publish hook.

## Tasks
1. `README.md` (EN, canonical) in the PRD §9 order: tagline + GIF placeholder path `docs/demo.gif`; "Run it in 3 steps" (the canonical install steps live in `i18n/*.json` under `install.step1..3`; `scripts/sync_readme.py` renders them into the READMEs, and `topoli-web` consumes the same JSON from the release artefact so README and site cannot drift); five try-it prompts with hooks; coverage table from `topoli coverage`; "what it does not do"; "coming next — vote on the waitlist" (four future commands with the waitlist link `?src=readme`); contributing in 4 steps; licences; star badge.
2. `README.fr.md`, `README.de.md`, `README.it.md` — written, not translated; mark in `docs/i18n-review.md` for native review. Language links at the top of each.
3. `LICENCES.md` final pass: every adapter present, attribution strings verified against source terms.
4. Seed issues (create via `gh`, bodies in `docs/seed-issues/`): 6× `good first canton` (GE regulation parsing, VD, BS, BE, TI, LU — each with source hints), 2× `good first issue` (Romansh strings; add a missing federal layer), 2× report-ui. Enable Discussions with a "Show your report" category.
5. Repo settings checklist in `docs/launch-checklist.md`: topics (`switzerland`, `open-data`, `claude-skill`, `ai-agents`, `proptech`, `construction`, `geospatial`), social preview = property card for the flagship example, description = tagline, homepage = site URL, `FUNDING.yml` optional.
6. `release.yml`: on tag `v*` — run full CI, build examples, regenerate `coverage.json`, attach to the release: `examples/*.zip`, `coverage.json`, `i18n.tar.gz` (the four JSON files + `jargon.json`), `card-<lang>.png` ×4 for the flagship example; then `repository_dispatch` to `topoli-web` (event `topoli-release`, payload = tag) using a fine-grained token stored as a secret. The public repo never references private repo contents.
7. Tag `v0.1.0` only after WO-11's bars are met and the website (WO-13–15) is live.

## Done when
All four READMEs render on GitHub with working links; `scripts/sync_readme.py --check` passes; ten issues exist with labels; `git tag v0.1.0` triggers a green release and a website deploy.
