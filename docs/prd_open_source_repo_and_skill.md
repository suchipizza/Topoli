# PRD — Topoli Open-Source Repository & Claude Skill (Phase 1)

**Version:** 1.0 · 8 September 2026
**Owner:** Noémie
**Parent doc:** `topoli_product_spec_v2.md` (strategy, phases, business model)
**Scope of this PRD:** everything that ships in the GitHub repository for Phase 1 — the `/property-audit` skill, the data adapters, the evidence model, the local HTML report, share artefacts, i18n, tests, and repo hygiene. The website has its own PRD.

---

## 1. Goal and success

**Goal:** a non-developer installs the skill in ≤ 3 steps, types one address, and within 90 seconds sees five findings about that property that surprise them enough to share the result.

**Phase 1 north-star metrics:** GitHub stars/week and waitlist signups (attributed to the skill via share links).

**Launch acceptance (all required):**
1. Install → first result works on a clean machine in Claude Code and in Claude.ai (where skills are supported), in < 10 minutes, following only the README.
2. `/property-audit` returns a complete layer-0 result for ≥ 95% of addresses in the City of Zürich and ≥ 80% of addresses elsewhere in Switzerland (federal layers only), measured on a 200-address regression set.
3. p50 time-to-first-result ≤ 60 s, p95 ≤ 90 s, on a normal home connection.
4. Every regulatory or hazard claim in layer 1 links to a source with dataset name, retrieval timestamp and URL.
5. All user-facing text exists in FR/DE/IT/EN and has been reviewed by a native speaker.
6. The HTML report and PNG share card render correctly, offline, and contain the repo URL and star CTA.
7. No API key, account, or configuration is required.

---

## 2. Users

| User | Entry point | Needs |
|---|---|---|
| General public (homeowner, buyer, neighbour) | Website → "run it in 3 steps" | Plain language, own language, no setup, one screen |
| Professional (architect, developer, supplier, investor) | Same, plus README | Full 18-section audit, sources, confidence classes, precedent activity |
| Contributor | GitHub | Clear adapter interface, fixtures, "good first canton" issues, CI feedback |
| Agent (Claude) | `SKILL.md` | Deterministic tools it can call, unambiguous output contract, abstention rules |

---

## 3. The skill: `/property-audit`

### 3.1 Invocation

```text
/property-audit "<address>" [--lang fr|de|it|en] [--goal "<free text>"] [--depth quick|full]
```

- `address`: any Swiss postal address, `Parcel <municipality> <number>`, or `lat,lon`. Free-form; the resolver handles typos and missing postcodes.
- `--lang`: defaults to the address's canton language (ZH→de, GE→fr, TI→it, bilingual cantons → canton's majority language); user's session language overrides if detectable.
- `--goal`: free-text intent ("build 12 apartments", "buy to renovate", "just curious"). Alters which findings rank in the top five and the recommended next step. Optional.
- `--depth`: `quick` = layer 0 only (default); `full` = layer 0 + layer 1 rendered immediately.

Natural-language invocations must also work: "What can I build at Badenerstrasse 123, Zürich?" → the skill triggers via its description in `SKILL.md`.

### 3.2 Pipeline (what the agent executes)

```text
1. resolve_address(address)          → site{coordinates, municipality, canton, parcel_ids[]}
2. get_parcel(parcel_id)             → parcel{geometry, area, zoning_code, local_id, national_id}
3. get_buildings(parcel)             → building[]{footprint, floors, year, use, heritage}
4. query_layers(parcel.geometry, federal_layer_set) → raw intersections (hazard, noise, contamination, ÖREB, solar)
5. fetch_regulation(canton, municipality, zoning_code) → regulation{rules[], evidence_spans[]}   [Zürich only in P1]
6. compute_potential(parcel, buildings, regulation) → class-C estimate with formula shown
7. search_construction_events(coordinates, radius=500m, since=12m) → event[]   [Zürich only in P1]
8. rank_findings(all, goal, lang)    → top 5 for layer 0 + full list for layer 1
9. render(report, lang)              → terminal text, ./reports/<id>/index.html, share card
```

