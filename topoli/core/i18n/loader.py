"""Load ``i18n/{fr,de,it,en}.json`` and fill slots.

Files are nested JSON objects; keys are addressed with dots (``"section.7.title"``).
A value equal to ``"__TODO__"`` means "not yet written in this language": ``t()`` falls back to
English and logs a warning, and ``tests/i18n`` fails until every TODO is filled (WO-07).
"""

from __future__ import annotations

import json
import logging
from functools import cache
from typing import Any

from topoli.core.domain import LANGS, Lang
from topoli.paths import asset_dir

log = logging.getLogger("topoli.i18n")

TODO = "__TODO__"


class MissingKeyError(KeyError):
    """Raised when a key exists in no language file."""


@cache
def load(lang: Lang) -> dict[str, str]:
    """Flattened ``{dotted.key: value}`` for one language."""
    path = asset_dir("i18n") / f"{lang}.json"
    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    flat: dict[str, str] = {}
    _flatten(data, "", flat)
    return flat


def _flatten(node: dict[str, Any], prefix: str, out: dict[str, str]) -> None:
    for key, value in node.items():
        if key.startswith("_"):  # "_comment" and friends
            continue
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            _flatten(value, full, out)
        elif isinstance(value, str):
            out[full] = value
        else:
            msg = f"i18n value at {full!r} must be a string or object, got {type(value).__name__}"
            raise TypeError(msg)


def all_keys() -> dict[Lang, set[str]]:
    return {lang: set(load(lang)) for lang in LANGS}


def t(key: str, lang: Lang, **slots: object) -> str:
    """Translate ``key`` into ``lang`` and fill ``{slots}``.

    Slot values are inserted as given; format numbers, areas and dates with
    :mod:`topoli.core.i18n.format` before passing them in.
    """
    strings = load(lang)
    value = strings.get(key)
    if value is None or value == TODO:
        fallback = load("en").get(key)
        if fallback is None:
            raise MissingKeyError(key)
        if lang != "en":
            log.warning("i18n.fallback", extra={"key": key, "lang": lang})
        value = fallback
    try:
        return value.format(**slots)
    except (KeyError, IndexError) as exc:
        msg = f"i18n key {key!r} ({lang}) needs slot {exc}; got {sorted(slots)}"
        raise ValueError(msg) from exc
