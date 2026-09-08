# 005 — City of Zürich: which density definition, and how existing floor area is approximated

**Status:** decided, awaiting architect review · 2026-09-08 · WO-05

## Density rule used

The BZO 2016 of the City of Zürich (AS 700.100, consolidated "mit Änderungen bis 29. Mai 2024") sets density in the Wohnzonen (Art. 13 Abs. 1) and Zentrumszonen (Art. 18 Abs. 1) as an **Ausnützungsziffer** (AZ) in percent, e.g. W3 90 %, W4 120 %, W5 165 %, Z6 230 %. Under § 254 PBG ZH the AZ is the ratio of the *anrechenbare Geschossfläche* (chargeable floor area of full floors and the attic/basement floors that count) to the *anrechenbare Landfläche* (chargeable land area of the parcel in the building zone).

Topoli reads the AZ from the article table (evidence span = the table row) and computes

```
allowed_floor_area = AZ × parcel_area
```

using the cadastral parcel area as the chargeable land area. This **over-estimates** the allowed area where parts of the parcel are outside the building zone or already counted for another building, and ignores Art. 13 Abs. 2 (areas with increased density along designated streets) and Arealüberbauung bonuses (Art. 8). Both are stated in the caveat.

Industrie- und Gewerbezonen use a **Baumassenziffer** (m³/m²) plus an AZ only for Handel/Dienstleistung; Quartiererhaltungszonen and Kernzonen set density through floors, building depth and street fronts. For these zones the potential is **undetermined** (class D), never converted.

## Existing floor area

The GWR publishes per building the footprint (`garea`), the number of storeys (`gastw`: **all** storeys incl. ground floor; attic and basement storeys count when at least partly residential; cellars do not — Merkmalskatalog 4.2 / housing-stat FAQ) and, for most buildings, the **energy reference area** `gebf` (heated gross floor area; the register enforces `gebf ≤ garea × gastw`). Topoli uses

```
existing_floor_area ≈ Σ buildings ( gebf if published, else gastw × garea )
```

`gebf` is the closest public proxy for the chargeable floor area (heated floors, walls included). Where it is missing the product `gastw × garea` is used and labelled an **upper bound** in the inputs and derivation, because it counts attic and basement storeys and unheated areas. A first run over 20 City of Zürich addresses (2026-09-08) shows utilisation mostly above 100 % — older buildings were built under earlier ordinances or with bonuses — so the layer-0 sentence for ≥ 100 % says "essentially built out … what stands today is protected", never "violation".

## Open questions for the reviewing architect

1. Is the energy reference area (`gebf`) an acceptable proxy for the chargeable floor area, or should a factor be applied (and which one is defensible for Zürich)?
2. Should the "increased density" streets (Art. 13 Abs. 2) be detected from the zoning layer (the canton's dataset does not carry them) — or stay a caveat?
3. Art. 13 "Überbauungsziffer Hauptgebäude" and "Gebäudelänge" rows are column-ambiguous in the text layer (three and two values for nine zones). They stay unresolved rather than guessed. Confirm which zones they apply to (W2bI–W2bIII?) so the parser can bind them.

Corrections land in `topoli/countries/ch/zh/regulation/parser.py` (bump `PARSER_VERSION`) and `topoli/core/scoring/potential.py`.
