"""Layer 0 — the five-finding screen (PRD §3.3), rendered from ``skills/property-audit/prompts/
layer0.<lang>.md`` (Jinja frame) with the findings' per-language sentences.

Numbers in the rendered sentences are rounded to two significant figures (``round_sig_text``);
years (1800–2100), codes glued to letters (``W4``, ``AU6979``) and article numbers are left alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import floor, log10
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from topoli.core.domain import Finding, Lang, Regulation, Site
from topoli.core.i18n import t
from topoli.core.scoring.next_step import NextStep, choose_next_step
from topoli.core.scoring.rank import select_layer0
from topoli.paths import asset_dir

_NUMBER = re.compile(r"(?<![\w.,/-])(\d{3,})(?![\w.-]|\s?%?\s?\d)")


def round_sig(value: float, digits: int = 2) -> float:
    if value == 0:
        return 0.0
    magnitude = floor(log10(abs(value)))
    factor = 10.0 ** (digits - 1 - magnitude)
    return float(round(value * factor) / factor)


def round_sig_text(text: str) -> str:
    """Round integers with ≥ 3 digits to two significant figures, leaving years and codes alone."""

    def repl(m: re.Match[str]) -> str:
        raw = m.group(1)
        value = int(raw)
        if 1800 <= value <= 2100:
            return raw
        rounded = int(round_sig(value))
        return str(rounded)

    return _NUMBER.sub(repl, text)


@dataclass
class Layer0:
    lang: Lang
    header: str
    findings: list[Finding]
    lines: list[tuple[str, str, str]]  # (icon, title, consequence) after rounding
    confidence: str
    counts: dict[str, int]
    next_step: NextStep
    report_path: str
    card_path: str
    text: str = ""
    goal_profile: str = "balanced"
    slots: dict[str, str] = field(default_factory=dict)


def confidence_line(findings: list[Finding], lang: Lang) -> tuple[str, dict[str, int]]:
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for f in findings:
        counts[f.cls] += 1
    parts = {}
    for cls, key in (("A", "official"), ("B", "derived"), ("C", "estimate"), ("D", "professional")):
        n = counts[cls]
        parts[cls] = (
            t(f"confidence.{key}_one", lang) if n == 1 else t(f"confidence.{key}", lang, n=n)
        )
    return t(
        "confidence.line", lang, a=parts["A"], b=parts["B"], c=parts["C"], d=parts["D"]
    ), counts


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(asset_dir("skills") / "property-audit" / "prompts")),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_layer0(
    site: Site,
    findings: list[Finding],
    lang: Lang,
    *,
    goal: str | None = None,
    regulations: list[Regulation] | None = None,
    oereb_available: bool = True,
    report_path: str = "./reports/<id>/index.html",
    card_path: str = "./reports/<id>/card.png",
) -> Layer0:
    shown = select_layer0(findings, lang, goal=goal)
    lines = [
        (f.icon or "•", round_sig_text(f.title.get(lang)), round_sig_text(f.consequence.get(lang)))
        for f in shown
    ]
    confidence, counts = confidence_line(shown, lang)
    step = choose_next_step(
        shown, site, lang, regulations=regulations, oereb_available=oereb_available
    )
    header = t(
        "layer0.header",
        lang,
        address=site.address,
        municipality=site.jurisdiction.municipality or "",
    )
    template = _env().get_template(f"layer0.{lang}.md")
    text = template.render(
        header=header,
        lines=lines,
        confidence=confidence,
        next_step=t("next_step.frame", lang, action=step.text),
        open_report=t("layer0.open_report", lang, path=report_path),
        share=t("layer0.share", lang, path=card_path),
    )
    return Layer0(
        lang=lang,
        header=header,
        findings=shown,
        lines=lines,
        confidence=confidence,
        counts=counts,
        next_step=step,
        report_path=report_path,
        card_path=card_path,
        text=text,
    )


def template_path(lang: Lang) -> Path:
    return asset_dir("skills") / "property-audit" / "prompts" / f"layer0.{lang}.md"
