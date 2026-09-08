# WO-11 — Regression set, performance, review harness

**Read first:** PRD (repo) §1 launch acceptance, §10, §11.
**Depends on:** WO-07, WO-10.

## Objective
Proof that the launch bars hold: 200-address regression, p95 ≤ 90 s, zero telemetry, and a 20-audit professional review with the error definition applied.

## Tasks
1. `tests/regression/addresses.csv` — 200 addresses: 120 City of Zürich across all zone types and districts, 30 other ZH municipalities, 50 across GE/VD/BS/BE/TI/LU/SG/VS/GR/FR. Record fixtures for all (cache-backed; live recording run once, document its date).
2. `tests/regression/test_full_audit.py` — for each address: audit completes without exception; coverage entries present for every adapter; layer 0 valid in four languages; class-A/B findings all have sources; expected findings snapshot (`expected/<slug>.json`) diffed with a readable report. Acceptance: ≥ 95% ZH-city complete, ≥ 80% elsewhere.
3. Performance: `tests/perf/test_timing.py` replays fixtures with recorded latencies (respx with per-call delays from `meta.json`), asserts p50 ≤ 60 s, p95 ≤ 90 s; also a real `-m live` timing run script producing `docs/perf-<date>.md`.
4. Call budget test: assert ≤ 25 external calls per audit on the densest fixture.
5. Telemetry test: run an audit with an egress allowlist mock; any host not in `countries/**/allowed_hosts.txt` fails the test.
6. Review harness: `topoli review export` (from WO-05) extended to all findings; `tests/review/zh20.csv` filled by the reviewing architect; `topoli review import` computes the error count per PRD §10 definition and writes `tests/review/RESULT.md`. Launch bar: ≤ 2 errors, 0 in hazards.
7. Coverage bars: `topoli coverage` prints the README/website table from `coverage.json`.

## Done when
`uv run pytest tests/regression tests/perf tests/i18n` green with the acceptance percentages printed; egress test green; `RESULT.md` exists with the bar met (or lists the fixes required).
