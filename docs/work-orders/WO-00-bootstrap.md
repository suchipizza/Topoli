# WO-00 — Repository bootstrap

**Read first:** `CLAUDE.md`, PRD (repo) §9, §12.
**Depends on:** nothing.

## Objective
An empty-but-complete `topoli` repo: layout, tooling, CI, licence files, docs copied in, so every later WO lands in a known structure.

## Tasks
1. Create the layout from PRD §9 exactly (empty `__init__.py`/`.gitkeep` where needed):
   `skills/property-audit/{SKILL.md,prompts/,scripts/}`, `core/{domain,evidence,geospatial,scoring,reporting,i18n,adapters}/`, `countries/ch/{federal,zh}/`, `ui/local-report/`, `i18n/`, `examples/`, `tests/{fixtures,source-contracts,regression,i18n,review}/`, `docs/decisions/`, `.github/{workflows,ISSUE_TEMPLATE}/`. No `website/` folder — the site is a separate private repo (`REPOS.md`).
2. `pyproject.toml` with `uv`; deps: `httpx`, `shapely`, `pyproj`, `pydantic>=2`, `jinja2`, `typer`, `rich`; dev: `pytest`, `pytest-recording` (or `vcrpy`), `ruff`, `mypy`, `respx`. Package name `topoli`, CLI entry `topoli`.
3. `LICENSE` = Apache-2.0. `LICENCES.md` with the table header (source · dataset · licence · attribution text · redistribution y/n · adapter id) and no rows.
4. `CONTRIBUTING.md` skeleton: how to add a canton (4 steps), fixture recording, native-review checklist for i18n. `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ROADMAP.md` (phases 1–7 table from spec §7).
5. Copy the spec and the repo PRD into `docs/`. The website PRD goes to `topoli-web`, not here. Copy this `CLAUDE.md` to root.
6. CI (`.github/workflows/ci.yml`): ruff, mypy, pytest on PR; `nightly.yml` running `pytest tests/source-contracts -m live` on a schedule with an action that opens/updates an issue labelled `source-degraded` on failure.
7. Issue templates: `bug`, `new-canton` (checklist: source URL, licence, fields, fixture sites), `wrong-finding` (address, finding, what's wrong, source that proves it).
8. Labels to create on the GitHub repo (document in `docs/labels.md`, apply with `gh`): `good first canton`, `good first issue`, `source-degraded`, `i18n/fr|de|it|en`, `adapter`, `report-ui`, `website`.
9. `topoli --version` and `topoli doctor` (checks Python version, network to geo.admin.ch, cache dir writable) work.

## Done when
`uv sync && uv run ruff check . && uv run mypy . && uv run pytest` all pass on an empty test set, `uv run topoli doctor` prints green, CI is green on the first PR.
