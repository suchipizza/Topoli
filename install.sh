#!/bin/sh
# Topoli — install the /property-audit skill for Claude Code (macOS, Linux, WSL).
#   curl -fsSL https://raw.githubusercontent.com/suchipizza/Topoli/main/install.sh | sh
# What it does: clones (or updates) the repo into ~/.topoli/src, installs the Python
# environment with uv (installing uv if missing), and links the skill into ~/.claude/skills/.
set -eu
SRC="${TOPOLI_HOME:-$HOME/.topoli/src}"
SKILLS="$HOME/.claude/skills"
REPO="https://github.com/suchipizza/Topoli.git"

if ! command -v uv >/dev/null 2>&1; then
  echo "→ installing uv (Python environment manager) …"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -d "$SRC/.git" ]; then
  echo "→ updating $SRC …"
  git -C "$SRC" pull --ff-only -q
else
  echo "→ cloning Topoli into $SRC …"
  mkdir -p "$(dirname "$SRC")"
  git clone -q --depth 1 "$REPO" "$SRC"
fi

echo "→ installing the Python environment (uv sync) …"
(cd "$SRC" && uv sync -q)

mkdir -p "$SKILLS"
rm -rf "$SKILLS/property-audit"
ln -s "$SRC/skills/property-audit" "$SKILLS/property-audit"

echo "→ checking …"
(cd "$SRC" && uv run topoli doctor --skip-network >/dev/null)
echo
echo "✓ Installed. Open Claude Code and type:  /property-audit \"Badenerstrasse 171, 8003 Zürich\""