Steps 1–7 are **deterministic scripts** (`scripts/*.py`), not model reasoning. The agent only calls them, then does steps 8–9 with a strict template. This is the mechanism that prevents regulatory hallucination.

Every step emits progress to the terminal (`✓ Resolved address`, `✓ Found parcel 8003/1234`, `✓ Checked 11 federal layers`, `⚠ Cantonal regulation not available for VS — help add it`). Partial failure never aborts: missing sources become explicit "unknown" findings.

### 3.3 Output contract — Layer 0 (default)

Exactly this structure, in the user's language:

```text
PROPERTY CHECK — <formatted address>, <municipality>

<emoji> <one-sentence finding a homeowner understands>
        <one-sentence consequence>
… (3 to 5 findings)

Confidence: <n> official facts · <n> calculations · <n> estimates · <n> need a professional
Next step: <exactly one action, with the specific article/office/document>

▸ Open full report: ./reports/<id>/index.html
▸ Share: ./reports/<id>/card.png
```

Rules:
- 3–5 findings, ranked by (a) relevance to `--goal`, (b) severity, (c) surprise value (heuristic: findings that contradict the naive expectation rank higher).
- Vocabulary whitelist per language: no term from `i18n/jargon.json` may appear in layer 0 (e.g. Ausnützungsziffer, COS, ÖREB, W3, ES III). Enforced by a test.
- No numbers with more precision than two significant figures in layer 0.
- Every finding stores its class (A/B/C/D) and source; layer 0 only shows the compressed confidence line.

### 3.4 Output contract — Layer 1 (full report)

Eighteen sections, each rendered only if data exists, with a "Not available for this canton yet → help add it" stub otherwise:

1. Identity (address, EGID, parcel IDs, municipality, canton)
2. Existing buildings (footprint, floors, year, use, energy class if public)
3. Parcel (area, geometry, adjacent parcels)
4. Zoning (code, name, plain explanation)
5. Applicable regulations (rules extracted, article citations, effective dates)
6. Development potential (formula, inputs, result, class C)
7. Public-law restrictions (ÖREB/RDPPF)
8. Natural hazards (flood, landslide, avalanche, rockfall — each with intersection area)
9. Environmental constraints (contaminated sites, groundwater protection, nature/forest)
10. Noise (sensitivity level, exposure, source)
11. Heritage (federal/cantonal/municipal inventories, ISOS)
12. Terrain & geology (slope, elevation range)
13. Energy & solar (roof suitability, orientation)
14. Nearby construction activity (events within 500 m, 12 months) — Zürich only in P1
15. Unknowns & missing data (explicit list, with the source that would resolve each)
16. Decision summary (goal-aware, 5–8 sentences, class-tagged)
17. Recommended professional checks (who to ask, for what)
18. Sources (dataset, authority, licence, retrieved_at, URL — one row per claim)

Each finding in layer 1 shows its class badge (A/B/C/D) and a "why" expander linking to layer 2.

### 3.5 Layer 2 (evidence)

Machine-readable `./reports/<id>/evidence.json` containing every `finding` object (schema §5), raw API responses (`raw/*.json`), geometry intersections (GeoJSON), parser version, and timestamps. Layer 1's "why" expander reads from this file.

### 3.6 Abstention rules

- If a rule has no evidence span → the finding is class D ("cannot be determined from public data"), never a guess.
- If two sources conflict → both are shown, marked, and the finding is class D with the conflict named.
- If a source is > 30 days stale in the cache → refetch; if the fetch fails → serve cached with a "as of <date>" marker.
- Financial valuations, cost estimates, approval likelihood: never produced in P1.

---

## 4. Data adapters (Phase 1 scope)

### 4.1 Federal baseline (all of Switzerland)

