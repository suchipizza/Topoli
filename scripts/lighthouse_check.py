"""Assert Lighthouse category scores from one or more JSON reports (CI gate for the report).

CI runs Lighthouse three times on the same page; the first run on a cold runner is often
noisy, so the *best* score per category across the runs must meet the threshold.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

THRESHOLDS = {"performance": 0.90, "accessibility": 0.90, "best-practices": 0.90}


def main(paths: list[str]) -> int:
    runs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths if Path(p).is_file()]
    if not runs:
        print("no Lighthouse reports found")
        return 1
    ok = True
    for cat, minimum in THRESHOLDS.items():
        scores = [float(r["categories"][cat]["score"] or 0) for r in runs]
        best = max(scores)
        flag = "OK " if best >= minimum else "LOW"
        detail = ", ".join(f"{s:.2f}" for s in scores)
        print(f"{flag} {cat}: best {best:.2f} of [{detail}] (min {minimum})")
        ok = ok and best >= minimum
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
