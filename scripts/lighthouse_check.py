"""Assert Lighthouse category scores from a JSON report (CI gate for the local report)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

THRESHOLDS = {"performance": 0.90, "accessibility": 0.90, "best-practices": 0.90}


def main(path: str) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ok = True
    for cat, minimum in THRESHOLDS.items():
        score = float(data["categories"][cat]["score"] or 0)
        flag = "OK " if score >= minimum else "LOW"
        print(f"{flag} {cat}: {score:.2f} (min {minimum})")
        ok = ok and score >= minimum
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
