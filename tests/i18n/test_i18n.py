from __future__ import annotations

import string
from datetime import date, datetime

import pytest

from topoli.core.domain import LANGS
from topoli.core.i18n import (
    CANTON_LANG,
    TODO,
    MissingKeyError,
    all_keys,
    canton_lang,
    fmt_area,
    fmt_date,
    fmt_number,
    fmt_pct,
    load,
    t,
)
from topoli.core.i18n.format import NBSP, NNBSP


def test_all_four_files_share_identical_key_sets() -> None:
    keys = all_keys()
    reference = keys["en"]
    for lang in LANGS:
        missing = reference - keys[lang]
        extra = keys[lang] - reference
        assert not missing, f"{lang}.json is missing keys: {sorted(missing)}"
        assert not extra, f"{lang}.json has extra keys: {sorted(extra)}"


def test_english_has_no_todo() -> None:
    todo = [k for k, v in load("en").items() if v == TODO]
    assert not todo


@pytest.mark.xfail(
    strict=True, reason="FR/DE/IT strings are written in WO-07; remove this mark then"
)
def test_no_todo_values_in_any_language() -> None:
    for lang in LANGS:
        todo = sorted(k for k, v in load(lang).items() if v == TODO)
        assert not todo, f"{lang}.json still has __TODO__ at: {todo[:10]}…"


def test_slots_are_declared_identically_across_languages() -> None:
    fmt = string.Formatter()
    en = load("en")
    for lang in LANGS:
        for key, value in load(lang).items():
            if value == TODO:
                continue
            slots = {name for _, name, _, _ in fmt.parse(value) if name}
            en_slots = {name for _, name, _, _ in fmt.parse(en[key]) if name}
            assert slots == en_slots, f"{lang}:{key} slots {slots} differ from en {en_slots}"


def test_t_fills_slots_and_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    assert t("layer0.header", "en", address="Badenerstrasse 123", municipality="Zürich").startswith(
        "PROPERTY CHECK — Badenerstrasse 123, Zürich"
    )
    assert t("section.7", "en") == "Public-law restrictions"
    # fallback to EN while a language is __TODO__ or when the key is filled — either way a string
    assert t("section.7", "fr")
    with pytest.raises(MissingKeyError):
        t("does.not.exist", "de")
    with pytest.raises(ValueError, match="needs slot"):
        t("layer0.header", "en", address="x")


@pytest.mark.parametrize(
    ("value", "lang", "expected"),
    [
        (1234, "de", "1'234"),
        (1234, "fr", f"1{NNBSP}234"),
        (1234, "it", f"1{NNBSP}234"),
        (1234, "en", "1,234"),
        (1234567.891, "de", "1'234'567.9"),
        (1234567.891, "fr", f"1{NNBSP}234{NNBSP}567,9"),
        (-42.5, "en", "-42.5"),
        (999, "de", "999"),
    ],
)
def test_fmt_number(value: float, lang: str, expected: str) -> None:
    decimals = 1 if isinstance(value, float) else 0
    assert fmt_number(value, lang, decimals) == expected  # type: ignore[arg-type]


def test_fmt_area_and_pct() -> None:
    assert fmt_area(1234, "de") == f"1'234{NBSP}m²"
    assert fmt_area(1234, "fr") == f"1{NNBSP}234{NBSP}m²"
    assert fmt_area(1234, "en") == f"1,234{NBSP}m²"
    assert fmt_pct(0.453, "en") == "45%"
    assert fmt_pct(0.453, "de") == f"45{NBSP}%"
    assert NBSP == "\u00a0" and NNBSP == "\u202f"


def test_fmt_date() -> None:
    d = date(2026, 9, 8)
    assert fmt_date(d, "de") == "08.09.2026"
    assert fmt_date(d, "fr") == "08.09.2026"
    assert fmt_date(d, "it") == "08.09.2026"
    assert fmt_date(d, "en") == "8 September 2026"
    assert fmt_date(datetime(2026, 9, 8, 23, 59), "en") == "8 September 2026"


@pytest.mark.parametrize(
    ("canton", "expected"),
    [
        ("ZH", "de"),
        ("GE", "fr"),
        ("VD", "fr"),
        ("NE", "fr"),
        ("JU", "fr"),
        ("TI", "it"),
        ("BE", "de"),
        ("FR", "fr"),
        ("VS", "fr"),
        ("GR", "de"),
        ("zh", "de"),
        (None, "en"),
        ("XX", "en"),
    ],
)
def test_canton_lang(canton: str | None, expected: str) -> None:
    assert canton_lang(canton) == expected


def test_canton_lang_covers_all_26_cantons() -> None:
    assert len(CANTON_LANG) == 26
