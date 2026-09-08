# Contributing to Topoli

Thanks for helping. The most valuable contributions are **jurisdictions** (a canton, a city), **fixtures** (real addresses that prove an adapter works) and **native-language review** of user-facing text.

## Ground rules

Read `CLAUDE.md` first — its non-negotiables apply to humans too:

1. Deterministic scripts fetch and compute. Never ask a model to estimate a rule, a hazard or a number.
2. Every class A/B finding carries `source.url` and `source.retrieved_at`, or validation downgrades it to D.
3. Abstain rather than guess. No valuations, cost estimates or approval likelihoods.
4. Four languages. Templates are written per language, never machine-translated. No jargon on layer 0.
5. No telemetry, no Topoli server calls. Official public sources only.
6. No adapter without a row in `LICENCES.md`. Datasets are fetched on demand, never redistributed.

## Set up

```bash
git clone https://github.com/suchipizza/Topoli.git && cd Topoli
uv sync
uv run topoli doctor
uv run ruff check . && uv run mypy . && uv run pytest
```

## Add your canton in 4 steps

1. **Open (or claim) a `good first canton` issue.** Fill the `new-canton` template: source URL, licence terms, fields available, three fixture addresses. If licensing or availability is unclear, write it up in `docs/decisions/NNN-<slug>.md` — do not work around it.
2. **Write the adapter** in `topoli/countries/ch/<canton>/`, implementing the `Adapter` protocol from `topoli/core/adapters/base.py` (`id`, `jurisdiction`, `licence`, `ttl`, `fetch`, `to_findings`, `health`) and registering it in the package `__init__` via `topoli.core.adapters.registry.register`. Put the official documentation URL and the exact request you use in the module docstring. Respect rate limits; the shared HTTP client enforces the per-audit call budget.
3. **Record fixtures and tests.** `uv run topoli fixtures record --adapter <id> --address "<addr>"` for at least three sites, including one negative case. Add a source-contract test under `tests/source-contracts/` marked `live`, and localized finding templates in all four `i18n/*.json` files (mark languages you cannot write natively with `__TODO__` and list them in `docs/i18n-review.md`).
4. **Add the licence row** to `LICENCES.md` and open the PR. CI runs ruff, mypy, pytest and the jargon test. A maintainer runs the live contract test before merge.

## Recording fixtures

Fixtures are the adapter's raw responses in the cache file format plus a `meta.json` (address, date, endpoints, version) under `tests/fixtures/<adapter_id>/<slug>/`:

```bash
uv run topoli fixtures record --adapter ch/federal/parcel --address "Via Nassa 5, 6900 Lugano" --slug lugano-via-nassa-5
uv run topoli fixtures list
```

In tests, the `replay(adapter_id, slug)` fixture seeds a temporary cache from those files; every test is offline unless marked `live` (`uv run pytest -m live tests/source-contracts -o addopts=""` hits the network). Re-record when a source changes its schema, and mention the recording date in the PR.

## Native-review checklist for i18n

Each of `i18n/{fr,de,it,en}.json` is signed off by a native speaker before launch. Reviewer checklist:

- [ ] Every value reads as if written in this language, not translated.
- [ ] Layer-0 strings contain no term from `i18n/jargon.json` for this language (the test enforces it; you check the *feel*).
- [ ] A 14-year-old would understand every layer-0 sentence.
- [ ] Numbers, areas and dates use the locale format (`1'234 m²` de-CH, `1 234 m²` fr-CH/it-CH, `1,234 m²` en).
- [ ] The professional-boundary sentence ("does not replace an architect, planning office, notary or land register") is present and idiomatic.
- [ ] No sentence implies a valuation, cost, or approval likelihood.
- [ ] Record your sign-off (name, date, file hash) in `docs/i18n-review.md`.

## Commit messages

`feat(ch/zh): …`, `fix(core/evidence): …`, `docs(i18n/fr): …`, `test(regression): …`, `chore(ci): …`.

## Reporting a wrong finding

Use the `wrong-finding` issue template: address, the finding, what is wrong, and the official source that proves it. Wrong hazard findings are treated as release blockers.