| Adapter | Source | Provides | Licence check |
|---|---|---|---|
| `ch/federal/geocode` | geo.admin.ch SearchServer | address → coordinates, municipality, EGID | ✔ required before ship |
| `ch/federal/parcel` | geo.admin.ch identify (cadastral layer) | parcel geometry, IDs, area | ✔ |
| `ch/federal/buildings` | GWR/RegBL via geo.admin.ch | building footprints, floors, year, use | ✔ |
| `ch/federal/oereb` | ÖREB cadastre extract API | public-law restrictions per parcel | ✔ (per canton availability) |
| `ch/federal/hazards` | federal hazard maps (flood, landslide, avalanche, rockfall) | intersections | ✔ |
| `ch/federal/noise` | federal road/rail noise layers (Lärmbelastung) | exposure bands | ✔ |
| `ch/federal/contamination` | KbS cadastre of polluted sites | intersections | ✔ |
| `ch/federal/solar` | Sonnendach roof suitability | per-building suitability class | ✔ |
| `ch/federal/heritage` | ISOS + federal inventories | listing status | ✔ |
| `ch/federal/terrain` | swissALTI3D via geo.admin.ch height service | elevation, slope | ✔ |

### 4.2 Zürich (first deep canton)

| Adapter | Source | Provides |
|---|---|---|
| `ch/zh/zoning` | Canton ZH / City of Zürich zoning WFS | zone code + name for a parcel |
| `ch/zh/regulation` | BZO (Bau- und Zonenordnung) of the City of Zürich, PBG canton | extracted rules per zone: Ausnützungsziffer, max floors, max height, setbacks, with article evidence spans |
| `ch/zh/heritage` | municipal inventory of protected buildings | listing status |
| `ch/zh/construction_events` | Stadt Zürich Baukollegium / Bauausschreibungen publications | permits within radius, applicant, project type, date |

P1 regulation extraction covers **City of Zürich BZO only**; other ZH municipalities return zone code (from the cantonal layer) but class D for numeric rules, with the stub "regulation parsing for <municipality> not yet contributed".

### 4.3 Adapter interface (contract every adapter must satisfy)

```python
class Adapter(Protocol):
    id: str  # "ch/zh/zoning"
    jurisdiction: Jurisdiction  # country, canton, municipality (or None)
    licence: Licence  # SPDX-like id + attribution string + redistribution flag

    def fetch(self, site: Site) -> list[Record]: ...  # raw records with retrieved_at, url
    def to_findings(self, records, site, lang) -> list[Finding]: ...
    def health(self) -> HealthStatus: ...  # used by coverage dashboard
```

Every adapter ships with: (a) recorded fixtures for ≥ 3 sites, (b) a source-contract test that hits the live endpoint nightly and fails on schema drift, (c) an entry in `LICENCES.md`.

### 4.4 Caching

Local on-disk cache (`~/.topoli/cache/`), keyed by adapter + request, TTL 30 days for static layers, 24 h for construction events. No network calls to any Topoli server in P1. A `--no-cache` flag exists.

---

## 5. Evidence model

```yaml
finding:
  id: string
  title: {fr, de, it, en}            # written per language, not machine-translated
  consequence: {fr, de, it, en}
  class: A | B | C | D               # official / derived / estimate / professional
  severity: info | low | medium | high
  category: potential | hazard | noise | heritage | environment | zoning | activity | identity | unknown
  source:
    adapter_id: string
    authority: string
    dataset: string
    licence: string
    retrieved_at: ISO-8601
    url: string
  geometry_intersection: {area_m2, fraction} | null
  derivation: string | null          # formula or rule text for class B/C
  evidence_spans: [{document, article, text}] | []
  caveat: {fr, de, it, en}
  rank_score: float
```

Rule: a class-A or class-B finding without `source.url` and `retrieved_at` fails validation and is downgraded to D. The regression suite asserts this.

---

## 6. Local HTML report

Path: `./reports/<municipality>-<parcel>/index.html`, fully self-contained (inlined CSS/JS, map tiles fetched from swisstopo at view time with graceful fallback to a static PNG).

