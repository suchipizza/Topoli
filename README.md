<p align="right"><a href="README.fr.md">Français</a> · <a href="README.de.md">Deutsch</a> · <a href="README.it.md">Italiano</a></p>

# Topoli

**Open-source construction intelligence for AI agents.**

Give your AI a Swiss address. It gathers official data, tells you what you can build, what could block you and what's happening nearby — with the evidence behind every conclusion. In French, German, Italian and English. No account, no API key, nothing sent anywhere but official public sources.

[![Stars](https://img.shields.io/github/stars/suchipizza/Topoli?style=flat&label=%E2%AD%90%20Star)](https://github.com/suchipizza/Topoli/stargazers) [![CI](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml/badge.svg)](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue.svg)](LICENSE)

![30-second demo: an address in, five findings and the report out](docs/demo.gif)

```text
/property-audit "Badenerstrasse 171, 8003 Zürich"
```

```text
PROPERTY CHECK — Badenerstrasse 171 8003 Zürich, Zürich

🌧  Heavy-rain runoff: 14% of the plot can be reached by surface water during heavy rain.
    Entrances, light wells and garage ramps may need protection against water from the street or slope.

🔊  Road noise: moderate (about 64 dB by day, 51 dB at night).
    Bedrooms and living rooms may have to face away from the road or use sound-insulating windows.

🏘  40 building applications were published within 500 m in the last 12 months.
    The neighbourhood is changing (conversions, heating and solar, extensions, new buildings …).

🗺  Zoning: neighbourhood-preservation zone, up to 5 full floors and 18 m building height.
    New buildings must fit the existing street pattern: closed street fronts, prescribed building depth and roof shapes.

☀️  Solar: the roofs are well suited for solar panels (97 m² usable, about 17 MWh a year).
    A solar installation is likely worthwhile; many cantons subsidise it.

Confidence: 2 official facts · 3 calculations · 0 estimates · 0 need a professional
Next step: request the cantonal hazard-map extract for this plot from the cantonal natural-hazards office (ZH)

▸ Open full report: ./reports/zurich-AU6979/index.html
▸ Share: ./reports/zurich-AU6979/card.png
```

Real, unedited output — see the committed [examples](examples/) (Zürich ×2, Geneva) with their 18-section reports and evidence files.

## Run it in 3 steps

The steps are the same everywhere; only step 2 differs by surface.

<!-- topoli:install:start -->
1. Open Claude (Claude.ai or Claude Code).
2. Add the skill: paste the repository URL or run the one-line install command shown.
3. Type: /property-audit "<your address>"
<!-- topoli:install:end -->

**Claude Code** (macOS, Linux, WSL) — step 2 is one line:

```bash
curl -fsSL https://raw.githubusercontent.com/suchipizza/Topoli/main/install.sh | sh
```

Windows (PowerShell): `irm https://raw.githubusercontent.com/suchipizza/Topoli/main/install.ps1 | iex`. Needs Python 3.11+ and Git; the installer adds [`uv`](https://docs.astral.sh/uv/) if missing, clones this repository into `~/.topoli/src` and links the skill into `~/.claude/skills/`. Alternative: `/plugin marketplace add suchipizza/Topoli` then `/plugin install topoli@topoli` (command becomes `/topoli:property-audit`).

**Claude.ai** — step 2 is "upload the skill under Customize → Skills" (paid plans, code execution on). Being validated: whether the sandbox can reach the Swiss geodata services. Until then, Claude Code is the reliable path. [Details →](docs/decisions/011-skill-install-paths.md)

Stuck? → [GitHub Discussions](https://github.com/suchipizza/Topoli/discussions).

## Try these addresses

| Prompt | Why it is interesting |
|---|---|
| `/property-audit "Badenerstrasse 171, 8003 Zürich"` | quarter-preservation zone, 40 building applications within 500 m, road noise, runoff |
| `/property-audit "Rue du Rhône 14, 1204 Genève" --lang fr` | federal layers only — what a canton looks like before its adapters exist |
| `/property-audit "Freie Strasse 10, 4001 Basel" --lang de` | Basel old town, ÖREB restrictions |
| `/property-audit "Via Nassa 5, 6900 Lugano" --lang it` | lakeside: rare-flood extent, no public-law cadastre yet in Ticino |
| `/property-audit "Bundesplatz 3, 3011 Bern"` | heritage: federal cultural property and UNESCO old town, noise sensitivity levels |

Add `--goal "I want to build 12 apartments"` (or *buy*, *renovate*) to change which findings come first.

## What it checks

Ten federal checks for every Swiss address — address, parcel, buildings, flood/runoff/rockfall extents, road and rail noise, polluted sites, public-law restrictions (where the canton publishes its cadastre), roof solar suitability, federal heritage inventories, terrain — plus, for the Canton of Zürich, the zone, the City of Zürich building-ordinance rules with article citations, a development-potential estimate, protected objects and construction publications within 500 m. Every line carries its source, dataset, retrieval time and one of four confidence classes: **A** official fact · **B** calculation · **C** estimate · **D** needs a professional.

<!-- topoli:coverage:start -->
| Canton | Federal layers | Cantonal depth | Construction events |
|---|---|---|---|
| ZH | ██████████ 100% | ██████████ 100% | ██████████ 100% |
| GE | █████████░ 90% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| VD | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| BS | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| BE | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| TI | █████████░ 90% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| LU | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| SG | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| VS | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| GR | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| FR | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| AG | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| NE | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| JU | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| SO | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| TG | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| SH | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| SZ | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| ZG | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| BL | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| AR | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| AI | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| GL | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| OW | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| NW | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |
| UR | ██████████ 100% | ░░░░░░░░░░ 0% | ░░░░░░░░░░ 0% |

[help add yours →](https://github.com/suchipizza/Topoli/labels/good%20first%20canton)
<!-- topoli:coverage:end -->

## What it does not do

- No valuations, cost estimates or approval likelihoods — ever.
- It does not replace an architect, the planning office, a notary, the land register, a surveyor, an engineer or an environmental consultant. It tells you what to ask them.
- No guessing: when a rule has no citable article or a source is unavailable, the finding says so (class D) instead of inventing a number.
- Runs on your machine, talks only to official public sources ([`allowed_hosts.txt`](topoli/countries/ch/allowed_hosts.txt)), sends no telemetry. The only counter is the click on the share link, on the website.

## Coming next — vote on the waitlist

`/nearby-construction` · `/development-potential` · `/construction-leads` · `/renovation-opportunities` — [tell us which one you need →](https://topoli.ch/run?src=readme&lang=en)

## Contributing — add your canton in 4 steps

1. Claim a [`good first canton`](https://github.com/suchipizza/Topoli/labels/good%20first%20canton) issue (source URL, licence, fields, three fixture addresses).
2. Write the adapter in `topoli/countries/ch/<canton>/` against the `Adapter` protocol; document the endpoint and licence in the docstring.
3. Record fixtures (`topoli fixtures record …`), add a live contract test and the templates in all four languages.
4. Add the `LICENCES.md` row and open the PR. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licences

Code: [Apache-2.0](LICENSE). Data: fetched on demand from official sources under their own licences, listed in [LICENCES.md](LICENCES.md) — never redistributed. Map tiles © swisstopo. Card font: Inter (SIL OFL 1.1).

Maintained by Noémie Rakotomalala · [Imprint and privacy](https://topoli.ch/en#imprint)
