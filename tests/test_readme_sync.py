"""The four READMEs stay in lockstep with i18n install steps and coverage.json (WO-12)."""

from __future__ import annotations

import re
import subprocess
import sys

from topoli.paths import repo_root

ROOT = repo_root()
READMES = ["README.md", "README.fr.md", "README.de.md", "README.it.md"]


def test_sync_check_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_readme.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_readmes_share_structure() -> None:
    for name in READMES:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert text.startswith('<p align="right">'), name
        assert "docs/demo.gif" in text and "install.sh | sh" in text, name
        assert "/nearby-construction" in text and "?src=readme&lang=" in text, name
        assert "LICENCES.md" in text and "good%20first%20canton" in text, name
        assert re.search(
            r"topoli:install:start -->\n1\. .+\n2\. .+\n3\. .+\n<!-- topoli:install:end", text
        ), name
        assert "| ZH |" in text and "| TI |" in text, name
        for other in READMES:
            if other != name:
                assert f'href="{other}"' in text, f"{name} must link to {other}"
    assert (ROOT / "docs" / "seed-issues").is_dir()
    assert len(list((ROOT / "docs" / "seed-issues").glob("*.md"))) == 10
