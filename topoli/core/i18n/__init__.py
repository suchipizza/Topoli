"""Internationalisation: string loader, slot filling, locale formatting, canton → language."""

from topoli.core.i18n.canton_lang import CANTON_LANG, canton_lang
from topoli.core.i18n.format import fmt_area, fmt_date, fmt_number, fmt_pct
from topoli.core.i18n.jargon import (
    JargonHit,
    assert_no_jargon,
    find_jargon,
    jargon_entries,
)
from topoli.core.i18n.loader import TODO, MissingKeyError, all_keys, load, t

__all__ = [
    "CANTON_LANG",
    "TODO",
    "JargonHit",
    "MissingKeyError",
    "all_keys",
    "assert_no_jargon",
    "canton_lang",
    "find_jargon",
    "fmt_area",
    "fmt_date",
    "fmt_number",
    "fmt_pct",
    "jargon_entries",
    "load",
    "t",
]
