"""Jargon banned from layer 0 (PRD §3.3), loaded from ``i18n/jargon.json``.

Each entry has an ``id``, the surface forms (``terms``) in whichever language they occur, and a
one-line ``explanation`` per language for layer 1. A term is matched on word boundaries;
forms that contain a digit or are all upper-case (codes such as ``W3``, ``ES III``, ``ÖREB``)
match case-sensitively, everything else case-insensitively.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import cache
from typing import Any

from topoli.core.domain import LANGS, Lang
from topoli.paths import asset_dir


@dataclass(frozen=True)
class JargonEntry:
    id: str
    terms: tuple[str, ...]
    explanation: dict[str, str]
    pattern: re.Pattern[str]

    def explain(self, lang: Lang) -> str:
        return self.explanation[lang]


@dataclass(frozen=True)
class JargonHit:
    entry_id: str
    matched: str
    start: int


def _compile(terms: tuple[str, ...]) -> re.Pattern[str]:
    parts = []
    for term in terms:
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        case_sensitive = any(ch.isdigit() for ch in term) or term.upper() == term
        body = escaped if case_sensitive else f"(?i:{escaped})"
        parts.append(rf"(?<!\w){body}(?!\w)")
    return re.compile("|".join(parts))


@cache
def jargon_entries() -> tuple[JargonEntry, ...]:
    path = asset_dir("i18n") / "jargon.json"
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    entries = []
    for raw in data["entries"]:
        explanation = dict(raw["explanation"])
        missing = [lang for lang in LANGS if lang not in explanation]
        if missing:
            msg = f"jargon entry {raw['id']!r} lacks explanation for {missing}"
            raise ValueError(msg)
        terms = tuple(raw["terms"])
        entries.append(JargonEntry(raw["id"], terms, explanation, _compile(terms)))
    return tuple(entries)


def find_jargon(text: str, lang: Lang) -> list[JargonHit]:
    """All banned terms occurring in ``text``. ``lang`` is accepted for API symmetry;
    the ban list is the union over languages because codes leak across languages."""
    del lang
    hits = []
    for entry in jargon_entries():
        for match in entry.pattern.finditer(text):
            hits.append(JargonHit(entry.id, match.group(0), match.start()))
    return sorted(hits, key=lambda h: h.start)


def assert_no_jargon(text: str, lang: Lang) -> None:
    """Raise ``AssertionError`` listing every banned term found in ``text``."""
    hits = find_jargon(text, lang)
    if hits:
        found = ", ".join(f"{h.matched!r} ({h.entry_id})" for h in hits)
        msg = f"layer-0 text ({lang}) contains banned jargon: {found}\n  text: {text!r}"
        raise AssertionError(msg)
