"""``./reports/<municipality>-<parcel>/index.html`` — self-contained, four-language, printable.

Everything is inlined: tokens + report CSS, the script, the four i18n dictionaries (subset needed
by the page), the findings in all four languages, the layer-1 structure and the map frame.
The language switcher swaps copy client-side; no request leaves the page except swisstopo map
tiles at view time and the waitlist POST when the visitor submits it.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from topoli import __version__
from topoli.core.domain import LANGS, Finding, Lang
from topoli.core.evidence import AuditResult
from topoli.core.i18n import fmt_date, load, t
from topoli.core.reporting.assemble import Layer1, assemble
from topoli.core.reporting.layer0 import Layer0, render_layer0
from topoli.core.reporting.share import (
    TOPOLI_REPO_URL,
    TOPOLI_SITE_URL,
    TOPOLI_WAITLIST_URL,
    run_link,
    waitlist_link,
)
from topoli.core.reporting.static_map import MapFrame, frame_for, render_static_png
from topoli.paths import asset_dir

VOTES = ("monitor", "scan", "leads", "portfolio", "reports", "api", "cad", "other")
I18N_PREFIXES = (
    "layer0.",
    "report.",
    "section.",
    "class.",
    "coverage.",
    "layer1.",
    "trust.",
    "share.",
    "waitlist.",
    "event_type.",
    "next_step.frame",
    "confidence.",
)


def _env(lang: Lang) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(asset_dir("ui") / "local-report")),
        undefined=StrictUndefined,
        autoescape=True,
    )

    def tr(key: str, **slots: Any) -> str:
        return t(key, lang, **slots)

    def l10n(attr: Markup | str) -> str:
        """Current-language value of a ``_attr_json`` payload."""
        raw = (
            str(attr)
            .replace("&#39;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return str(obj.get(lang) or obj.get("en") or "")
        return str(obj)

    env.globals["tr"] = tr
    env.globals["l10n"] = l10n
    return env


def _i18n_subset() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for lang in LANGS:
        flat = load(lang)
        out[lang] = {k: v for k, v in flat.items() if k.startswith(I18N_PREFIXES)}
    return out


def _attr_json(obj: Any) -> Markup:
    """JSON for single-quoted HTML attributes: escape & < > and the quote ourselves."""
    text = json.dumps(obj, ensure_ascii=False)
    text = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;")
    )
    return Markup(text)


def _short(url: str | None, n: int = 60) -> str:
    if not url:
        return "—"
    return url if len(url) <= n else url[: n - 1] + "…"


def _finding_view(f: Finding, lang: Lang) -> dict[str, Any]:
    return {
        "dom_id": f.id.replace(".", "-").replace("/", "-"),
        "icon": f.icon or "•",
        "cls": f.cls,
        "severity": f.severity,
        "title": _attr_json(f.title.model_dump()),
        "consequence": _attr_json(f.consequence.model_dump()),
        "caveat": _attr_json(f.caveat.model_dump()),
        "dataset": f.source.dataset,
        "authority": f.source.authority,
        "retrieved_at": fmt_date(f.source.retrieved_at, lang) if f.source.retrieved_at else "—",
        "url": f.source.url,
        "url_short": _short(f.source.url),
        "derivation": f.derivation,
        "spans": [
            {"article": s.article, "text": s.text[:160], "url": s.url} for s in f.evidence_spans[:6]
        ],
    }


def _section_view(layer1: Layer1) -> list[dict[str, Any]]:
    out = []
    for s in layer1.sections:
        out.append(
            {
                "number": s.number,
                "available": s.available,
                "facts": s.facts,
                "text": [_attr_json({lang: line for lang in LANGS}) for line in s.text],
                "findings": [_finding_view(f, layer1.lang) for f in s.findings],
                "coverage": [
                    {"adapter_id": c.adapter_id, "status": c.status, "detail": c.detail}
                    for c in s.coverage
                ],
            }
        )
    return out


def _map(
    result: AuditResult, out_dir: Path, *, fetch_tiles: bool
) -> tuple[MapFrame | None, str | None]:
    parcel = result.parcels[0] if result.parcels else None
    if parcel is None or not parcel.geometry_lv95:
        return None, None
    buildings = [
        (float(b.geometry_lv95["coordinates"][0]), float(b.geometry_lv95["coordinates"][1]))
        for b in result.buildings
        if b.geometry_lv95 and b.geometry_lv95.get("type") == "Point"
    ]
    events = [(e.location.east, e.location.north, e.type) for e in result.events if e.location]
    frame = frame_for(parcel.geometry_lv95, buildings, events)
    fallback = None
    if fetch_tiles:
        img = render_static_png(frame, out_dir / "map.jpg")
        if img is not None:
            fallback = "map.jpg"
    elif (out_dir / "map.jpg").is_file():
        fallback = "map.jpg"
    return frame, fallback


def render_html(
    result: AuditResult,
    out_dir: Path,
    *,
    lang: Lang | None = None,
    goal: str | None = None,
    fetch_tiles: bool = True,
    summary_text: str | None = None,
    card_png: str | None = None,
) -> tuple[Path, Layer0]:
    lang = lang or result.lang
    oereb = result.coverage_for("ch/federal/oereb")
    layer0 = render_layer0(
        result.site,
        result.findings,
        lang,
        goal=goal or result.goal,
        regulations=result.regulations,
        oereb_available=bool(oereb and oereb.status == "ok"),
        report_path="./index.html",
        card_path="./card.png",
    )
    layer1 = assemble(result, lang, layer0.findings)
    frame, fallback = _map(result, out_dir, fetch_tiles=fetch_tiles)
    site = result.site
    localized_confidence = {}
    localized_next = {}
    for code in LANGS:
        l0 = render_layer0(
            site,
            result.findings,
            code,
            goal=goal or result.goal,
            regulations=result.regulations,
            oereb_available=bool(oereb and oereb.status == "ok"),
        )
        localized_confidence[code] = l0.confidence
        localized_next[code] = l0.next_step.text

    ui = asset_dir("ui") / "local-report"
    data = {
        "lang": lang,
        "version": __version__,
        "i18n": _i18n_subset(),
        "map": {"tiles": frame.tiles} if frame else None,
        "waitlist_url": TOPOLI_WAITLIST_URL,
        "hit_url": f"{TOPOLI_SITE_URL}/api/hit?e=star",
        "site_id": site.id,
    }
    context: dict[str, Any] = {
        "lang": lang,
        "version": __version__,
        "languages": [(code, load(code).get("lang.name", code)) for code in LANGS],
        "title": f"Topoli · {site.address}",
        "description": layer0.lines[0][1] if layer0.lines else site.address,
        "tokens_css": Markup((ui / "tokens.css").read_text(encoding="utf-8")),
        "report_css": Markup((ui / "report.css").read_text(encoding="utf-8")),
        "report_js": Markup((ui / "report.js").read_text(encoding="utf-8")),
        "repo_url": TOPOLI_REPO_URL,
        "contribute_url": f"{TOPOLI_REPO_URL}/labels/good%20first%20canton",
        "header_slots": _attr_json(
            {"address": site.address, "municipality": site.jurisdiction.municipality or ""}
        ),
        "header_text": layer0.header,
        "generated_slots": _attr_json(
            {"date": fmt_date(result.generated_at, lang), "version": __version__}
        ),
        "generated_text": t(
            "report.generated", lang, date=fmt_date(result.generated_at, lang), version=__version__
        ),
        "cards": [_finding_view(f, lang) for f in layer0.findings],
        "confidence": _attr_json(localized_confidence),
        "next_step": _attr_json(localized_next),
        "map": None
        if frame is None
        else {
            **asdict(frame),
            "fallback": fallback,
            "alt": t("report.map_alt", lang, address=site.address),
        },
        "sections": _section_view(layer1),
        "timeline": [
            {
                "date": e.publication_date.isoformat(),
                "distance": f"{e.distance_m:.0f} m" if e.distance_m is not None else "",
                "type": e.type,
                "description": e.description,
                "url": e.sources[0].url if e.sources else None,
            }
            for e in result.events
        ],
        "sources": [{**asdict(r), "url_short": _short(r.url)} for r in layer1.sources],
        "coverage": [
            {"adapter_id": c.adapter_id, "status": c.status, "detail": c.detail}
            for c in result.coverage
        ],
        "card_png": card_png,
        "run_url": run_link("report", lang),
        "run_url_template": f"{TOPOLI_SITE_URL}/run?src=report&lang={{lang}}",
        "waitlist_fallback": waitlist_link("report", lang),
        "waitlist_fallback_template": (
            f"{TOPOLI_SITE_URL}/{{lang}}#waitlist?src=report&lang={{lang}}"
        ),
        "votes": VOTES,
        "summary_text": summary_text or layer0.text,
        "data_json": Markup(json.dumps(data, ensure_ascii=False).replace("</", "<\\/")),
    }
    page = _env(lang).get_template("template.html").render(**context)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "index.html"
    path.write_text(page, encoding="utf-8")
    return path, layer0


def normalize_for_golden(page: str) -> str:
    """Strip timestamps/versions so example reports can be byte-compared."""
    page = re.sub(r"\d{1,2}[./ ]\w+[./ ]\d{4}", "DATE", page)
    page = re.sub(r"\d{4}-\d{2}-\d{2}T[0-9:.+Z]+", "TIMESTAMP", page)
    page = page.replace(html.escape(__version__), "VERSION").replace(__version__, "VERSION")
    return page
