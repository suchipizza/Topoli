# GitHub labels

Applied with `gh label create` (idempotent with `--force`). Re-run the block below after creating the repository or when a label is missing.

| Label | Colour | Purpose |
|---|---|---|
| `good first canton` | `#0E8A16` | A jurisdiction adapter a newcomer can add following CONTRIBUTING's 4 steps |
| `good first issue` | `#7057FF` | Small, well-scoped task |
| `source-degraded` | `#D93F0B` | Opened/updated by the nightly source-contract run when a live endpoint drifts |
| `adapter` | `#1D76DB` | Data adapter work |
| `report-ui` | `#FBCA04` | The local HTML report and share artefacts |
| `website` | `#C5DEF5` | Website-related (tracked in the site repo; label kept for cross-links) |
| `i18n/fr` | `#BFD4F2` | French copy or review |
| `i18n/de` | `#BFD4F2` | German copy or review |
| `i18n/it` | `#BFD4F2` | Italian copy or review |
| `i18n/en` | `#BFD4F2` | English copy or review |
| `wrong-finding` | `#B60205` | A reported incorrect finding (hazard errors are release blockers) |

```bash
R=suchipizza/Topoli
gh label create "good first canton" -R $R -c 0E8A16 -d "Add a jurisdiction adapter following CONTRIBUTING" --force
gh label create "good first issue"  -R $R -c 7057FF -d "Small, well-scoped task" --force
gh label create "source-degraded"   -R $R -c D93F0B -d "Nightly source-contract test found endpoint drift" --force
gh label create "adapter"           -R $R -c 1D76DB -d "Data adapter work" --force
gh label create "report-ui"         -R $R -c FBCA04 -d "Local HTML report and share artefacts" --force
gh label create "website"           -R $R -c C5DEF5 -d "Website-related" --force
for l in fr de it en; do gh label create "i18n/$l" -R $R -c BFD4F2 -d "Copy or native review: $l" --force; done
gh label create "wrong-finding"     -R $R -c B60205 -d "Reported incorrect finding" --force
```
