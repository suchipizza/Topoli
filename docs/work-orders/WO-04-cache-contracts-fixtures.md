# WO-04 — Cache, source-contract tests, fixture recorder

**Read first:** PRD (repo) §4.3, §4.4, §10.
**Depends on:** WO-02.

## Objective
Reliability plumbing every adapter uses: on-disk cache with TTLs and staleness markers, a one-command fixture recorder, a nightly contract-test harness that flips coverage to "degraded", and rate limiting.

## Tasks
1. `core/adapters/cache.py` — `~/.topoli/cache/<adapter_id>/<sha256(request)>.json`; TTL 30 d default, 24 h for event adapters (adapter declares `ttl`); `--no-cache`; stale-but-served behaviour: if refetch fails, serve cached and set `Record.stale_as_of`.
2. `core/adapters/http.py` — shared `httpx` client: per-host rate limits, exponential backoff (3 retries), timeouts (10 s), user agent `topoli/<version> (+repo url)`, global call budget ≤ 25 per audit (raise `BudgetExceeded`, which the pipeline turns into degraded coverage, not a crash).
3. `topoli fixtures record --adapter <id> --address "<addr>"` — records raw responses into `tests/fixtures/<adapter_id>/<slug>/` with a `meta.json` (address, date, endpoint). `topoli fixtures list`.
4. Contract tests: `tests/source-contracts/test_<adapter>.py` marked `live`, assert response schema keys and geometry validity; a summary JSON is written to `tests/source-contracts/last_run.json` and `coverage.json` marks failing adapters `degraded`.
5. `nightly.yml` uploads `last_run.json` as an artifact and opens/updates one issue per degraded adapter (title `source-degraded: <adapter_id>`).
6. `topoli cache stats|clear`.

## Done when
Running the same audit twice hits the network 0 times the second run (assert via a counter in the client); `uv run pytest -m live tests/source-contracts` passes; simulated failure of one adapter (respx) yields `degraded` in `coverage.json` and a served-stale marker.
