# 001 — Python package layout: `topoli/` package, assets at the repo root

**Status:** decided · 2026-09-08 · WO-00

## Context

PRD §9 sketches `core/`, `countries/` and `skills/` as sibling folders at the repository root, while WO-01's "done when" requires `from topoli.core.domain import Finding` to work and `CLAUDE.md` requires `mypy --strict` and one-command install (`uv sync`). Root-level `core/` and `countries/` cannot be imported as `topoli.core` without a build-time path rewrite that editable installs and mypy do not follow reliably.

## Options

1. Root-level `core/`, `countries/` imported as bare top-level packages (`import core`). Rejected: collides with any other package named `core`, and breaks the `topoli.*` namespace WO-01 requires.
2. Hatch `sources` rewrite mapping `core → topoli/core` at wheel build. Rejected: editable installs and mypy see different module paths from the wheel.
3. **A real `topoli/` package holding `core/` and `countries/`; everything non-Python stays at the root.** Chosen.

## Decision

```text
topoli/                 Python package (imports: topoli.core.*, topoli.countries.ch.*)
├── core/{domain,evidence,geospatial,scoring,reporting,i18n,adapters}/
├── countries/ch/{federal,zh}/
├── cli.py · paths.py
skills/property-audit/  SKILL.md, prompts/, scripts/   (what users install)
ui/local-report/        report template, card renderer
i18n/                   {fr,de,it,en,jargon}.json
examples/ · tests/ · docs/
```

Wherever the PRD or `CLAUDE.md` says `core/…` or `countries/…`, read `topoli/core/…` and `topoli/countries/…`. Root assets (`i18n/`, `ui/`, `skills/`) are force-included into the wheel under `topoli/_data/` and located at runtime by `topoli.paths.asset_dir()`, so the installed package and the checkout behave identically.

## Consequences

- One `uv sync` gives a working editable install; `mypy --strict` type-checks the same paths that ship.
- Contributors find adapters where `CONTRIBUTING.md` says: `topoli/countries/ch/<canton>/`.
- The skill folder stays at the root so the 3-step install can point at `skills/property-audit/` directly.
