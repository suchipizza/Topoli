"""Share artefacts (WO-09): both card sizes + summary.txt per language, no overflow, clean URLs."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

from topoli.core.adapters import get_client
from topoli.core.domain import LANGS, Lang
from topoli.core.pipeline import build_result
from topoli.core.reporting import card
from topoli.core.reporting.card import LANDSCAPE, SQUARE, render_cards
from topoli.core.reporting.layer0 import render_layer0
from topoli.core.reporting.share import ALLOWED_SRC, run_link
from topoli.core.reporting.summary import summary_text, write_summary

ADAPTERS = [
    "ch/federal/hazards",
    "ch/federal/noise",
    "ch/federal/contamination",
    "ch/federal/oereb",
    "ch/federal/solar",
    "ch/federal/heritage",
    "ch/federal/terrain",
    "ch/zh/zoning",
    "ch/zh/regulation",
    "ch/zh/heritage",
    "ch/zh/construction_events",
]


@pytest.fixture(scope="module")
def result_de(replay_module: Callable[[str, str], int]):  # type: ignore[no-untyped-def]
    for adapter_id in ADAPTERS:
        with contextlib.suppress(AssertionError):
            replay_module(adapter_id, "zurich-badenerstrasse-171")
    get_client().reset()
    result, _ = build_result("Badenerstrasse 171, 8003 Zürich", lang="de")
    return result


@pytest.mark.parametrize("lang", LANGS)
def test_cards_and_summary_in_every_language(result_de, lang: Lang, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    layer0 = render_layer0(
        result_de.site, result_de.findings, lang, regulations=result_de.regulations
    )
    paths = render_cards(layer0, tmp_path / lang)
    assert [p.name for p in paths] == ["card.png", "card-square.png"]
    with Image.open(paths[0]) as im:
        assert im.size == (LANDSCAPE.width, LANDSCAPE.height)
    with Image.open(paths[1]) as im:
        assert im.size == (SQUARE.width, SQUARE.height)
    assert all(p.stat().st_size < 400_000 for p in paths)
    summary = write_summary(layer0, tmp_path / lang)
    text = summary.read_text(encoding="utf-8")
    assert layer0.text.strip() in text
    assert run_link("summary", lang) in text and "github.com/suchipizza/Topoli" in text
    assert "Badenerstrasse" not in run_link("summary", lang)


def test_longest_german_strings_do_not_overflow(  # type: ignore[no-untyped-def]
    result_de, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layer0 = render_layer0(
        result_de.site, result_de.findings, "de", regulations=result_de.regulations
    )
    long_title = (
        "Sie könnten hier wahrscheinlich mehr bauen: die bestehenden Gebäude nutzen etwa 45% "
        "dessen, was die Zone zuzulassen scheint, und zwar ausführlich formuliert "
    ) * 2
    layer0.lines = [(icon, long_title, cons) for icon, _t, cons in layer0.lines]
    calls: list[tuple[int, int]] = []
    original = card._fit

    def spy(  # type: ignore[no-untyped-def]
        text, bold, max_width, max_lines, start, minimum
    ):
        font, lines = original(text, bold, max_width, max_lines, start, minimum)
        calls.append((len(lines), max_lines))
        assert all(font.getlength(ln) <= max_width + 1 for ln in lines), (font.size, lines)
        return font, lines

    monkeypatch.setattr(card, "_fit", spy)
    render_cards(layer0, tmp_path)
    assert calls and all(n <= m for n, m in calls)


def test_run_links_never_contain_addresses_or_ids() -> None:
    for src in ALLOWED_SRC:
        for lang in LANGS:
            url = run_link(src, lang)
            assert url == f"https://topoli.ch/run?src={src}&lang={lang}"


def test_summary_is_layer0_plus_links(result_de) -> None:  # type: ignore[no-untyped-def]
    layer0 = render_layer0(
        result_de.site, result_de.findings, "fr", regulations=result_de.regulations
    )
    text = summary_text(layer0)
    assert text.startswith("CHECK IMMOBILIER")
    assert text.rstrip().endswith("github.com/suchipizza/Topoli")
