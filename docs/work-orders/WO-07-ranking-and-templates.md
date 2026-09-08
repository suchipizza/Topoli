# WO-07 — Finding ranking and layer 0/1 templates in four languages

**Read first:** PRD (repo) §3.3, §3.4, §8; spec §6.3, §6.4.
**Depends on:** WO-03, WO-05 (WO-06 optional).

## Objective
From an `AuditResult`, produce the exact layer-0 text (3–5 findings, confidence line, one next step) and the layer-1 section content, in FR/DE/IT/EN, with no jargon on layer 0, deterministically.

## Tasks
1. `core/scoring/rank.py` — `rank_score = w_goal·goal_relevance + w_sev·severity + w_surprise·surprise`. `goal_relevance` from a small keyword→category map for `--goal` (build/extend → potential, zoning; buy → hazards, heritage, noise; renovate → solar, heritage, buildings; empty → balanced). `surprise` is a per-template constant (e.g. "listed building" = high, "no flood risk" = low unless the canton is flood-prone). Weights in `scoring/weights.yaml`; tests pin the top-5 for the fixtures.
2. Layer-0 templates: `skills/property-audit/prompts/layer0.<lang>.md` are *not* prompts — they are Jinja templates with slot rules, one finding template per `(category, outcome)` pair (e.g. `potential.headroom`, `potential.none`, `hazard.flood.none`, `hazard.flood.medium`, `noise.high`, `heritage.listed`, `activity.n`, `unknown.regulation`). Each: one sentence + one consequence sentence. Written per language by a native speaker; EN and DE first-pass by you, FR/IT marked for review in `docs/i18n-review.md` with a checklist.
3. Fill `i18n/{fr,de,it,en}.json` completely (remove all `__TODO__`), including section names 1–18, class labels, confidence line format, next-step frames, coverage stubs. Un-skip the WO-01 tests.
4. Next step selector `core/scoring/next_step.py`: exactly one, chosen by rule: listed heritage → "contact the municipal heritage office about X"; potential headroom in ZH → "verify BZO §<art> with the city planning office"; hazard medium/high → "request the cantonal hazard map extract"; else → "order the ÖREB extract". Each with the specific article/office.
5. Confidence line: counts of A/B/C/D across the five shown findings, rendered with i18n labels.
6. Number precision: layer 0 rounds to two significant figures (`~45%`, `~320 m²`); test enforces.
7. `tests/regression/test_layer0.py`: for every fixture and every language, render layer 0 and assert: 3–5 findings, no jargon (`assert_no_jargon`), one next step, confidence counts match finding classes.
8. Layer-1 content assembler `core/reporting/assemble.py`: builds the 18-section structure with "not available — help add it" stubs, class badges, and per-claim source rows for section 18.

## Done when
`topoli audit "<Zürich fixture>" --lang fr|de|it|en --depth quick` prints a compliant layer 0 in all four languages; jargon and i18n completeness tests green; ranking tests pin expected top-5 for 10 fixtures.
