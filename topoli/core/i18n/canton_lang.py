"""Default output language from the canton (PRD §3.1).

Bilingual/trilingual cantons take their majority language: BE→de, FR→fr, VS→fr, GR→de.
"""

from __future__ import annotations

from topoli.core.domain import Lang

CANTON_LANG: dict[str, Lang] = {
    "AG": "de",
    "AI": "de",
    "AR": "de",
    "BE": "de",
    "BL": "de",
    "BS": "de",
    "FR": "fr",
    "GE": "fr",
    "GL": "de",
    "GR": "de",
    "JU": "fr",
    "LU": "de",
    "NE": "fr",
    "NW": "de",
    "OW": "de",
    "SG": "de",
    "SH": "de",
    "SO": "de",
    "SZ": "de",
    "TG": "de",
    "TI": "it",
    "UR": "de",
    "VD": "fr",
    "VS": "fr",
    "ZG": "de",
    "ZH": "de",
}


def canton_lang(canton: str | None, default: Lang = "en") -> Lang:
    """Language for a canton abbreviation (case-insensitive); ``default`` if unknown/None."""
    if not canton:
        return default
    return CANTON_LANG.get(canton.strip().upper(), default)
