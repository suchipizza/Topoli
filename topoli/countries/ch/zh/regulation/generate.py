"""Write ``generated/zones.yaml`` from a parse of the BZO text (``python -m … .generate``).

The YAML is checked in so reviewers (and the architect review, PRD §10) can read every extracted
rule with its article; the test suite diff-checks it against a fresh parse of the recorded text.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from topoli.countries.ch.zh.regulation.parser import ParsedBzo, parse_bzo

GENERATED = Path(__file__).resolve().parent / "generated" / "zones.yaml"


def to_dict(parsed: ParsedBzo, version_line: str) -> dict[str, Any]:
    zones: dict[str, Any] = {}
    for code in sorted(parsed.zones):
        zr = parsed.zones[code]
        zones[code] = {
            "rules": [
                {
                    "key": r.key,
                    "value": r.value,
                    "unit": r.unit,
                    "article": r.evidence_spans[0].article,
                    "span": r.evidence_spans[0].text,
                }
                for r in zr.rules
            ],
            "unresolved": sorted(zr.unresolved),
        }
    return {"parser_version": parsed.parser_version, "source_version": version_line, "zones": zones}


def render(parsed: ParsedBzo, version_line: str) -> str:
    return yaml.safe_dump(
        to_dict(parsed, version_line), allow_unicode=True, sort_keys=False, width=110
    )


def main(argv: list[str] | None = None) -> int:
    from topoli.countries.ch.zh.regulation.source import bzo_text, bzo_version, fetch_bzo

    record = fetch_bzo("ch/zh/regulation")
    text = bzo_text(record)
    parsed = parse_bzo(text)
    GENERATED.parent.mkdir(parents=True, exist_ok=True)
    GENERATED.write_text(render(parsed, bzo_version(record)), encoding="utf-8")
    print(f"wrote {GENERATED} ({len(parsed.zones)} zones)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
