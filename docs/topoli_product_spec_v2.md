# Open-Source Construction Intelligence for AI Agents
## Product & Strategy Specification v2 — Switzerland First, Europe Next

**Status:** Pre-build product thesis (v2, rewritten 8 September 2026)
**Name:** **Topoli**
**Initial form:** a Claude skill (inspired by `claude-seo`), distributed via GitHub and a four-language website
**Languages (day one):** French, German, Italian, English
**Audiences:** general public *and* construction/property professionals
**Phase 1 goals:** GitHub stars + waitlist
**Initial market:** Switzerland · **Next:** France · **Long term:** agent-native construction & property intelligence for Europe

---

## 0. What changed in v2

Relative to v1, this version:

1. Makes **Phase 1 = stars + waitlist** the governing constraint; everything else is subordinate.
2. Adds the missing product requirements: four languages, extreme simplicity, a fast aha moment, shareability, a general-public audience alongside professionals, a website that teaches non-developers to run a Claude skill, and `claude-seo` as the reference model.
3. Cuts v1 scope to **one command** and moves the rest to later phases.
4. Describes **every phase (1–7)** with deliverables, success criteria, and exit conditions, instead of detailing only Phase 1.
5. Condenses the competitor teardown to what changes decisions.

---

## 1. One-paragraph thesis

Swiss construction and property data is excellent but scattered across federal, cantonal, municipal, cadastral, ÖREB/RDPPF, environmental, gazette, permit and transport sources. Nobody — not a homeowner, not an architect, not an AI agent — can combine it into a decision without expertise. We encode that expertise as an **open-source agent skill**: give it an address and, within about a minute, it returns a plain-language investigation with source-level evidence. The open layer wins distribution, trust, contributors and GitHub stars; a hosted layer later monetizes what open-source users teach us is hardest — **continuous normalization, history, monitoring and opportunity detection at scale**. Formula: *fragmented government data → normalize → join around one economic object (the parcel/project) → detect constraints and events → convert into a decision → sell that decision to people for whom being wrong is expensive.*

---

## 2. Why this is attractive

**2.1 The problem is structurally right for open source.** Fragmentation is normally a weakness. Here every canton, municipality and dataset is a discrete, visible, gamifiable contribution. The repository accrues jurisdiction expertise that no single team could build alone, and the hosted product later monetizes the maintenance burden.

**2.2 Willingness to pay is unusually high.** A developer can lose hundreds of thousands of francs misreading development potential; an architect loses billable days missing a rule; a supplier loses a contract by hearing about a project too late. The value of avoiding one mistake is orders of magnitude above any software price.

**2.3 The agent interface is real differentiation.** Incumbents assume `human → website → filters → report`. We assume `human → agent → tools → reasoning → action`. The agent runs a workflow ("is this 12-apartment project plausible, and what should I ask the architect before making an offer?"), it does not display layers.

**2.4 The timing is right.** People increasingly start tasks inside Claude, Cursor and ChatGPT. Being the thing an agent reaches for when a construction/property question appears is a position incumbents do not occupy.

---

## 3. Competitors (condensed)

Two Swiss products validate the market and show what not to build. Figures below are their public claims as of 8 September 2026, not verified measurements.

### Terrara — unified Swiss cadastral/property platform, architect-centric
- Claims 4M+ parcels, 142+ parameters, 3,000+ municipalities normalized; AI Building Analyzer (>95% claimed accuracy); CAD/DXF/IFC exports.
- Pricing: Free (100 analyses) · Basic CHF 29.90 · Standard CHF 59.90 · Premium CHF 119.90 · Custom data on quote.
- Gaps: closed source, web-destination only, no agent-native workflow, no community adapter model, normalization logic not inspectable, parcel-centric rather than event-centric, free-as-in-price not free-as-in-infrastructure.
- **Lesson:** do not compete by making lookup free — Terrara already gives away 100 analyses. Compete on open execution, agent workflows, inspectable evidence, extensibility and event intelligence.