Sections and behaviour:
- **Header:** address, municipality, date, language switcher (FR/DE/IT/EN — switches all copy client-side from embedded `i18n`), star button, share button.
- **Findings cards (layer 0):** the five findings, colour by severity, class badge, expand to layer 1 detail.
- **Map:** parcel outline, building footprints, hazard/noise overlays toggled per finding, nearby construction pins.
- **Full report:** 18 collapsible sections (§3.4).
- **Nearby activity timeline** (Zürich P1; generic component for P2).
- **Coverage notice:** what was checked, what wasn't available for this canton, link to contribute.
- **Sources panel:** table with dataset, authority, licence, retrieved_at, URL.
- **Trust footer:** the four classes explained in one line each; "This does not replace an architect, planning office, notary or land register"; licences.
- **Waitlist block:** "What would you want next?" checkboxes (from spec §6.8) posting to the website's endpoint; works without JS by linking to the website form with prefilled `?src=report&lang=`.

Design: one accent colour, system font stack, prints cleanly to A4 (professionals will PDF it). Lighthouse ≥ 90 on performance and accessibility. Renders on mobile.

---

## 7. Share artefacts

Generated on every run (no separate command):

| Artefact | File | Contents |
|---|---|---|
| Static report | `index.html` | §6, self-contained, forwardable by email |
| Property card | `card.png` (1200×630, also 1080×1080) | address, five findings, map thumbnail, confidence line, project name, `topoli.<tld>/run` (placeholder), "⭐ Star on GitHub" |
| Text block | `summary.txt` | layer 0 verbatim + "Run this yourself in 3 steps → <url>" |

Card generation runs headless (Playwright or a pure-Python renderer); it must not require a browser install step for the user — bundle or degrade to HTML-only with a notice.

Share links carry `?src=card&lang=<lang>` for the website's privacy-safe counter. No personal data, no address, in any tracking parameter.

---

## 8. Internationalisation

- `i18n/{fr,de,it,en}.json`: all UI strings, finding titles/consequences templates, section names, next-step templates, jargon glossary.
- `i18n/jargon.json`: terms banned from layer 0 with one-line explanations for layer 1.
- Findings are **templated per language with slots** (`"Le bâtiment existant utilise environ {pct}% de ce que le zonage semble permettre."`), never translated at runtime.
- Number, area and date formatting per locale (`1'234 m²` in de-CH, `1 234 m²` in fr-CH).
- Source excerpts stay in the source language with a one-line paraphrase in the user's language.
- Test: every key present in all four files; every layer-0 template passes the jargon test; a native reviewer signs off each file (checklist in `CONTRIBUTING.md`).

---

## 9. Repository

```text
topoli/
├── README.md (en) · README.fr.md · README.de.md · README.it.md
├── LICENSE (Apache-2.0)  · LICENCES.md (per-source data licences)
├── CONTRIBUTING.md · CODE_OF_CONDUCT.md · ROADMAP.md · SECURITY.md
├── skills/property-audit/
│   ├── SKILL.md                    # trigger description, invocation, output contract, abstention rules
│   ├── prompts/{layer0,layer1,next_step}.{fr,de,it,en}.md
│   └── scripts/{resolve,parcel,buildings,layers,regulation,potential,events,render}.py
├── core/{domain,evidence,geospatial,scoring,reporting,i18n}/
├── countries/ch/{federal,zh}/…
├── ui/local-report/{template.html,card/}
├── i18n/{fr,de,it,en,jargon}.json
├── examples/{zurich-badenerstrasse,zurich-seefeld,geneva-federal-only}/   # committed sample reports
├── tests/{fixtures,source-contracts,regression,i18n}/
└── .github/{workflows,ISSUE_TEMPLATE,FUNDING.yml}
```

**README (canonical, en; the other three are written, not translated):**
1. One-line tagline + 30-second GIF (address in → five findings + report opening).
2. "Run it in 3 steps" — identical to the website's steps, for Claude.ai and Claude Code.
3. Five try-it prompts (Zürich, Geneva, Basel, Lugano, Bern).
4. What it checks / coverage table with bars.
5. What it does not do (no valuations, no approval predictions, does not replace professionals).
6. Coming next — vote on the waitlist (`/nearby-construction`, `/development-potential`, `/construction-leads`, `/renovation-opportunities`).
7. Contributing: "add your canton" in 4 steps.
8. Licences, imprint, star badge with live count.

