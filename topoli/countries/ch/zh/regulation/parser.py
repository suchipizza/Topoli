"""Rule-specific extractors for the BZO 2016 of the City of Zürich (deterministic, no LLM).

Each extractor knows one article's table layout and returns ``Rule`` objects whose evidence span
is the verbatim table row (article number, text, character offsets in the extracted PDF text).
Anything the extractor cannot read unambiguously stays **absent** (listed in ``unresolved``) and
becomes class D downstream — never a guess.

Covered (``PARSER_VERSION``):

* Art. 13 Abs. 1 — Wohnzonen W2bI…W6: Vollgeschosse, anrechenbares Untergeschoss/Dachgeschoss,
  Gebäudehöhe, Grundgrenzabstand, Ausnützungsziffer. (Gebäudelänge and Überbauungsziffer rows
  are column-ambiguous in the text layer → unresolved.)
* Art. 14 Abs. 1 — Mehrlängenzuschlag: maximum Grenzabstand per Wohnzone.
* Art. 18 Abs. 1 — Zentrumszonen Z5…Z7.
* Art. 19 Abs. 1 — Industrie- und Gewerbezonen IG I…III (AZ for Handel/Dienstleistung,
  Baumassenziffer, Freiflächenziffer).
* Art. 24g/24l/24o Abs. 2/1/2 — Quartiererhaltungszonen QI/QII/QIII by number of full floors
  (Gebäudehöhe, Firsthöhe, Grenzabstand). Codes like ``QI/5a`` map to family ``QI`` + floors 5.

Kernzonen (``K``), Zonen für öffentliche Bauten, Freihalte-/Erholungszonen carry no numeric
table in the BZO (plan-specific rules) → ``unresolved`` for every rule key.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from topoli.core.domain import EvidenceSpan, Rule

PARSER_VERSION = "bzo2016-parser/0.1.0"
DOCUMENT = "BZO 2016 (AS 700.100)"

RULE_KEYS = (
    "max_full_floors",
    "max_attic_floors",
    "max_basement_floors",
    "max_building_height_m",
    "min_boundary_setback_m",
    "max_boundary_setback_with_length_m",
    "floor_area_ratio",  # Ausnützungsziffer, in % of parcel area
    "floor_area_ratio_commercial",  # IG zones: AZ for Handel/Dienstleistung only
    "building_mass_ratio",  # Baumassenziffer m³/m²
    "min_open_space_ratio",  # Freiflächenziffer %
    "max_ridge_height_m",
)


@dataclass
class ZoneRules:
    zone: str
    rules: list[Rule] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)


@dataclass
class ParsedBzo:
    zones: dict[str, ZoneRules]
    parser_version: str = PARSER_VERSION

    def for_code(self, zone_code: str) -> ZoneRules | None:
        """Look up a zone code as published by the canton (``W4``, ``QI/5a``, ``Z6``, ``IG II``)."""
        code = zone_code.strip()
        if code in self.zones:
            return self.zones[code]
        m = re.match(r"^(QI{1,3})/(\d)[a-z]?$", code)
        if m:
            return self.zones.get(f"{m.group(1)}/{m.group(2)}")
        return self.zones.get(code.replace(" ", ""))


def _norm(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s.replace("­", "").replace(" -\n", "").replace("-\n", "")).strip()


def _article_block(text: str, article: str, next_article: str) -> tuple[str, int] | None:
    """Text of ``Art. <article>`` up to ``Art. <next_article>`` and its start offset."""
    start = re.search(rf"\n\s*Ar\s?t\.\s*{re.escape(article)}\b", text)
    if not start:
        return None
    end = re.search(rf"\n\s*Ar\s?t\.\s*{re.escape(next_article)}\b", text[start.end() :])
    stop = start.end() + end.start() if end else len(text)
    return text[start.start() : stop], start.start()


def _row(block: str, label_pattern: str, expected: int, unit: str) -> tuple[str, int] | None:
    """The table row starting with ``label_pattern`` → (row text, offset).

    Rows are one line; a label may wrap so that the numbers sit on the *next* line. Try the
    label's own line first and extend by one line only if it does not carry ``expected`` values.
    """
    m = re.search(label_pattern + r"[^\n]*", block)
    if not m:
        return None
    line = m.group(0)
    label = re.match(label_pattern, line)
    after = line[label.end() :] if label else line
    if len(_numbers(after, unit)) >= expected:
        return line, m.start()
    rest = block[m.end() : m.end() + 200]
    nxt = rest.split("\n", 2)
    extended = line + "\n" + (nxt[1] if len(nxt) > 1 else "")
    return extended, m.start()


_NUM = r"(\d+(?:[.,]\d+)?)"


def _numbers(row: str, unit: str) -> list[float]:
    """All numbers followed by ``unit`` (``%``, ``m``, ``m3/m2``) in a row, in order."""
    pattern = rf"{_NUM}\s*{re.escape(unit)}(?![\w/])" if unit else rf"(?<![\d.,]){_NUM}(?![\d.,%])"
    return [float(v.replace(",", ".")) for v in re.findall(pattern, row)]


def _after_label(row: str, label_pattern: str) -> str:
    m = re.match(label_pattern, row)
    return row[m.end() :] if m else row


def _rule(  # noqa: PLR0917
    key: str, value: float | int, unit: str | None, article: str, row: str, offset: int
) -> Rule:
    return Rule(
        key=key,
        value=value,
        unit=unit,
        definition=None,
        evidence_spans=[
            EvidenceSpan(
                document=DOCUMENT,
                article=f"Art. {article}",
                text=_norm(row),
                char_start=offset,
                char_end=offset + len(row),
                url="https://oerebdocs.zh.ch/getDoc?docid=6",
            )
        ],
        parser_version=PARSER_VERSION,
    )


def _table(
    text: str,
    article: str,
    next_article: str,
    zones: list[str],
    rows: Sequence[tuple[str, str, str, str | None]],
) -> dict[str, ZoneRules]:
    """Generic column table: ``rows`` = (rule_key, label regex, unit, unit_label)."""
    out = {z: ZoneRules(z) for z in zones}
    found = _article_block(text, article, next_article)
    if found is None:
        for z in out.values():
            z.unresolved.extend(k for k, *_ in rows)
        return out
    block, base = found
    for key, label, unit, unit_label in rows:
        row = _row(block, label, len(zones), unit)
        values = _numbers(_after_label(row[0], label), unit) if row else []
        if row is None or len(values) != len(zones):
            for z in out.values():
                z.unresolved.append(key)
            continue
        for zone, value in zip(zones, values, strict=True):
            v: float | int = int(value) if unit == "" else value
            out[zone].rules.append(_rule(key, v, unit_label, article, row[0], base + row[1]))
    return out


def parse_residential(text: str) -> dict[str, ZoneRules]:
    zones = ["W2bI", "W2bII", "W2bIII", "W2", "W3", "W4b", "W4", "W5", "W6"]
    rows = [
        ("max_full_floors", r"Vollgeschosse max\.", "", "floors"),
        ("max_basement_floors", r"anrechenbares\s*\n?\s*Untergeschoss max\.", "", "floors"),
        ("max_attic_floors", r"anrechenbares\s*\n?\s*Dachgeschoss max\.", "", "floors"),
        ("max_building_height_m", r"Gebäudehöhe max\.", "m", "m"),
        ("min_boundary_setback_m", r"Grundgrenzabstand\s*\n?\s*min\.", "m", "m"),
        ("floor_area_ratio", r"Ausnützungsziffer\s*\n?\s*max\.", "%", "%"),
    ]
    out = _table(text, "13", "14", zones, rows)
    # Art. 14: cap of the boundary setback with the length surcharge
    found = _article_block(text, "14", "15")
    if found:
        block, base = found
        row = _row(block, r"W2bI W2bII W2bIII W2 W3 W4b W4 W5 W6", len(zones), "m")
        values = (
            _numbers(_after_label(row[0], r"W2bI W2bII W2bIII W2 W3 W4b W4 W5 W6"), "m")
            if row
            else []
        )
        if row and len(values) == len(zones):
            for zone, value in zip(zones, values, strict=True):
                out[zone].rules.append(
                    _rule(
                        "max_boundary_setback_with_length_m",
                        value,
                        "m",
                        "14",
                        row[0],
                        base + row[1],
                    )
                )
    for z in out.values():
        if not any(r.key == "max_boundary_setback_with_length_m" for r in z.rules):
            z.unresolved.append("max_boundary_setback_with_length_m")
    # basement "0*" for W4/W5/W6 is footnoted (Art. 8 Abs. 7); parses as 0, the span keeps the *
    return out


def parse_centre(text: str) -> dict[str, ZoneRules]:
    zones = ["Z5", "Z6", "Z7"]
    rows = [
        ("max_full_floors", r"Vollgeschosse max\.", "", "floors"),
        ("max_basement_floors", r"anrechenbares Untergeschoss max\.", "", "floors"),
        ("max_attic_floors", r"anrechenbares Dachgeschoss max\.", "", "floors"),
        ("max_building_height_m", r"Gebäudehöhe max\.", "m", "m"),
        ("min_boundary_setback_m", r"Grundgrenzabstand min\.", "m", "m"),
        ("floor_area_ratio", r"Ausnützungsziffer max\.", "%", "%"),
    ]
    return _table(text, "18", "18a", zones, rows)


def parse_industrial(text: str) -> dict[str, ZoneRules]:
    zones = ["IG I", "IG II", "IG III"]
    rows = [
        ("max_full_floors", r"Vollgeschosse max\.", "", "floors"),
        ("max_attic_floors", r"anrechenbares Dachgeschoss", "", "floors"),
        ("max_basement_floors", r"anrechenbares Untergeschoss max\.", "", "floors"),
        ("max_building_height_m", r"Gebäudehöhe max\.", "m", "m"),
        ("min_boundary_setback_m", r"Grundgrenzabstand min\.", "m", "m"),
        (
            "floor_area_ratio_commercial",
            r"Ausnützungsziffer für Handels- und\s*\n?\s*Dienstleistungsnutzung max\.",
            "%",
            "% (Handel/Dienstleistung)",
        ),
        ("building_mass_ratio", r"Baumassenziffer max\.", "m3/m2", "m³/m²"),
        ("min_open_space_ratio", r"Freiflächenziffer min\.", "%", "%"),
    ]
    return _table(text, "19", "19a", zones, rows)


def parse_quarter_preservation(text: str) -> dict[str, ZoneRules]:
    out: dict[str, ZoneRules] = {}
    specs = [
        ("QI", "24g", "24h", [3, 4, 5, 6, 7]),
        ("QII", "24l", "24m", [3, 4]),
        ("QIII", "24o", "24p", [3, 4, 5]),
    ]
    for family, article, nxt, floors in specs:
        zones = [f"{family}/{n}" for n in floors]
        rows = [
            ("max_full_floors", r"Vollgeschosse max\.", "", "floors"),
            ("max_basement_floors", r"anrechenbares? Untergeschosse? max\.", "", "floors"),
            ("max_attic_floors", r"anrechenbares? Dachgeschosse?(?: max\.)?", "", "floors"),
            ("max_building_height_m", r"Gebäudehöhe max\.", "m", "m"),
            ("max_ridge_height_m", r"Firsthöhe max\.", "m", "m"),
            ("min_boundary_setback_m", r"(?:seitlicher )?Grenzabstand min\.", "m", "m"),
        ]
        out.update(_table(text, article, nxt, zones, rows))
    return out


def parse_bzo(text: str) -> ParsedBzo:
    zones: dict[str, ZoneRules] = {}
    zones.update(parse_residential(text))
    zones.update(parse_centre(text))
    zones.update(parse_industrial(text))
    zones.update(parse_quarter_preservation(text))
    for code in ("K", "Oe", "F", "E", "L"):
        zones[code] = ZoneRules(code, unresolved=list(RULE_KEYS))
    return ParsedBzo(zones=zones)
