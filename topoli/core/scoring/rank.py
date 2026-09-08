"""Finding ranking for layer 0 (PRD §3.3): goal relevance, severity, surprise — from weights.yaml.

Deterministic: the same findings and goal always yield the same order. Ties are broken by
finding id. Findings are also filtered for layer-0 *eligibility*: one per category family
(``id`` prefix before the first dot), no class-D unknowns unless nothing else is left, and no
sentence containing banned jargon in the requested language (``assert_no_jargon``).
"""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path
from typing import Any

import yaml

from topoli.core.domain import Finding, Lang
from topoli.core.i18n import find_jargon

WEIGHTS_PATH = Path(__file__).resolve().parent / "weights.yaml"


@cache
def load_weights() -> dict[str, Any]:
    with WEIGHTS_PATH.open(encoding="utf-8") as fh:
        data: dict[str, Any] = yaml.safe_load(fh)
    return data


def goal_profile(goal: str | None) -> tuple[str, dict[str, float]]:
    """Name and category→relevance map for a free-text ``--goal``."""
    cfg = load_weights()["goals"]
    text = (goal or "").lower()
    if text:
        words = set(re.findall(r"[a-zà-ÿ]+", text))
        best, best_hits = "balanced", 0
        for name, spec in cfg.items():
            hits = sum(1 for kw in spec.get("keywords", []) if any(w.startswith(kw) for w in words))
            if hits > best_hits:
                best, best_hits = name, hits
        return best, dict(cfg[best]["relevance"])
    return "balanced", dict(cfg["balanced"]["relevance"])


def surprise_of(template_key: str | None) -> float:
    table: dict[str, float] = load_weights()["surprise"]
    key = template_key or ""
    best_len, best = -1, 0.3
    for prefix, value in table.items():
        if key.startswith(prefix) and len(prefix) > best_len:
            best_len, best = len(prefix), float(value)
    return best


def rank_score(finding: Finding, relevance: dict[str, float]) -> float:
    w = load_weights()["weights"]
    sev = float(load_weights()["severity"].get(finding.severity, 0.1))
    goal = float(relevance.get(finding.category, 0.0))
    surprise = surprise_of(finding.template_key)
    penalty = 0.5 if finding.cls == "D" else 0.0
    score = float(w["goal"]) * goal + float(w["severity"]) * sev + float(w["surprise"]) * surprise
    return round(score - penalty, 4)


def rank(findings: list[Finding], goal: str | None = None) -> list[Finding]:
    """All findings, scored and sorted (highest first), with ``rank_score`` set."""
    _, relevance = goal_profile(goal)
    scored = [f.model_copy(update={"rank_score": rank_score(f, relevance)}) for f in findings]
    return sorted(scored, key=lambda f: (-f.rank_score, f.id))


def family(finding: Finding) -> str:
    return finding.id.split(".")[0]


def select_layer0(
    findings: list[Finding],
    lang: Lang,
    *,
    goal: str | None = None,
    limit: int = 5,
    minimum: int = 3,
) -> list[Finding]:
    """The 3–5 findings shown on layer 0, ranked, jargon-free, one per family."""
    ranked = rank(findings, goal)
    chosen: list[Finding] = []
    families: set[str] = set()

    def eligible(f: Finding, allow_d: bool) -> bool:
        if family(f) in families:
            return False
        if f.cls == "D" and not allow_d:
            return False
        text = f"{f.title.get(lang)} {f.consequence.get(lang)}"
        return not find_jargon(text, lang)

    for allow_d in (False, True):
        for f in ranked:
            if len(chosen) >= limit:
                break
            if eligible(f, allow_d):
                chosen.append(f)
                families.add(family(f))
        if len(chosen) >= minimum:
            break
    return chosen[:limit]
