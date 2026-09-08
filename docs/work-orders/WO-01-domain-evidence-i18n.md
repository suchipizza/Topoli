# WO-01 — Domain model, evidence model, i18n scaffold

**Read first:** PRD (repo) §3.3–3.6, §5, §8; spec §8, §10.
**Depends on:** WO-00.

## Objective
The typed core every adapter and renderer builds on: `Site`, `Parcel`, `Building`, `ConstructionEvent`, `Regulation`, `Finding`, `Source`, validation rules, and the i18n loader with the jargon test.

## Tasks
1. `core/domain/*.py` — pydantic models matching spec §8 and PRD §5. `Finding.title/consequence/caveat` are `LocalizedText` (`fr, de, it, en` all required). `Finding.cls` is `Literal["A","B","C","D"]`.
2. `core/evidence/validate.py` — `validate(finding) -> Finding`: A/B without `source.url`+`retrieved_at` → cloned as D with `caveat` = i18n key `caveat.downgraded_missing_source`. Emits a structured warning. Unit tests for each rule in PRD §3.6 (missing span → D; conflicting sources → D with both listed; stale cache marker).
3. `core/evidence/report_model.py` — `AuditResult` = site + parcels + buildings + findings + coverage (per adapter: ok / degraded / not_available / not_contributed) + timings + `topoli_version` + `parser_versions`.
4. `core/i18n/` — loader for `i18n/{fr,de,it,en}.json`; `t(key, lang, **slots)`; locale formatting helpers (`fmt_area`, `fmt_number`, `fmt_date`) producing `1'234 m²` (de-CH), `1 234 m²` (fr-CH/it-CH), `1,234 m²` (en). Language default from canton (`core/i18n/canton_lang.py`: ZH→de, GE/VD/NE/JU→fr, TI→it, bilingual: BE→de, FR→fr, VS→fr, GR→de).
5. Create the four JSON files with the structural keys only (skill, report and README strings; site copy lives in `topoli-web`) (section names 1–18, class labels, confidence line, next-step frame, coverage stubs, "help add it" line). Values in EN; FR/DE/IT values marked `"__TODO__"` — the test in step 6 must fail until filled, which is intentional and tracked in WO-07.
6. `i18n/jargon.json`: list of banned layer-0 terms per language with one-line explanations (seed: Ausnützungsziffer, Baumassenziffer, Überbauungsziffer, Empfindlichkeitsstufe, ÖREB/RDPPF, COS/CUS/IUS/IOS/IM, W2/W3/W4 zone codes, ISOS, KbS, ES II/III, Gestaltungsplan, Kernzone, BZO, PBG). Tests: (a) all four files share identical key sets; (b) no `__TODO__` (skip-marked until WO-07); (c) `tests/i18n/test_jargon.py` helper `assert_no_jargon(text, lang)` used later by layer-0 tests.
7. `docs/decisions/001-domain-model.md` — record any deviation from the spec schema and why.

## Done when
`uv run pytest tests/core tests/i18n -k "not todo"` green; `python -c "from topoli.core.domain import Finding"` works; a sample `Finding` with missing source round-trips through `validate()` as class D.
