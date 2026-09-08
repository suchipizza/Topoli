# Work orders (Phase 1)

Each `WO-xx` file is a self-contained brief for a Claude Code session. Run them in order; each lists its dependencies and a hard "done when" that is verified by running the stated command before moving on. `CLAUDE.md` at the repository root is the standing context every session reads.

| WO | Deliverable | Depends on |
|---|---|---|
| 00 | Repo bootstrap, tooling, CI skeleton | — |
| 01 | Domain + evidence model, i18n scaffold | 00 |
| 02 | Federal adapters: geocode, parcel, buildings | 01 |
| 03 | Federal layer adapters: hazards, noise, contamination, ÖREB, solar, heritage, terrain | 02 |
| 04 | Cache, adapter contract tests, fixtures recorder | 02 |
| 05 | Zürich zoning, BZO regulation extraction, potential calc | 03, 04 |
| 06 | Zürich construction events | 04 |
| 07 | Finding ranking + layer 0/1 templates in FR/DE/IT/EN | 03, 05 |
| 08 | HTML report + evidence.json | 07 |
| 09 | Share artefacts: card.png, summary.txt | 08 |
| 10 | Skill packaging: SKILL.md, scripts, 3-step install | 08 |
| 11 | Regression suite, performance, jargon and review harness | 07, 10 |
| 12 | READMEs ×4, seeded issues, release v0.1.0 | 09, 10, 11 |

Critical path to a first real audit: 00→01→02→04→03→05→07→08→10. The website is a separate repository and consumes this repository's release artefacts (`coverage.json`, `i18n.tar.gz`, example reports, share cards).
