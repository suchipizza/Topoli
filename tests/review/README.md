# Professional review harness (PRD §10)

Before launch, an architect reviews 20 City of Zürich audits. `tests/review/zh20.txt` lists the addresses; `uv run topoli review export --addresses tests/review/zh20.txt --out tests/review/zh20.csv` writes one row per address with the zone, every extracted rule (value + article), the potential inputs and result, all findings with their class, and the source URLs. The reviewer fills `reviewer_verdict` (`ok` / `error`) and `reviewer_comment` per row.

## What counts as an error

A **finding error** is (PRD §10):

1. a class **A** (official fact) or class **B** (deterministic derived fact) claim that is **wrong** — the value, the zone, the rule, the object, or the hazard exposure does not match the authoritative source; or
2. a class **C** (estimate) or **D** (needs a professional) statement that is **presented as A/B** — for instance an estimate rendered without its caveat, or a rule shown as official when the ordinance text does not support it.

Not errors: a class-D "cannot be determined" where the reviewer could determine it with professional judgement (that is by design); a class-C estimate the reviewer would compute differently, as long as the inputs and formula shown are correct and the caveat is present.

**Launch bar:** ≤ 2 errors in 20 audits, **0** in hazards. Results are recorded in `tests/review/RESULT.md` (WO-11's `topoli review import` computes the count).
