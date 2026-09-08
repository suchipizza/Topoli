# WO-02 — Federal spine: geocode, parcel, buildings

**Read first:** PRD (repo) §3.2 steps 1–3, §4.1, §4.3; `CLAUDE.md` non-negotiables 5–6.
**Depends on:** WO-01.

## Objective
`resolve_address("Badenerstrasse 123, Zürich")` → `Site` with coordinates (WGS84 + LV95), municipality, canton, EGID, parcel IDs; `get_parcel(id)` → geometry + area; `get_buildings(parcel)` → footprints, floors, year, use.

## Tasks
1. `core/adapters/base.py` — the `Adapter` protocol from PRD §4.3 (`id`, `jurisdiction`, `licence`, `fetch`, `to_findings`, `health`) plus `Record` (raw payload, `retrieved_at`, `url`, `adapter_id`).
2. Read `https://docs.geo.admin.ch/` (SearchServer, identify, and layer catalogue). In each adapter docstring record: doc URL, exact endpoint, parameters used, layer names, licence terms found. If terms are unclear → `docs/decisions/002-geoadmin-licensing.md` and stop for confirmation before shipping.
3. `countries/ch/federal/geocode.py` — SearchServer `locations` search; accept free-form address, `Parcel <municipality> <no>`, or `lat,lon`; return the best match with a confidence; handle multiple candidates by preferring the one matching the postcode/municipality mentioned; typo tolerance via the service's fuzzy behaviour, not our own.
4. `countries/ch/federal/parcel.py` — identify on the cadastral parcel layer at the resolved point; return geometry (both CRS), area (computed in LV95 via shapely, cross-checked with the service's attribute), national/local IDs, municipality; also return adjacent parcel IDs (touching geometries) for layer-1 section 3.
5. `countries/ch/federal/buildings.py` — GWR/RegBL attributes and footprints for the parcel (intersect building layer with parcel geometry): EGID, footprint area, floors, construction year, category/use, energy carrier if public. Record which attributes are missing rather than defaulting.
6. `core/geospatial/` — CRS transforms, `intersect(parcel, layer_geoms) -> (area_m2, fraction)`, point-in-polygon, buffer(radius m) in LV95.
7. Fixtures: record real responses for 5 sites (2 City of Zürich, 1 Winterthur, 1 Genève, 1 Lugano) with `pytest-recording`; tests run offline by default, `-m live` hits the network.
8. `LICENCES.md` rows for every dataset touched.
9. CLI: `topoli resolve "<address>"` prints the Site as JSON; `topoli parcel <id>`; `topoli buildings <parcel-id>`.

## Done when
`uv run topoli resolve "Badenerstrasse 123, 8003 Zürich"` returns a parcel ID and ≥ 1 building; all five fixtures pass offline; `-m live` passes; `LICENCES.md` has rows for search, cadastre and GWR layers.
