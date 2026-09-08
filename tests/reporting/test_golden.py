"""Golden byte-compare of three example reports modulo timestamps/versions (WO-08).

Regenerate after an intentional template change:
    TOPOLI_UPDATE_GOLDEN=1 uv run pytest tests/reporting/test_golden.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.build_report_offline import build
from topoli.core.adapters import set_client
from topoli.core.reporting.html import normalize_for_golden

GOLDEN = Path(__file__).resolve().parents[1] / "golden"
CASES = [
    ("zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich", "de"),
    ("zurich-limmatquai-1", "Limmatquai 1, 8001 Zürich", "en"),
    ("bern-bundesplatz-3", "Bundesplatz 3, 3011 Bern", "fr"),
]


@pytest.mark.parametrize(("slug", "address", "lang"), CASES, ids=[c[0] for c in CASES])
def test_golden_report(slug: str, address: str, lang: str, tmp_path: Path) -> None:
    path = build(slug, address, tmp_path, lang)
    set_client(None)
    actual = normalize_for_golden(path.read_text(encoding="utf-8"))
    golden = GOLDEN / f"{slug}.{lang}.html"
    if os.environ.get("TOPOLI_UPDATE_GOLDEN") == "1" or not golden.is_file():
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(actual, encoding="utf-8")
        pytest.skip(f"golden written: {golden.name}")
    expected = golden.read_text(encoding="utf-8")
    if actual != expected:
        a, b = actual.splitlines(), expected.splitlines()
        first = next(
            (i for i, (x, y) in enumerate(zip(a, b, strict=False)) if x != y), min(len(a), len(b))
        )
        got = a[first][:160] if first < len(a) else "<eof>"
        exp = b[first][:160] if first < len(b) else "<eof>"
        pytest.fail(
            f"{golden.name} differs at line {first + 1}:\n  got: {got}\n  exp: {exp}\n"
            "Run with TOPOLI_UPDATE_GOLDEN=1 after an intentional change."
        )