### BuildRush — land opportunity discovery & feasibility (CZH Innovations Sàrl, Lausanne)
- Promise: any Swiss address → feasibility analysis in ~15 seconds. Covers cadastre, zoning, indices (COS/CUS/IUS/IOS/IM), setbacks, hazards, noise, contamination, easements, permit history, market pricing; outputs constructibility score, 3D envelope, financial simulation, land value, developer margin, PDF.
- Differentiators: parcel fusion (merge adjacent parcels), area/municipality scanning, financial feasibility.
- Pricing: subscriptions with one-year minimum (prices not public); CHF 19.90 one-off report on indexed parcel pages.
- Gaps: closed, no reproducible reasoning path, no contribution model, opportunity analysis limited to land/development, no supplier/construction-event intelligence.
- **Lesson:** BuildRush is the benchmark for where the *paid* product eventually goes ("find me the best opportunities"). Its 15-second demo is the bar for our aha moment.

### Positioning
- Terrara = professional property data application.
- BuildRush = land-feasibility and opportunity application.
- **Topoli = the agent capability layer** — open, inspectable, extensible, and useful even if the company disappears.

**Not:** a free Terrara · a prettier BuildRush · "MCP for Swiss government data" · "chat with Swiss maps".

---

## 4. Product principles

1. **Decision before dashboard.** Every workflow starts from a question ("Can I build this?", "What could block it?", "What is being built nearby?"), never from "which layers do you want?"
2. **Evidence before confidence.** Every conclusion carries authority, dataset, retrieval time, URL, and a caveat. Traceable correctness is the professional moat.
3. **Simple first, deep on demand.** The default output is understandable by someone with no construction background. Professional depth lives one click below.
4. **Four languages, natively.** FR/DE/IT/EN are first-class in the skill, the report, the README and the website. Language defaults to the address's region and can be overridden.
5. **Aha in under two minutes.** Install to first surprising result must fit inside a coffee break. The aha moment drives sharing; sharing drives stars.
6. **Shareable by design.** Every result is an artifact somebody wants to send to someone else, and that artifact carries the project.
7. **Local/open execution first.** No mandatory account, no proprietary API. Agent → open skill → official public sources.
8. **Hosted infrastructure sells reliability, not hostage access.** The paid layer wins because it is faster, normalized, historical, monitored and supported — not because the open version was crippled.
9. **Country adapters, not country-specific architecture.** The domain model is country-independent; jurisdictions plug in.
10. **Protect the wedge.** Construction/property decisions from public data. Not generic Swiss open-data search.

---

## 5. Audiences

Two audiences, one output. The general public drives sharing and stars; professionals drive the waitlist and revenue.

### General public (new in v2 — drives distribution)
| Persona | Question | Aha moment |
|---|---|---|
| Homeowner | "What could I do with my house/plot?" | "You could likely add a floor / extension"; "Your roof is highly solar-suitable" |
| Buyer | "What will I discover too late if I buy this?" | "Flood zone: no. Noise: high (rail). Protected building: yes." |
| Curious neighbour / citizen | "What's being built next to me?" | "3 permits filed within 300 m in the last 12 months" |
| Renter / journalist / student | "Show me what this address is, officially" | The whole picture, sourced, in their language |

### Professionals (drive waitlist and paid product)
| Persona | Job | High-value capabilities |
|---|---|---|
| Architect | "Before I spend hours on a proposal, tell me what matters about this site" | zoning, setbacks, height, indices, restrictions, hazards, heritage, terrain, precedents; later CAD/BIM export |
| Property developer (strongest paid persona) | "Find land where I can create more value than the market sees" | residual potential, parcel clustering, neighbourhood activity, bulk search, alerts |
| Construction supplier / specialist | "Which new projects will need what I sell, early enough to act?" | construction-event feed → lead scoring |
| Investor | "Is this parcel under-valued relative to what can be built?" | potential, constraints, precedents, monitoring |
| Municipality / planning consultant | "How do regulation, activity and potential interact across territory?" | area analytics (enterprise, later) |

---

## 6. Phase 1 in detail — the skill, the aha moment, the website

Phase 1 has exactly two goals: **GitHub stars** and **waitlist signups**. Every deliverable below exists to serve one of those two numbers. Anything that does not is Phase 2 or later.

### 6.1 Form factor: a Claude skill, modelled on `claude-seo`

`claude-seo` is the reference: one repository, one obvious command, one clear output, install instructions that a non-developer can follow, and a result that makes people say "wait, it can do *that*?". We copy the *shape*, not the domain.

