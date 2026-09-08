# Native review of user-facing text

Every string in `i18n/{fr,de,it,en}.json` and `i18n/jargon.json` is **written per language**, not machine-translated. English is the reference; German, French and Italian were written by the maintainers in a first pass (WO-07, 2026-09-08) with Swiss conventions (ß → ss; « » in DE/FR; formal address *Sie / vous / Lei*). Before launch, one native speaker per language signs off the whole file using the checklist in `CONTRIBUTING.md`.

| Language | File | First pass | Native review | Reviewer | Notes |
|---|---|---|---|---|---|
| en | `i18n/en.json` | 2026-09-08 | ☐ pending | | reference language |
| de | `i18n/de.json` | 2026-09-08 | ☐ pending | | Swiss German orthography; check "Baugesuche" vs "Bauprojekte" wording used by the City of Zürich |
| fr | `i18n/fr.json` | 2026-09-08 | ☐ pending | | Swiss French (« septante » not needed); check RDPPF wording for Geneva/Vaud readers |
| it | `i18n/it.json` | 2026-09-08 | ☐ pending | | Ticino usage (« licenza edilizia », « fondo », « piano regolatore ») |
| all | `i18n/jargon.json` explanations | 2026-09-08 | ☐ pending | | one-line explanations for layer 1 |

## How to review

1. `uv run topoli audit "<address in your language region>" --lang <xx> --depth full` on two or three addresses and read layer 0 first: would a 14-year-old understand every sentence? Is anything a translation rather than how you would say it?
2. Open the JSON file and read every value once; edit in place. Keep the `{slots}` exactly as they are.
3. `uv run pytest tests/i18n tests/regression` — the jargon and slot tests must stay green.
4. Record your sign-off here (name, date) and in the PR.

Once a language is marked reviewed, `__TODO__` values in that file are build errors, not warnings.
