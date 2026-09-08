# WO-10 — Skill packaging: SKILL.md, scripts, 3-step install

**Read first:** PRD (repo) §3.1–3.2, §9 (install), §15 open question 1; spec §6.1–6.2.
**Depends on:** WO-08.

## Objective
The thing users install. `/property-audit "<address>"` works in Claude Code in three steps; a Claude.ai path exists (full or fetch-only variant) and is documented with the same three steps.

## Tasks
1. Investigate the current Claude skill packaging and install mechanics for Claude Code and Claude.ai (read the official docs at implementation time; do not rely on memory). Write `docs/decisions/00x-skill-install-paths.md` with: exact install steps for each surface, whether scripts can execute on Claude.ai, and the chosen variant for Claude.ai.
2. `skills/property-audit/SKILL.md`: frontmatter `name: property-audit`, a trigger `description` that fires on natural-language questions ("what can I build at…", "check this address", DE/FR/IT equivalents listed); body = invocation, flags, the pipeline as an ordered list of script calls, the *exact* layer-0 output contract, abstention rules, and the rule "never add facts not present in `evidence.json`". Keep it under ~150 lines; details live in scripts.
3. `skills/property-audit/scripts/audit.py` — single entry point `python audit.py "<address>" --lang --goal --depth --json` that runs the whole deterministic pipeline and prints progress lines (`✓ Resolved address` … `⚠ Cantonal regulation not available for VS — help add it`) then the layer-0 text and the report path. The skill instructs Claude to run this and then present the output unchanged, translating only the progress narration if the user's language differs.
4. One-line install for Claude Code (whatever the mechanism is — a marketplace/plugin manifest, a `git clone` + skill folder, or an installer script `install.sh`/`install.ps1` that creates a venv and links the skill). Must be ≤ 3 steps total including opening Claude; tabs handle OS differences, never extra steps.
5. Natural-language trigger test: a checklist of 12 phrasings (3 per language) documented in `tests/skill/triggers.md` with manual verification results.
6. `examples/` — commit three generated example folders (Zürich ×2, Genève federal-only) produced by the real pipeline; README links to them.
7. Record the 30-second GIF script (`docs/demo-script.md`): prompt → progress lines → five findings → report opening. Actual recording is done by you (Noémie) with a recording tool; the WO produces the script and a `topoli demo` command that replays a fixture with realistic timing.

## Done when
On a clean macOS and a clean Ubuntu VM: follow only the README's three steps → `/property-audit "Badenerstrasse 123, Zürich"` → layer 0 on screen ≤ 90 s and `index.html` opens. Claude.ai path documented and tested or explicitly scoped as fetch-only with a working variant.
