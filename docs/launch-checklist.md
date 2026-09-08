# Launch checklist — public repository (the site half lives in the private repo)

Tick before tagging `v0.1.0`.

## Repository settings (GitHub UI / `gh`)
- [ ] Description = "Open-source construction intelligence for AI agents" (`gh repo edit -d …`)
- [ ] Homepage = site URL once the domain is cleared (`gh repo edit -h …`)
- [ ] Topics: `switzerland`, `open-data`, `claude-skill`, `ai-agents`, `proptech`, `construction`, `geospatial` (`gh repo edit --add-topic …`)
- [ ] Social preview image = `examples/zurich-badenerstrasse/card.png` (Settings → General → Social preview; no API for this)
- [ ] Discussions enabled with a "Show your report" category
- [ ] Secret scanning + push protection on; `TOPOLI_WEB_DISPATCH_TOKEN` (fine-grained PAT, `repository_dispatch` on `topoli-web` only) stored as an Actions secret
- [ ] Branch protection on `main`: require the `checks` and `report-quality` jobs

## Content
- [ ] Ten seeded issues exist with labels (`docs/seed-issues/`, `scripts/seed_issues.sh`)
- [ ] `docs/demo.gif` recorded (`docs/demo-script.md`), ≤ 5 MB, linked from all four READMEs
- [ ] `docs/i18n-review.md`: fr/de/it signed off by native speakers
- [ ] `tests/review/RESULT.md`: launch bar met (≤ 2 errors in 20 audits, 0 in hazards)
- [ ] `scripts/sync_readme.py --check` green; coverage table matches `topoli coverage`
- [ ] `docs/decisions/011`: Claude.ai path tested (network from the sandbox yes/no) and the README tab adjusted

## Release
- [ ] `uv run pytest` green, `uv run pytest -m live tests/source-contracts -o addopts=""` green today
- [ ] `git tag v0.1.0 && git push --tags` → `release.yml` builds examples, `coverage.json`, `i18n.tar.gz`, `card-<lang>.png`, attaches them and dispatches `topoli-release` to the site repo
- [ ] Site live in four languages, `/run` counter answering, star count live
