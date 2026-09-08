# 002 — Domain model: deviations from spec §8 / PRD §5

**Status:** decided · 2026-09-08 · WO-01 (numbered 002 because 001 records the package layout)

## Deviations and why

| Spec / PRD | Implemented | Why |
|---|---|---|
| `site` carries `parcels[]`, `buildings[]`, `zoning`, `restrictions[]`, `hazards[]`… | `Site` is the *resolved identity* (address, coordinates, jurisdiction, parcel ids, EGID). Parcels, buildings, regulations, events and findings live on `AuditResult` | One container for the whole run (= `evidence.json`) avoids duplicating findings inside `site` and again in the findings list |
| `finding.class` | Python attribute `cls`, JSON key `class` (pydantic alias) | `class` is a keyword; JSON on disk still matches PRD §5 |
| `finding` fields | Added `template_key`, `slots`, `icon`, `rule_ref`, `alternatives`, `validation_notes` | Layer-0 rendering (WO-07) needs the template id and slot values; abstention rules (PRD §3.6) need to know when a finding relies on a regulation rule (`rule_ref`) and which sources conflict (`alternatives`); `validation_notes` makes every downgrade auditable in layer 2 |
| `construction_event.value_estimate` | Omitted | `CLAUDE.md` non-negotiable 3: never produce valuations or cost estimates (P1). Can be added when a phase actually needs it |
| `regulation.extracted_rules`, `confidence` | `rules: list[Rule]` where each `Rule` requires ≥ 1 evidence span and a `parser_version`; `unresolved: list[str]` names the rule keys the parser could not extract; `class` on the regulation | Enforces "never store `max_height = 15m` without its span" at the type level; unresolved keys become class-D findings downstream instead of silence |
| `parcel.zoning`, `legal_restrictions`, `source_records[]` | `zoning_code`/`zoning_name`; restrictions are findings; `sources: list[Source]` | Keeps parcel a data object; restrictions are already findings with evidence |
| Coordinates | Both CRS stored on every `Coordinates` (`lon/lat` WGS84, `east/north` LV95); geometries stored as GeoJSON dicts twice (`geometry_wgs84`, `geometry_lv95`) | `CLAUDE.md` convention; areas computed in LV95; evidence.json stays plain GeoJSON |
| `finding.geometry_intersection: {area_m2, fraction} \| null` | Same | — |

## Validation (PRD §3.6, §5)

`topoli.core.evidence.validate.validate()` never upgrades a class. It downgrades to D for: class A/B with incomplete source; `rule_ref` set without evidence spans; conflicting sources (`merge_conflicting`). A stale cache marker keeps the class and appends the "as of <date>" caveat. Each downgrade is logged on `topoli.evidence` with `finding_id`, `from_class`, `reason`, `adapter_id`, and recorded in `validation_notes`.

## i18n

Caveats added by validation are rendered through `t()` in all four languages at validation time, so `evidence.json` is self-contained. Until FR/DE/IT strings are written (WO-07), `t()` falls back to English and logs `i18n.fallback`.

## Jargon

`i18n/jargon.json` bans surface forms in *all* languages regardless of the output language (codes such as `W3` or `ÖREB` leak across languages). Zone-code patterns (`W1–W6`, `Z1–Z7`, `K1–K5`, `R1–R7`) are Zürich/Geneva-style; other cantons add theirs with their adapter.
