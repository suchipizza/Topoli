# 011 — Skill install paths (Claude Code, Claude.ai) and the 3 steps

**Status:** decided for Claude Code; Claude.ai path to be verified by hand · 2026-09-08 · WO-10

Read on 2026-09-08: https://code.claude.com/docs/en/skills.md, …/plugins.md, …/plugins-reference.md, …/plugin-marketplaces.md, https://claude.com/docs/skills/overview.md, https://claude.com/docs/skills/how-to.md.

## Claude Code (primary surface)

Personal skills live in `~/.claude/skills/<name>/SKILL.md`; scripts inside the skill folder are run through `${CLAUDE_SKILL_DIR}`. The skill needs the `topoli` package and its dependencies (httpx, shapely, pyproj, pillow, pypdf …), so "copy SKILL.md" alone is not enough. Two install routes, both ≤ 3 steps:

| Route | Step 2 | Command afterwards |
|---|---|---|
| **One-line installer (default)** | `curl -fsSL https://raw.githubusercontent.com/suchipizza/Topoli/main/install.sh \| sh` (Windows: `irm …/install.ps1 \| iex`) — clones into `~/.topoli/src`, `uv sync` (installs `uv` if missing), symlinks `~/.claude/skills/property-audit` | `/property-audit "<address>"` |
| Plugin marketplace | `/plugin marketplace add suchipizza/Topoli` then `/plugin install topoli@topoli` (`.claude-plugin/plugin.json` + `marketplace.json` at the repo root, skill at `skills/property-audit/`) | `/topoli:property-audit "<address>"` — plugin skills are namespaced, and the Python environment still has to be created once with `uv sync` in the plugin folder |

The installer route is the one in the README and on the website because it yields exactly `/property-audit` and prepares the environment. `SKILL.md` runs `uv run --project <repo> python ${CLAUDE_SKILL_DIR}/scripts/audit.py …` and falls back to `pip install topoli@git+…` + `python3`.

## Claude.ai (web/desktop)

Skills exist on Pro/Max/Team/Enterprise and can include Python scripts executed in the code-execution sandbox (`dependencies:` frontmatter). **Not documented:** a self-service upload UI for custom skills, and whether the sandbox can reach arbitrary hosts (`api3.geo.admin.ch`, `maps.zh.ch`, `wmts.geo.admin.ch`, `oerebdocs.zh.ch`, `daten.statistik.zh.ch`, `amtsblattportal.ch`). Without network the scripts cannot fetch anything, so a "fetch-only variant" is meaningless there.

**Decision:** the Claude.ai tab on the website/README carries the same three steps with step 2 = "upload the skill zip under Customize → Skills" and a visible note "requires code execution; being validated". Noémie tests it once with a Pro account (PRD open question 1); if the sandbox has no network, the tab changes to "use Claude Code (5 minutes)" until Anthropic documents network access. Tracked as a `good first issue`.

## Description text

Claude.ai limits `description` to 200 characters, so the SKILL.md description is ≤ 200 characters and carries the trigger verbs in all four languages ("Was kann ich bauen · que puis-je construire · cosa posso costruire").