**Install (the 3 steps, must be identical in README and website):**
1. Open Claude (Claude.ai or Claude Code).
2. Add the skill: paste the repo URL / run the one-line install command shown.
3. Type `/property-audit "<your address>"`.

Any variation between environments is handled inside step 2 with tabs, never by adding a step.

**Repo hygiene for stars:** topics set (`switzerland`, `open-data`, `claude-skill`, `ai-agents`, `proptech`, `construction`), social preview image = the property card, `good first canton` and `good first issue` labels seeded with ≥ 10 issues at launch, GitHub Discussions on, release v0.1.0 tagged on launch day.

---

## 10. Quality, testing, CI

| Suite | What it asserts | Runs |
|---|---|---|
| Unit | domain model, scoring, i18n formatting | every PR |
| Fixture regression | 200 Swiss addresses (120 ZH, 80 other cantons) → expected layer-0 findings, class counts, no jargon | every PR |
| Source contracts | live endpoints return the expected schema | nightly; failure opens an issue and flips the coverage bar to "degraded" |
| Golden reports | 3 example reports byte-compare (modulo timestamps) | every PR |
| Professional review | 20 ZH audits reviewed by an architect before launch; error log kept in `tests/review/` | pre-launch, then monthly |
| Performance | p95 ≤ 90 s end-to-end on fixtures with network replay | weekly |
| Accessibility | report Lighthouse ≥ 90 | every PR touching `ui/` |

Definition of "finding error" for the review: a class-A/B claim that is wrong, or a class-C/D claim presented as A/B. Launch bar: ≤ 2 errors in 20 audits, zero in hazards.

---

## 11. Telemetry

None sent from the skill. The only signal is the share-link counter on the website. A `--stats` flag prints local run timing for bug reports. This is a stated principle in the README ("runs on your machine, talks only to official sources").

---

## 12. Non-functional requirements

- Python ≥ 3.11, dependencies installable with one `pip`/`uv` command; no compiled geospatial stack (use `shapely` wheels; avoid GDAL).
- Works on macOS, Linux, Windows (WSL acceptable for Claude Code; Claude.ai path has no OS dependency).
- Offline re-render of any existing report.
- Respect source rate limits; total calls per audit ≤ 25; exponential backoff.
- Apache-2.0 for code; data licences per `LICENCES.md`; never redistribute datasets, only fetch on demand.

---

## 13. Out of scope for Phase 1 (explicitly)

Other commands · non-ZH cantonal regulation parsing · financial feasibility, valuation, cost or margin estimates · approval-likelihood predictions · parcel fusion · area scanning · monitoring/alerts · accounts, hosted API, any Topoli server call · Cursor/ChatGPT/Gemini/MCP adapters · CAD/BIM export · Romansh · PDF export (browser print is enough).

---

## 14. Phase 1 milestones

| # | Milestone | Done when |
|---|---|---|
| M0 | Due diligence | licensing matrix signed off; name cleared; Terrara/BuildRush trials on 15 parcels logged; `claude-seo` install flow documented |
| M1 | Federal spine | `resolve → parcel → buildings → 10 federal layers` on 200-address fixture, evidence.json valid |
| M2 | Zürich depth | BZO rules extracted for all City of Zürich zones with evidence spans; potential formula reviewed by an architect |
| M3 | Layer 0/1 in four languages | templates written per language; jargon test green; native review done |
| M4 | Report + share | HTML report, card.png, summary.txt; Lighthouse ≥ 90; prints to A4 |
| M5 | Skill packaging | works in Claude Code and Claude.ai in 3 steps on a clean machine; GIF recorded |
| M6 | Launch readiness | README ×4, 10 seeded issues, CI green, 20-audit professional review passed, website live |

---

## 15. Open questions

1. Claude.ai skill distribution mechanics at launch date — confirm the exact install path and whether scripts can run there; if not, the Claude.ai path may need a lighter, fetch-only variant.
2. ÖREB extract availability and licence per canton — determines which cantons get section 7.
3. Whether the City of Zürich construction publications are machine-readable enough for P1, or whether nearby activity moves entirely to Phase 2.
4. Card rendering dependency (Playwright vs pure-Python) — decide on install-friction grounds.