- Delivered as a Claude skill first (Claude Code and Claude.ai where skills are supported). Cursor/Codex/ChatGPT/Gemini/MCP adapters are Phase 3.
- The brand never contains "Claude". Claude is the first distribution surface, not the product.
- Install path must be **≤ 3 steps** and identical across languages.

### 6.2 One command

```text
/property-audit "Badenerstrasse 123, Zürich"
```

Optional flags: `--lang fr|de|it|en` (defaults to the address's region), `--goal "..."` (free text, e.g. "I want to build 12 apartments").

Nothing else ships in Phase 1. `/nearby-construction`, `/development-potential`, `/construction-leads` and `/renovation-opportunities` appear in the README as **"coming next — vote on the waitlist"**, not as shipped commands.

### 6.3 The aha moment (hard spec)

Target: **address in → first result on screen in ≤ 90 seconds**, including data fetches.

The first screen is **five plain-language findings, maximum**, written for the general public, in the user's language. Example:

```text
PROPERTY CHECK — Badenerstrasse 123, 8003 Zürich

🏗  You could probably build more here.
    Existing building uses ~45% of what zoning appears to allow.

🌊  Flood risk: none identified in federal hazard layers.

🔊  Noise: high — the parcel sits in a rail/road noise zone.
    This affects how apartments can be laid out.

🏛  Heritage: the building is listed in the municipal inventory.
    Demolition or major changes need approval.

🏘  6 construction permits filed within 500 m in the last 12 months.

Confidence: 3 official facts · 1 calculation · 1 estimate
Next step: verify zoning article BZO §X with the city planning office.

▸ Open full report (18 sections, sources, map)
▸ Share this check
```

Rules:
- Each finding is one sentence a homeowner understands, plus one sentence of consequence.
- The confidence line compresses the four-class safety taxonomy (§10) into one visible summary — badge, not lecture.
- Exactly one recommended next step on the first screen.
- The 18-section professional audit (identity, buildings, parcel, zoning, regulations, potential, ÖREB restrictions, hazards, environment, noise, heritage, terrain/geology, energy/solar, nearby activity, unknowns, decision summary, professional checks, sources) is **one click below**, never the default.

### 6.4 Extreme simplicity — UI requirements

- **Zero configuration.** No API keys, no accounts, no dataset selection. If a source is unavailable, the finding says "not available for this canton yet — help add it →".
- **One input.** An address. Parcel IDs and coordinates work but are never required.
- **Progressive disclosure.** Layer 0: five findings. Layer 1: full report. Layer 2: raw evidence (dataset, retrieval time, geometry intersection, parser version).
- **The visual report** (`./reports/<parcel-id>/index.html`, local, no server): map + parcel outline, the five findings as cards, expandable sections, timeline of nearby activity, source panel, language switcher, share button. Beautiful by default — it is the artefact people forward.
- **No jargon on layer 0.** "Ausnützungsziffer", "COS", "ÖREB" appear only in layer 1 with a one-line explanation.
- **Copy is written per language, not translated.** A German-speaking Zürich homeowner and a French-speaking Geneva architect must both feel the product was made for them.

### 6.5 Multilingual requirement

| Surface | FR | DE | IT | EN |
|---|---|---|---|---|
| Skill output (layer 0/1) | ✓ | ✓ | ✓ | ✓ |
| HTML report | ✓ | ✓ | ✓ | ✓ |
| README | ✓ | ✓ | ✓ | ✓ (canonical) |
| Website | ✓ | ✓ | ✓ | ✓ |
| Waitlist form | ✓ | ✓ | ✓ | ✓ |
| Source excerpts | as published (usually the canton's language) |

Implementation: all user-facing strings in `i18n/{fr,de,it,en}.json`; a native speaker reviews each language before launch; Romansh is a welcome community contribution, not a requirement.

### 6.6 Shareability

Sharing is the growth loop: *aha → share → recipient installs → star → their aha → share.*

- **Share button** on every result producing: (a) a self-contained static HTML file, (b) a PNG "property card" (the five findings, map thumbnail, project logo, repo URL), (c) a copyable text block.
- Every shared artefact carries: project name, "Run this yourself in 3 steps → [website]", "⭐ Star on GitHub".
- Shared artefacts are always inspectable — the recipient can open sources without installing anything.
- Track shares (privacy-safe counter on the website link, no personal data).

### 6.7 The website (new in v2)

One page, four languages, one job: **get a non-developer from "what is this?" to "I ran it and I'm impressed" and then to a star or a waitlist signup.**

Structure (in scroll order):

1. **Headline** — "Give your AI an address. Find out what you can build there." (localized per language)
2. **Live example** — a real report, embedded, in the visitor's language.
3. **"How to run a Claude skill" in 3 steps** — screenshots, no terminal assumed, written for someone who has never used GitHub. Covers Claude.ai and Claude Code.
4. **Try it prompts** — five copy-paste examples (Zürich, Geneva, Basel, Lugano, Bern).
5. **⭐ Star on GitHub** — prominent, repeated at top and bottom, with live star count.
6. **Waitlist** — "What would you want next?" (see §6.8).
7. **Coverage map** — honest canton-by-canton coverage bars (Federal 100%, Zürich x%, Geneva x%, …) with "help us add your canton".
8. **Trust** — what is official fact vs estimate, what the tool does not replace, licensing of sources.
9. Footer: GitHub, contributing, imprint.

Non-goals: no blog, no docs site, no pricing page, no login.

### 6.8 Waitlist design

The waitlist tests **which paid workflow professionals want**, not just email addresses. Shown after a result (in the report and on the website):

> **What would you want next?** (pick any)
> ☐ Monitor this property for changes · ☐ Scan a whole area for opportunities · ☐ Find construction leads for my company · ☐ Analyse my portfolio · ☐ Professional/client-ready reports · ☐ API / normalized data · ☐ CAD/BIM export · ☐ Other

Then role (architect, developer, investor, contractor, supplier, engineer, property manager, municipality, homeowner/buyer, software developer), company size, and canton/geography. Free-text "what were you trying to find out?" is optional but the most valuable field.

Teasers in the free report promise **new capability**, never "pay to keep using what was free". Never locked: basic hazards, citations, single-parcel lookup, the core workflow.

### 6.9 Phase 1 deliverables

- Claude skill with `/property-audit` (address → parcel → federal layers → one strong canton)
- Federal baseline adapters (geo.admin.ch search, ÖREB, hazards, solar, noise) + **Zürich** as the first deep canton
- Evidence model and four-class confidence taxonomy
- Layer 0/1/2 output, HTML report, share artefacts
- FR/DE/IT/EN across skill, report, README, website
- Website (four languages) with "how to run a Claude skill", star CTA, waitlist, coverage map
- README with a 30-second GIF demo, five try-it prompts, and "coming next" list
- Naming/trademark/domain clearance; source licensing matrix for every adapter shipped

### 6.10 Phase 1 metrics and exit criteria

Primary: **GitHub stars** and **waitlist signups**.
Secondary: install→first-result completion rate, time-to-first-result, share count, share→install conversion, language distribution, general-public vs professional ratio on the waitlist.

Success criterion: *a non-developer can go from the website to a surprisingly good answer in under ten minutes, in their language, and wants to send it to someone.*

Exit to Phase 2 when: stars are compounding week over week, ≥ 1 waitlist workflow is clearly winning, and Zürich audits are reliable enough that a professional would forward one to a client.

---

## 7. All phases

| Phase | Name | Core question answered | Primary metric |
|---|---|---|---|
| 1 | Skill + aha + website | "What can I do with this address?" | Stars, waitlist |
| 2 | Construction events | "What is changing around here?" | Repeat usage, shares |
| 3 | Multi-agent + contribution ecosystem | "Can anyone add a canton or an agent?" | External contributors, jurisdictions |
| 4 | Paid-demand test | "Which workflow do people pay for?" | Waitlist→intent conversion, WTP |
| 5 | First paid wedge | "Can we sell it?" | Paying customers, retention |
| 6 | France | "Is this a platform, not a Swiss proptech?" | French usage, adapter reuse |
| 7 | Construction knowledge graph | "Do we own the infrastructure?" | Data assets, API adoption, ARR |

Phases overlap; the sequence describes priority, not strict gating.

### Phase 2 — Construction events
Turn "what is here" into "what is changing here".
- Adapters: Geneva construction authorizations + projected buildings, Basel-Stadt Baupublikationen + public-land construction sites, Zürich construction sources.
- Event normalization (`construction_event`), nearby search, timeline in the report.
- Ships `/nearby-construction <address> --radius 1000m --since 24m`.
- Layer 0 gains a "What's happening nearby" finding for the general public; professionals get project type, applicant, author, status, significance, source.
- Success: *the agent can tell a user what is changing around a location, with sources.*

### Phase 3 — Multi-agent compatibility and contribution ecosystem
Make the project a standard, not a Claude plugin.
- Three-layer architecture formalized: deterministic tools (`resolve_address`, `get_parcel`, `query_layer`, `search_construction_events`, `fetch_regulation`, `intersect_geometry`) → portable workflows → agent adapters (Claude, Cursor, Codex, ChatGPT, Gemini, MCP server, CLI).
- Adapter SDK, source-contract tests, fixtures, CI, coverage dashboard, "good first canton" issues, freshness/health reporting.
- Ships `/development-potential`.
- Success: *someone outside the core team adds a jurisdiction; the skill runs unchanged in a second agent.*

### Phase 4 — Paid-demand test
Do not build SaaS yet. Show working previews (limited-scope, real data) for monitoring, area scanning, lead search and hosted API inside the free report and on the website.
- Ships `/construction-leads` and `/renovation-opportunities` in preview form.
- Measure: preview CTR, waitlist workflow votes, role, company size, geography, self-reported WTP, requested parcel/project volume.
- 20+ interviews with waitlist professionals; hands-on comparison against Terrara and BuildRush on the same 10–20 parcels.
- Success: *one workflow has a clear, quantified willingness to pay.*

### Phase 5 — First paid wedge
Choose from Phase 4 data, not assumptions. Candidates in likely order: (1) construction-lead monitoring for suppliers, (2) developer opportunity discovery, (3) normalized hosted API (`GET /v1/site?address=…`), (4) property/portfolio monitoring.
- Pricing hypotheses only: Developer CHF 29–49/mo · Pro CHF 99–299/mo · API usage-based · Lead intelligence hundreds/mo for SMBs, five figures/yr for large suppliers. Finalize after demand data.
- The open skill remains fully functional; the paid product is faster, historical, monitored, batchable, alertable and supported.
- Success: *first paying customers retained past month three.*

### Phase 6 — France
Prove the platform thesis. France's infrastructure is nationally standardized (BAN, cadastre, Géoportail de l'Urbanisme / API Carto, Géorisques, Sitadel permits, DVF), so it may scale nationally faster than Switzerland.
- Reuse domain model, skills, evidence system, report UI; add `countries/fr/` adapters.
- French language already shipped in Phase 1 — only data and jurisdiction logic are new.
- Benchmark: PermisAPI (monetizes transformation and reliability of public data, not ownership).
- Success: *the same skill answers a Lyon address as well as a Zürich one.*

### Phase 7 — Construction knowledge graph / infrastructure
The long-term proprietary asset: parcel ↔ building ↔ owner/entity ↔ regulation ↔ permit ↔ project ↔ architect ↔ developer ↔ contractor ↔ infrastructure ↔ event, with history, entity resolution, change detection, project classification, opportunity scores and outcome data.
- Products: monitoring, lead intelligence, opportunity discovery, portfolio analytics, enterprise/municipal analytics, CRM integrations, SLAs.
- Success: *third-party agents and products default to Topoli for construction/property questions in Switzerland and France.*

---

## 8. Data architecture

Model economic objects, not government agencies. Core objects (country-independent):

```yaml
site:        { id, country, address, coordinates, parcels[], buildings[], jurisdiction, zoning, restrictions[], hazards[], environmental_constraints[], infrastructure[] }
parcel:      { national_id, local_id, geometry, area, municipality, zoning, legal_restrictions, source_records[] }
building:    { id, geometry, use, year, floors, height, energy, heritage }
construction_event: { id, location, parcels, type, description, applicant, project_author, publication_date, status, value_estimate, expected_trades[], sources[] }
regulation:  { jurisdiction, effective_from, effective_to, source_document, extracted_rules, evidence_spans, confidence }
finding:     { title, severity, confidence, class (A/B/C/D), source{authority,dataset,retrieved_at,url}, geometry_intersection, interpretation, caveat, lang }
```

Evidence graph: never store `max_height = 15m`; store rule → source document → article → jurisdiction → effective dates → parser version → interpretation.

### Swiss sources for early phases
- **Federal (Phase 1):** geo.admin.ch search & feature identification (address, parcel, municipality resolution; ÖREB/public-law restriction layers; hazard, noise, contaminated-site layers); federal roof solar-potential dataset.
- **Zürich (Phase 1):** cantonal/municipal zoning and building regulations, construction publications.
- **Geneva (Phase 2):** construction authorizations API; projected building footprints.
- **Basel-Stadt (Phase 2):** Baupublikationen; public-land construction sites.
- **Coverage is always explicit** — never fake national completeness; coverage bars are a contribution mechanism.

### Repository shape
```text
topoli/
├── README.{en,fr,de,it}.md · LICENSE · CONTRIBUTING.md · ROADMAP.md
├── skills/            property-audit/ (P1) · nearby-construction/ (P2) · development-potential/ (P3) · construction-leads/ · renovation-opportunities/ (P4)
├── i18n/              en.json fr.json de.json it.json
├── core/              domain/ evidence/ geospatial/ scoring/ reporting/
├── countries/         ch/{federal,zh,ge,bs,...}/ · fr/{national,...}/ (P6)
├── adapters/          claude/ (P1) · cursor/ codex/ chatgpt/ gemini/ mcp/ cli/ (P3)
├── ui/local-report/   HTML report, share card generator
├── website/           four-language landing page
├── examples/          zurich-property/ geneva-permit/ basel-construction/
└── tests/             fixtures/ source-contracts/ regression/
```

---

## 9. Business model, open/proprietary boundary, moat

**Free forever:** core domain schema, skill/workflow definitions, direct public-source adapters (where licensing permits), evidence model, local single-site report, share artefacts, geospatial utilities, contribution framework, examples, tests, MCP server and SDKs.

**Proprietary/paid (Phases 5–7):** hosted normalized API, historical index, alerts/monitoring, entity resolution at scale, bulk/area search, lead scoring, CRM integrations, portfolio monitoring, premium report templates, team workspaces, commercial market data, private/custom sources, SLAs, outcome analytics.

**How open source attacks closed competitors:** commoditize the basic workflow → make it inspectable → become the developer/agent default → let the community own the long tail → monetize the operationally hard layer.

**Weak moats (do not rely on):** prompts, a skill file, calling geo.admin.ch, a prettier map, basic RAG, generic "AI analysis".

**Strong moats:** normalized cross-jurisdiction graph, historical snapshots (accumulate → proprietary), construction-event entity resolution, outcome data, distribution/integration (agents learn "use Topoli for this").

---

## 10. Safety and professional boundaries

Four output classes, visible on every report but compressed to a single badge on layer 0:

| Class | Example |
|---|---|
| **A. Official fact** | "The official layer classifies the parcel as W3." |
| **B. Deterministic derived fact** | "The parcel intersects the noise zone by ~320 m²." |
| **C. Heuristic estimate** | "Existing building uses roughly 45% of theoretical density." |
| **D. Professional judgment required** | "Whether five storeys will be approved cannot be determined from public data." |

Mitigations against regulatory hallucination: deterministic extraction where possible, evidence links on every regulatory claim, rule-specific parsers, abstention when evidence is insufficient, professional-reviewed regression cases. The product never implies it replaces an architect, planning authority, surveyor, engineer, notary, land register, environmental consultant or formal valuation. In every language.

---

## 11. Naming

Requirements: not Claude-specific, not Switzerland-specific, usable across FR/DE/IT/EN and France, credible to professionals, easy to type as a CLI/package, not limited to "parcel" (later covers projects/events). Crowded: BuildScope, BuildLens, SiteLens, SiteStack, LandLens, ParcelMind, BuildAtlas. Candidates for clearance: Topoli, BuiltGraph, CivicSite, SiteTrace, PlotOS.

Decision: **Topoli stays the codename; the public brand must be cleared (domain, trademark, GitHub org, package names in all four languages) before Phase 1 launch**, because the share loop bakes the name into every artefact. Tagline stays brand-independent: *Open-source construction intelligence for AI agents.*

---

## 12. Positioning and launch messaging

Top-level (localized):
> **Open-source construction intelligence for AI agents.**
> Give your agent an address. It gathers official data, tells you what you can build, what could block you and what's happening nearby — with the evidence behind every conclusion.

Launch hooks:
- "Switzerland has 26 cantons, 2,000+ municipalities and a maze of construction data. We taught an AI agent to investigate it. Open source, in four languages."
- "Give your AI a Swiss address. It will tell you what you can build there."

CTAs: **Run it in 3 steps →** · **⭐ Star on GitHub** · **Want monitoring, area scans or construction leads? Join the waitlist →**

---

## 13. Metrics

| Group | Metrics |
|---|---|
| Growth (Phase 1–3) | GitHub stars/week, installs, install→first-result rate, time-to-first-result, shares, share→install, language mix, public vs professional mix |
| Waitlist | signups, workflow votes, role/company distribution, geography, free-text intent |
| Data quality | source uptime, freshness, % of claims with evidence, test pass rate, jurisdiction coverage, deterministic validation accuracy, human-reviewed error rate |
| Community (Phase 3+) | contributors, adapters merged, jurisdictions, agent integrations |
| Business (Phase 4+) | preview CTR, interview-derived WTP, paying customers, retention, ARR, API adoption |

---

## 14. Risks

| Risk | Response |
|---|---|
| Competitors add agent interfaces | Win mindshare early, be the interoperable layer, make community adapters valuable, accumulate history, own integrations |
| Government APIs brittle/inconsistent | Source contracts/tests, caching, adapter isolation, freshness monitoring, visible degraded states — and this is the future paid moat |
| AI hallucinates regulation | §10 mitigations; abstain rather than guess |
| Four languages dilute quality | Native review per language before launch; layer 0 copy written, not translated |
| Simplicity vs. professional depth | Progressive disclosure; layer 0 never carries jargon, layer 1 always carries everything |
| Open source undermines monetization | Only if paid = repo; paid = scale + normalization + history + monitoring + enrichment + workflows |
| Scope creep | One command in Phase 1; the wedge is construction/property decisions from public data |
| Source licensing | Licensing matrix per adapter before it ships; never redistribute what cannot be redistributed |
| Naming/trademark collision after launch | Clear before Phase 1 — the share loop makes renaming expensive |

---

## 15. Pre-build due diligence (before Phase 1 code)

1. Hands-on trials of Terrara and BuildRush on the same 10–20 Zürich/Geneva/Basel parcels; side-by-side with authoritative portals.
2. Source/licensing matrix for every Phase 1 adapter.
3. Naming, domain, trademark, GitHub org and package clearance.
4. Five field interviews (2 architects, 1 developer, 1 supplier, 1 homeowner) to validate the layer-0 findings wording in at least two languages.
5. Read `claude-seo`'s repo structure and install flow; document what to copy.

---

## 16. Sources

**Terrara:** https://www.terrara.ch/index-en.html · https://www.terrara.ch/about.html
**BuildRush:** https://buildrush.ch/ · https://buildrush.ch/etude-de-faisabilite-analyse-parcelle · https://buildrush.ch/fusions-de-parcelles-fusionner-terrains · https://buildrush.ch/analyse-toutes-parcelles-commune-recherche-groupee · https://buildrush.ch/etude-de-cout-immobiliere · https://buildrush.ch/conditions-generales-utilisation · https://buildrush.ch/a-propos
**Switzerland:** https://opendata.swiss/ · https://docs.geo.admin.ch/ · https://docs.geo.admin.ch/access-data/search.html · https://opendata.swiss/fr/dataset/autorisation-de-construire-dossier1 · https://opendata.swiss/en/dataset?groups=soci&keywords_en=bauprojekt · https://opendata.swiss/de/dataset/eignung-von-hausdachern-fur-die-nutzung-von-sonnenenergie
**France:** https://www.data.gouv.fr/dataservices/api-carto-module-geoportail-de-lurbanisme-gpu · https://www.data.gouv.fr/dataservices/api-georisques · https://www.data.gouv.fr/organizations/permisapi/datasets

Competitor claims are reported as their claims, checked on 8 September 2026, and may change.
