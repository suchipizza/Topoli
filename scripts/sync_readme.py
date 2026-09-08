"""Keep the four READMEs in lockstep with ``i18n/*.json`` (install steps) and ``coverage.json``.

    uv run python scripts/sync_readme.py            # rewrite the marked blocks
    uv run python scripts/sync_readme.py --check    # exit 1 if any README is out of date

Blocks are delimited by ``<!-- topoli:install:start -->`` / ``end`` and
``<!-- topoli:coverage:start -->`` / ``end``; everything else is written by hand, per language.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

from topoli.core.domain import Lang
from topoli.core.i18n import load
from topoli.core.scoring.coverage import build_coverage

ROOT = Path(__file__).resolve().parents[1]
READMES = {"en": "README.md", "fr": "README.fr.md", "de": "README.de.md", "it": "README.it.md"}
LABELS = {
    "en": ("Canton", "Federal layers", "Cantonal depth", "Construction events", "help add yours →"),
    "fr": (
        "Canton",
        "Couches fédérales",
        "Profondeur cantonale",
        "Chantiers",
        "aidez-nous à ajouter le vôtre →",
    ),
    "de": (
        "Kanton",
        "Bundesebenen",
        "Kantonale Tiefe",
        "Bautätigkeit",
        "helfen Sie mit, Ihren hinzuzufügen →",
    ),
    "it": (
        "Cantone",
        "Livelli federali",
        "Profondità cantonale",
        "Cantieri",
        "aiutaci ad aggiungere il tuo →",
    ),
}
CONTRIBUTE = "https://github.com/suchipizza/Topoli/labels/good%20first%20canton"


def install_block(lang: str) -> str:
    strings = load(cast(Lang, lang))
    return "\n".join(f"{i}. {strings[f'install.step{i}']}" for i in (1, 2, 3))


def coverage_block(lang: str) -> str:
    data = build_coverage()
    c_canton, c_fed, c_cant, c_ev, help_txt = LABELS[lang]
    rows = [f"| {c_canton} | {c_fed} | {c_cant} | {c_ev} |", "|---|---|---|---|"]
    ordered = [
        "ZH",
        "GE",
        "VD",
        "BS",
        "BE",
        "TI",
        "LU",
        "SG",
        "VS",
        "GR",
        "FR",
        "AG",
        "NE",
        "JU",
        "SO",
        "TG",
        "SH",
        "SZ",
        "ZG",
        "BL",
        "AR",
        "AI",
        "GL",
        "OW",
        "NW",
        "UR",
    ]
    for canton in ordered:
        row = data["cantons"][canton]
        cells = [_bar(row["federal_pct"]), _bar(row["cantonal_pct"]), _bar(row["events_pct"])]
        rows.append(f"| {canton} | " + " | ".join(cells) + " |")
    rows.append("")
    rows.append(f"[{help_txt}]({CONTRIBUTE})")
    return "\n".join(rows)


def _bar(pct: int) -> str:
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled) + f" {pct}%"


def render(text: str, lang: str) -> str:
    text = _replace(text, "install", install_block(lang))
    return _replace(text, "coverage", coverage_block(lang))


def _replace(text: str, block: str, content: str) -> str:
    start, end = f"<!-- topoli:{block}:start -->", f"<!-- topoli:{block}:end -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        msg = f"marker {start} missing"
        raise SystemExit(msg)
    return pattern.sub(f"{start}\n{content}\n{end}", text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    stale = []
    for lang, name in READMES.items():
        path = ROOT / name
        current = path.read_text(encoding="utf-8")
        updated = render(current, lang)
        if updated != current:
            if args.check:
                stale.append(name)
            else:
                path.write_text(updated, encoding="utf-8")
                print(f"updated {name}")
    if stale:
        print("out of date: " + ", ".join(stale) + " — run scripts/sync_readme.py")
        return 1
    print("READMEs in sync" if args.check else "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
