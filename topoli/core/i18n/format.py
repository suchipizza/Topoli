"""Locale formatting (PRD §8): ``1'234 m²`` de-CH · ``1 234 m²`` fr-CH/it-CH · ``1,234 m²`` en."""

from __future__ import annotations

from datetime import date, datetime

from topoli.core.domain import Lang

NBSP = " "  # no-break space between number and unit
NNBSP = " "  # narrow no-break space as fr/it thousands separator

_THOUSANDS: dict[Lang, str] = {"de": "'", "fr": NNBSP, "it": NNBSP, "en": ","}
_DECIMAL: dict[Lang, str] = {"de": ".", "fr": ",", "it": ",", "en": "."}

_MONTHS_EN = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def fmt_number(value: float, lang: Lang, decimals: int = 0) -> str:
    """``fmt_number(1234.5, "de", 1) == "1'234.5"``; negative values keep their sign."""
    sign = "-" if value < 0 else ""
    text = f"{abs(value):,.{decimals}f}"  # en-US grouping, then swap separators
    int_part, _, frac_part = text.partition(".")
    int_part = int_part.replace(",", _THOUSANDS[lang])
    if decimals > 0:
        return f"{sign}{int_part}{_DECIMAL[lang]}{frac_part}"
    return f"{sign}{int_part}"


def fmt_area(m2: float, lang: Lang, decimals: int = 0) -> str:
    return f"{fmt_number(m2, lang, decimals)}{NBSP}m²"


def fmt_pct(fraction: float, lang: Lang, decimals: int = 0) -> str:
    """``fmt_pct(0.453, "fr") == "45 %"`` (fr/de/it put a space before %; en does not)."""
    number = fmt_number(fraction * 100, lang, decimals)
    return f"{number}{NBSP}%" if lang != "en" else f"{number}%"


def fmt_date(value: date | datetime, lang: Lang) -> str:
    """``08.09.2026`` for fr/de/it (Swiss convention), ``8 September 2026`` for en."""
    d = value.date() if isinstance(value, datetime) else value
    if lang == "en":
        return f"{d.day} {_MONTHS_EN[d.month - 1]} {d.year}"
    return f"{d.day:02d}.{d.month:02d}.{d.year}"
