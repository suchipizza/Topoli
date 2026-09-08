# Topoli — repository context for Claude Code

Topoli is open-source construction & property intelligence for AI agents. Phase 1 ships one Claude skill, `/property-audit "<address>"`, that turns a Swiss address into five plain-language findings (layer 0), an 18-section sourced report (layer 1) and raw evidence (layer 2), in FR/DE/IT/EN, with no accounts or API keys. Goals of Phase 1: GitHub stars and waitlist signups. Full spec: `docs/topoli_product_spec_v2.md`. PRDs: `docs/prd_open_source_repo_and_skill.md`, `docs/prd_website.md`.

## Non-negotiables
1. **Deterministic data path.** `skills/property-audit/scripts/*.py` resolve, fetch, intersect and compute. The model only ranks findings and fills templates. Never write code that asks the model to "estimate" a rule, a hazard or a number.
2. **Evidence on everything.** Findings follow `core/domain/finding.py`. Class A/B findings without `source.url` and `source.retrieved_at` fail validation → downgraded to D. Do not weaken this.
3. **Abstain, don't guess.** No evidence span → class D. Conflicting sources → both shown, class D. Never produce valuations, cost estimates or approval likelihoods.
4. **Four languages.** Every user-facing string lives in `i18n/{fr,de,it,en}.json`; layer-0 templates are written per language with slots. Terms in `i18n/jargon.json` are banned from layer 0 (test enforced).
5. **No telemetry, no Topoli server calls.** Only official public sources. Local cache in `~/.topoli/cache/`.
6. **Licensing gate.** No adapter ships without an entry in `LICENCES.md` (source, licence, attribution text, redistribution allowed y/n). Datasets are fetched on demand, never redistributed.
7. **Phase 1 scope only.** One command. Zürich is the only deep canton. Anything else → `docs/decisions/` note, not code.

## Conventions
- Python ≥ 3.11, `uv` for env, `ruff` + `mypy --strict` clean, `pytest`. No GDAL; use `shapely`, `pyproj`, `httpx`.
- Coordinates: store WGS84 (EPSG:4326) and LV95 (EPSG:2056); compute areas in LV95.
- Adapters implement `core/adapters/base.py::Adapter` and live in `countries/<country>/<jurisdiction>/`. Each adapter ships fixtures for ≥ 3 sites (`tests/fixtures/<adapter_id>/`) and a nightly source-contract test.
- Commit messages: `feat(ch/zh): …`, `fix(core/evidence): …`, `docs(i18n/fr): …`.
- Before touching an external API: read its docs, put the doc URL and the exact request used in the adapter docstring, respect rate limits (≤ 25 calls per audit total), exponential backoff.
- Unknowns go in `docs/decisions/NNN-<slug>.md` (context, options, decision or open question). Do not silently pick.

## Definition of done (every WO)
Code + tests green in CI + fixtures recorded + `LICENCES.md` updated if a source was added + the WO's "done when" verified by running the stated command.
