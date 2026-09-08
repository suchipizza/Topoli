"""``summary.txt`` — layer 0 verbatim plus the run link and the star line (PRD §7)."""

from __future__ import annotations

from pathlib import Path

from topoli.core.i18n import t
from topoli.core.reporting.layer0 import Layer0
from topoli.core.reporting.share import TOPOLI_REPO_URL, run_link


def summary_text(layer0: Layer0) -> str:
    lang = layer0.lang
    lines = [
        layer0.text.rstrip(),
        "",
        t("layer0.run_yourself", lang, url=run_link("summary", lang)),
        t("layer0.star", lang, url=TOPOLI_REPO_URL),
        "",
    ]
    return "\n".join(lines)


def write_summary(layer0: Layer0, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "summary.txt"
    path.write_text(summary_text(layer0), encoding="utf-8")
    return path
