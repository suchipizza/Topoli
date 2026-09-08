"""Exactly one recommended next step for layer 0 (PRD §3.3, WO-07 task 4), chosen by rule:

1. listed heritage → contact the (municipal/cantonal) heritage office about the object;
2. development headroom in Zürich → verify the BZO article with the city planning office;
3. hazard medium/high → request the cantonal hazard-map extract;
4. otherwise → order the ÖREB extract (or, where the cadastre is missing, ask the municipality).

The office and article are concrete; the sentence is written per language in ``i18n``
(``next_step.<rule>``).
"""

from __future__ import annotations

from dataclasses import dataclass

from topoli.core.domain import Finding, Lang, Regulation, Site
from topoli.core.i18n import t


@dataclass(frozen=True)
class NextStep:
    rule: str
    text: str


def choose_next_step(
    findings: list[Finding],
    site: Site,
    lang: Lang,
    *,
    regulations: list[Regulation] | None = None,
    oereb_available: bool = True,
) -> NextStep:
    canton = site.jurisdiction.canton or ""
    municipality = site.jurisdiction.municipality or canton or "—"
    by_key = {f.template_key or "": f for f in findings}

    listed = next(
        (
            f
            for f in findings
            if (f.template_key or "").startswith(
                ("heritage.kgs", "heritage.zh.listed", "heritage.unesco")
            )
        ),
        None,
    )
    if listed is not None:
        office = t(
            "office.heritage_municipal" if canton == "ZH" else "office.heritage_cantonal",
            lang,
            municipality=municipality,
        )
        return NextStep(
            "heritage",
            t("next_step.heritage", lang, name=listed.slots.get("name", "—"), office=office),
        )

    headroom = by_key.get("potential.headroom")
    if headroom is not None and canton == "ZH":
        reg = regulations[0] if regulations else None
        article = "—"
        if reg:
            far = next((r for r in reg.rules if r.key == "floor_area_ratio"), None)
            if far:
                article = far.evidence_spans[0].article
        return NextStep(
            "potential",
            t(
                "next_step.potential_zh",
                lang,
                article=article,
                office=t("office.planning_zurich", lang),
            ),
        )

    hazard = next(
        (f for f in findings if f.category == "hazard" and f.severity in ("medium", "high")), None
    )
    if hazard is not None:
        return NextStep(
            "hazard",
            t(
                "next_step.hazard",
                lang,
                office=t("office.hazard_cantonal", lang, canton=canton or "—"),
            ),
        )

    if oereb_available:
        return NextStep("oereb", t("next_step.oereb", lang, municipality=municipality))
    return NextStep("municipality", t("next_step.municipality", lang, municipality=municipality))
