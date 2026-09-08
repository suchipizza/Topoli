"""Skill packaging (WO-10): SKILL.md contract, offline audit.py, committed examples, installers."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from topoli.core.adapters.fixtures import fixture_folders, seed_cache
from topoli.core.adapters.registry import all_ids
from topoli.core.evidence import AuditResult
from topoli.paths import repo_root

ROOT = repo_root()
SKILL = ROOT / "skills" / "property-audit"


def _frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with YAML frontmatter"
    return dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)


def test_skill_md_contract() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    fm = {k.strip(): v.strip() for k, v in _frontmatter(text).items()}
    assert fm["name"] == "property-audit"
    assert len(fm["description"]) <= 200, "Claude.ai limits descriptions to 200 characters"
    for phrase in ("Was kann ich bauen", "que puis-je construire", "cosa posso costruire"):
        assert phrase in fm["description"]
    assert text.count("\n") < 150
    assert "${CLAUDE_SKILL_DIR}/scripts/audit.py" in text
    assert "PROPERTY CHECK" in text and "Next step:" in text and "Confidence:" in text
    assert "Never add facts not present in `evidence.json`" in text
    assert "--lang" in text and "--goal" in text and "--depth" in text


def test_audit_script_runs_offline(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    for adapter_id in all_ids():
        folders = fixture_folders(adapter_id, "zurich-badenerstrasse-171")
        if folders:
            seed_cache(cache, *folders)
    env = {**os.environ, "TOPOLI_CACHE_DIR": str(cache), "TOPOLI_OFFLINE": "1"}
    proc = subprocess.run(
        [
            sys.executable,
            str(SKILL / "scripts" / "audit.py"),
            "Badenerstrasse 171, 8003 Zürich",
            "--lang",
            "en",
            "--no-report",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-800:]
    out = proc.stdout
    assert out.startswith("✓ Resolved address")
    assert "PROPERTY CHECK — Badenerstrasse 171" in out
    assert "Confidence:" in out and "Next step:" in out
    assert (
        3
        <= sum(
            1
            for ln in out.splitlines()
            if ln
            and not ln.startswith((" ", "✓", "⚠", "▸", "PROPERTY", "Confidence", "Next"))
            and ln[0] not in "-"
        )
        <= 8
    )


def test_examples_are_real_reports() -> None:
    examples = sorted(p for p in (ROOT / "examples").iterdir() if p.is_dir())
    names = [p.name for p in examples]
    assert {"zurich-badenerstrasse", "zurich-limmatquai", "geneva-federal-only"} <= set(names)
    for folder in examples:
        for f in ("index.html", "evidence.json", "summary.txt", "card.png", "card-square.png"):
            assert (folder / f).is_file(), f"{folder.name}/{f}"
        result = AuditResult.model_validate_json(
            (folder / "evidence.json").read_text(encoding="utf-8")
        )
        assert result.findings and all(f.source for f in result.findings)
        page = (folder / "index.html").read_text(encoding="utf-8")
        assert 'id="topoli-data"' in page and "github.com/suchipizza/Topoli" in page
    geneva = AuditResult.model_validate_json(
        (ROOT / "examples" / "geneva-federal-only" / "evidence.json").read_text(encoding="utf-8")
    )
    assert geneva.site.jurisdiction.canton == "GE"
    assert not any(c.adapter_id.startswith("ch/zh/") for c in geneva.coverage), (
        "federal-only example"
    )


def test_installers_parse() -> None:
    subprocess.run(["sh", "-n", str(ROOT / "install.sh")], check=True)
    assert (ROOT / "install.ps1").read_text(encoding="utf-8").startswith("# Topoli")
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert (
        plugin["name"] == "topoli" and market["plugins"][0]["source"]["repo"] == "suchipizza/Topoli"
    )


def test_triggers_checklist_has_twelve_phrasings() -> None:
    text = (ROOT / "tests" / "skill" / "triggers.md").read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if re.match(r"\|\s*\d+\s*\|", ln)]
    assert len(rows) == 12
    for lang in ("de", "fr", "it", "en"):
        assert sum(1 for r in rows if f"| {lang} |" in r) == 3
