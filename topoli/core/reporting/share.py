"""Share links (PRD §7, website PRD §6). The site is a separate repository; only its public URL
and the ``/run`` counter contract are known here. Links carry ``src`` and ``lang`` only — never an
address, a parcel id or anything personal (asserted by ``tests/core/test_share.py``).

``TOPOLI_SITE_URL`` is a placeholder until the brand domain is cleared (spec §11).
"""

from __future__ import annotations

from urllib.parse import urlencode

from topoli.core.domain import Lang

TOPOLI_SITE_URL = "https://topoli.ch"
TOPOLI_REPO_URL = "https://github.com/suchipizza/Topoli"
TOPOLI_WAITLIST_URL = f"{TOPOLI_SITE_URL}/api/waitlist"
ALLOWED_SRC = ("card", "report", "readme", "site", "summary")


def run_link(src: str, lang: Lang) -> str:
    """``https://topoli.ch/run?src=report&lang=fr`` → the site's privacy-safe counter + redirect."""
    if src not in ALLOWED_SRC:
        msg = f"src must be one of {ALLOWED_SRC}, got {src!r}"
        raise ValueError(msg)
    return f"{TOPOLI_SITE_URL}/run?{urlencode({'src': src, 'lang': lang})}"


def waitlist_link(src: str, lang: Lang, votes: list[str] | None = None) -> str:
    """No-JS fallback for the report's waitlist block: prefilled site form."""
    params: dict[str, str] = {"src": src, "lang": lang}
    if votes:
        params["vote"] = ",".join(votes)
    return f"{TOPOLI_SITE_URL}/{lang}#waitlist?{urlencode(params)}"


def star_link() -> str:
    return TOPOLI_REPO_URL
