# 004 — Federal constraint layers: what is queryable, how, and what is not

**Status:** decided · 2026-09-08 · WO-03

## Adapter contract change

`Adapter.fetch()` / `to_findings()` take a `SiteContext` (site + parcel + buildings) instead of a bare `Site` (PRD §4.3): every layer adapter needs the parcel outline, and solar needs the buildings' EGIDs. `to_findings` returns findings localized in all four languages; the caller picks the output language.

## Sources per adapter (verified live on 2026-09-08)

| Adapter | Mechanism | Why |
|---|---|---|
| hazards | WMS `GetMap` 64×64 PNG over the parcel bbox, masked by the rasterised outline (`wms.mask_coverage`) | Aquaprotect, surface runoff and SilvaProtect are **rasters**: `identify` answers "No GeoTable". A masked GetMap gives a deterministic coverage share (class B) with one call per hazard family |
| noise | WMS `GetFeatureInfo` (`value_0`, dB) at the parcel's interior point, one call per layer | Rasters; multi-layer JSON GetFeatureInfo raises a service exception, so 4 calls |
| contamination | one `identify` with the three federal KbS layers | Cantonal KbS is not on geo.admin.ch; it arrives as the ÖREB theme `ch.BelasteteStandorte` |
| ÖREB | `identify` on the availability layer → cantonal web service `GET <base>/extract/json/?EGRID=&LANG=` | Federal directive V2.0; ZH/BE/VS answer JSON (two key dialects), GE answers a third dialect (`Item`), TI has no cadastre. Failures → `degraded`, planned → `not_available` |
| solar | `identify` polygon on `ch.bfe.solarenergie-eignung-daecher`, roofs matched by `gwr_egid` | `klasse` 1–5 with `klasse_text` in DE/FR/IT/EN |
| heritage | `identify` polygon on KGS + UNESCO | **ISOS is not queryable**: `identify` returns nothing at known objects (Bern old town) and WMS GetFeatureInfo fails server-side. Reported in the caveat, tracked as a `good first issue` |
| terrain | one `profile.json` call along both bbox diagonals (24 points) | Cheaper than five `height` calls; slope = Δh / diagonal (coarse, class B) |

## Cantonal hazard maps

The legally binding cantonal *Gefahrenkarten* are not on geo.admin.ch as queryable layers. Phase 1 reports the federal rasters with explicit caveats ("the cantonal hazard map is decisive"); where a canton has introduced the ÖREB cadastre, hazard-related themes appear through the ÖREB adapter. A cantonal hazard-map adapter is a `good first canton` contribution.

## Call budget per audit

spine 5 (search, GWR point, AV point, AV polygon, GWR polygon) + hazards 4 + noise 4 + contamination 1 + ÖREB 2 + solar 1 + heritage 1 + terrain 1 = **19** of 25. Six remain for the Zürich adapters (WO-05/06).

## Levels are ours, extents are theirs

Hazard *levels* (none/low/medium) and noise *bands* (low/medium/high) are Topoli's mapping of published extents and dB values; every finding states the rule in `derivation` and keeps the raw value in `slots`. The legally relevant limit for noise depends on the zone's sensitivity level, an ÖREB theme.
