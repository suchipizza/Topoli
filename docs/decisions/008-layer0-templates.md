# 008 — Layer-0 templates live in the i18n JSON; the Jinja files are frames

**Status:** decided · 2026-09-08 · WO-07

WO-07 asked for `skills/property-audit/prompts/layer0.<lang>.md` to hold "one finding template per (category, outcome)". Since WO-03 every adapter already produces its finding sentences from `i18n/<lang>.json` under `finding.<template_key>.{title,consequence,caveat}` (slot-based, per language, jargon-tested). Duplicating those sentences in Jinja files would create two sources of truth that drift.

**Decision:** the finding sentences stay in the i18n JSON (one template per `template_key`, e.g. `hazard.flood.medium`, `potential.headroom`, `activity.n`). `layer0.<lang>.md` is the Jinja *frame* per language: header, the 3–5 finding lines, the confidence line, the single next step, and the report/share links. The frame renders the findings' pre-localized sentences; nothing in it is translated at runtime.

Related rules implemented in WO-07:
- **Ranking** (`core/scoring/rank.py`, `weights.yaml`): `goal · severity · surprise`, one finding per family on layer 0, class-D findings only when fewer than three others exist, and **any sentence containing banned jargon in the target language is ineligible** for layer 0 (so ÖREB legend texts with zone codes stay in layer 1).
- **Next step** (`core/scoring/next_step.py`): heritage → potential (Zürich, with the BZO article) → hazard → ÖREB extract → municipality; office names carry their preposition per language to avoid "à le"-type clashes.
- **Numbers**: layer-0 sentences are post-processed to two significant figures (`round_sig_text`), leaving years, codes glued to letters and article numbers untouched; the regression test enforces it.
- **Slots** may be `LocalizedText` (e.g. the list of event types) and resolve per language inside `make_finding`.
