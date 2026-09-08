---
name: property-audit
description: Audit a Swiss address — what you can build, what blocks it (flood, noise, heritage, zoning), what is built nearby — sourced. Was kann ich bauen · que puis-je construire · cosa posso costruire
allowed-tools: Bash(uv *) Bash(python3 *) Read
---

# /property-audit "<address>" [--lang fr|de|it|en] [--goal "<free text>"] [--depth quick|full]

Topoli turns a Swiss address into five plain-language findings (layer 0), an 18-section sourced
report (layer 1, `index.html`) and raw evidence (layer 2, `evidence.json`). Everything is
computed by deterministic scripts from official public sources; you only present the result.

Trigger this skill for questions like "Was kann ich an der … bauen?", "Check this address before
I buy", "Qu'est-ce que je peux construire au …", "Cosa posso costruire in …", "Is … in a flood
zone / noisy / a protected building?", "What is being built near …". Any Swiss postal address,
`Parcel <municipality> <number>` or `lat,lon` works. Zürich has the deepest coverage.

## Run it (one command)

```bash
uv run --project "$(cd "${CLAUDE_SKILL_DIR}" && pwd -P)/../.." python "${CLAUDE_SKILL_DIR}/scripts/audit.py" "<address>" [--lang xx] [--goal "..."] [--depth quick|full]
```

If `uv` is missing: `python3 -m pip install "topoli @ git+https://github.com/suchipizza/Topoli"` once,
then `python3 "${CLAUDE_SKILL_DIR}/scripts/audit.py" "<address>" …`.

`--lang` defaults to the address's canton language (ZH→de, GE→fr, TI→it); if the user writes in
another of the four languages, pass theirs. `--goal` is the user's intent in their words
("build 12 apartments", "buy to renovate") and changes which findings rank first.
`--depth full` also prints the 18 sections. Never add other flags.

## What the script does (you do not redo any of it)

1. `resolve_address` → site (coordinates, municipality, canton, parcel id)
2. `get_parcel`, `get_buildings` → geometry, area, buildings from the federal register
3. federal layers → hazards, noise, contamination, public-law restrictions, solar, heritage, terrain
4. Zürich only → zoning, building-ordinance rules with article citations, development potential
5. construction events within 500 m in the last 12 months
6. ranking of findings, one recommended next step, report + card + summary written to
   `./reports/<municipality>-<parcel>/`

Progress lines (`✓ …`, `⚠ …`) stream while it runs; partial failures never abort — missing
sources become explicit "not available yet" findings.

## Output contract — present the script's text unchanged

The script prints exactly this block; show it verbatim (you may translate only the progress
lines if the user's language differs from `--lang`):

```
PROPERTY CHECK — <address>, <municipality>

<emoji>  <one sentence a homeowner understands>
    <one sentence of consequence>
… (3 to 5 findings)

Confidence: <n> official facts · <n> calculations · <n> estimates · <n> need a professional
Next step: <exactly one action, naming the article/office/document>

▸ Open full report: ./reports/<id>/index.html
▸ Share: ./reports/<id>/card.png
```

Then add one line telling the user the report and card paths are local files they can open or
send. If they ask follow-up questions, answer **only** from `./reports/<id>/evidence.json`
(read it) and say which finding and source you rely on.

## Rules you must keep

- **Never add facts not present in `evidence.json`.** No zoning rules, hazard levels, prices,
  costs, valuations or approval chances from memory. If it is not in the evidence, say it cannot
  be determined from public data and name who to ask.
- Do not "correct" or round the script's numbers, classes (A/B/C/D) or the next step.
- If the script exits with `✗ …` (address not found), ask for a postcode or municipality and run
  again; do not guess a location.
- The result never replaces an architect, the planning office, a notary or the land register —
  keep that sentence when the user asks whether they can rely on it.
