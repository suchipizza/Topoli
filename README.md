# Topoli

**Open-source construction intelligence for AI agents.**

Give your agent a Swiss address. It gathers official data, tells you what you can build, what could block you and what's happening nearby — with the evidence behind every conclusion. In French, German, Italian and English.

> **Status: pre-alpha, under construction.** The first command, `/property-audit "<address>"`, is being built work order by work order (see [`docs/work-orders/`](docs/work-orders/)). The launch README with the 3-step install, try-it prompts and coverage table lands with release v0.1.0.

## What it will do

```text
/property-audit "Badenerstrasse 123, Zürich"
```

Within about a minute: five plain-language findings (layer 0), an 18-section sourced report (layer 1) and the raw evidence (layer 2). No account, no API key, no telemetry — it runs on your machine and talks only to official public sources.

## Principles

- **Deterministic data path.** Scripts fetch and compute; the model only ranks findings and fills templates. It never invents a regulation, a hazard or a number.
- **Evidence on everything.** Every finding carries authority, dataset, retrieval time and URL, and one of four confidence classes (official fact · derived fact · estimate · professional judgment required).
- **Abstain, don't guess.** No evidence → "cannot be determined from public data". Never valuations, cost estimates or approval likelihoods.
- **Four languages, written not translated.**
- **Coverage is explicit.** Federal layers cover all of Switzerland; Zürich is the first deep canton. Help add yours →

## Development

```bash
uv sync
uv run topoli doctor
uv run ruff check . && uv run mypy . && uv run pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`ROADMAP.md`](ROADMAP.md) and [`docs/`](docs/).

## Licence

Code: [Apache-2.0](LICENSE). Data: fetched on demand from official sources under their own licences, listed in [`LICENCES.md`](LICENCES.md). Never redistributed.
