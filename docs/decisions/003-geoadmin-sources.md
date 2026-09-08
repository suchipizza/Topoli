# 003 — geo.admin.ch as the federal spine: endpoints, licensing, gaps

**Status:** decided · 2026-09-08 · WO-02

## Endpoints verified against the official documentation (read 2026-09-08)

| Purpose | Endpoint | Doc |
|---|---|---|
| Address / parcel search | `GET /rest/services/api/SearchServer?type=locations&origins=address\|parcel&sr=2056` | https://docs.geo.admin.ch/access-data/search.html |
| Parcel at point / neighbours | `GET /rest/services/all/MapServer/identify` on `ch.swisstopo-vd.amtliche-vermessung` (point, then ESRI-rings polygon) | https://docs.geo.admin.ch/access-data/identify-features.html |
| Buildings on parcel | same `identify` on `ch.bfs.gebaeude_wohnungs_register` with the parcel polygon | same |
| Elevation (WO-03) | `GET /rest/services/height?easting&northing&sr=2056` | https://docs.geo.admin.ch/access-data/get-point-height.html |

Findings that shaped the code:
- Location results put the LV95 **northing in `attrs.x` and easting in `attrs.y`**. Tests assert this so drift is caught.
- `identify` accepts polygons only as ESRI JSON (`{"rings": …, "spatialReference": {"wkid": 2056}}`); GeoJSON input returns 400. Outlines are simplified to ≤ 150 vertices to keep GET URLs short.
- An entrance point can touch two parcels; the parcel is chosen by the EGRID the GWR entrance names, then by point containment.
- `fuzzy: "true"` on search does not mean "wrong": a mistyped postcode still returns the right street. Confidence is lowered for fuzziness and postcode mismatch; nothing is rejected.

## Licensing

All three sources are served under the [geo.admin.ch general terms of use (FSDI)](https://www.geo.admin.ch/en/general-terms-of-use-fsdi): free, no registration, "fair use" request limits, source must be credited. Topoli fetches on demand, caches locally, and never redistributes; attribution strings are in `LICENCES.md` and shown in the report's sources panel. Per-dataset licences on opendata.swiss (mostly "OPEN BY") do not add obligations beyond attribution for our use.

## Gaps and choices

1. **Building footprint polygons.** No identifiable geo.admin.ch layer exposes footprint polygons (swissBUILDINGS3D / swissTLM3D are download products, not `identify` layers; the search for such layers returned only the aviation "Bebaute Gebiete" derivative). The GWR provides the footprint **area** (`garea`) and a reference point per building, which is what the potential calculation (WO-05) needs. Polygons can come later from cantonal AV WFS services or the swissTLM3D STAC download; tracked as a `good first issue`.
2. **The spec's example address "Badenerstrasse 123, Zürich" does not exist** (numbering jumps to 171 in that stretch). Fixtures and examples use "Badenerstrasse 171, 8003 Zürich" instead. README copy must not promise a non-existent address.
3. **GWR code labels** are hard-coded from the Merkmalskatalog 4.2 PDF (`gwr_codes.py`) rather than fetched; unknown codes are shown raw, never guessed.
4. **Municipality name** comes from the GWR entrance nearest the point (`ggdename`), not from the search label, because the search label carries the postal locality, which differs from the political municipality (e.g. "8003 Zürich" vs. Zürich, BFS 261, is fine, but "Genève" postal localities span several communes).
