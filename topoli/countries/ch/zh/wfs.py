"""Canton of Zürich OGD WFS (``https://maps.zh.ch/wfs/OGDZHWFS``).

Read on 2026-09-08: GetCapabilities (WFS 2.0.0, GeoJSON output
``application/json; subtype=geojson``, default CRS EPSG:2056, ``AccessConstraints: none``,
``Fees: none``, provider "Geoinformation Kanton Zürich"); terms of use
https://www.zh.ch/de/politik-staat/opendata.html — open government data, "frei nutzbar",
commercial use and redistribution allowed, no warranty.

Request used: ``GET …/OGDZHWFS?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0
&TYPENAMES=<type>&SRSNAME=EPSG:2056&OUTPUTFORMAT=application/json; subtype=geojson
&BBOX=<minx,miny,maxx,maxy>,EPSG:2056&COUNT=<n>``.

Feature types used by the Zürich adapters:

* ``ms:ogd-0156_arv_basis_np_gn_zonenflaeche_f`` — "ÖREB-Kataster – vereinfachtes Datenmodell ZH –
  Nutzungsplanung (Grundnutzung) (156.1)": harmonised communal zoning for **every** municipality
  of the canton; attributes ``typ_gde_abkuerzung`` (zone code, e.g. ``W4``, ``QI/5a``, ``K``),
  ``typ_gde_bezeichnung`` (zone name), ``typ_zh_abkuerzung``/``typ_zh_bezeichnung`` (cantonal
  zone family), ``vollgeschosse_max``, ``gebaeudehoehe_max``, ``wohnanteil_min``,
  ``rechtsstatus``, ``festsetzungsdatum``/``festsetzungsnr``, ``genehmigungsnr``, ``dokument``
  (ÖREB document ids incl. the BZO), ``typ_bfsnr``.
* ``ms:ogd-0368_giszhpub_arv_kaz_denkmalschutzobjekte_p`` — "Denkmalschutzobjekte (368.1)":
  protected objects (cantonal + communal), point per object with ``objekt``, ``einstufung``
  (``kantonal``/``kommunal``), ``schutz``, ``katasternummer`` (parcel), ``egid``, ``erlass``.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from topoli.core.adapters import Record, get_client

WFS_URL = "https://maps.zh.ch/wfs/OGDZHWFS"
TERMS_URL = "https://www.zh.ch/de/politik-staat/opendata.html"
TYPE_ZONING = "ms:ogd-0156_arv_basis_np_gn_zonenflaeche_f"
TYPE_HERITAGE = "ms:ogd-0368_giszhpub_arv_kaz_denkmalschutzobjekte_p"


def get_features(
    adapter_id: str,
    typename: str,
    bbox: tuple[float, float, float, float],
    *,
    count: int = 10,
    ttl: timedelta = timedelta(days=30),
) -> Record:
    minx, miny, maxx, maxy = bbox
    params: dict[str, Any] = {
        "SERVICE": "WFS",
        "REQUEST": "GetFeature",
        "VERSION": "2.0.0",
        "TYPENAMES": typename,
        "SRSNAME": "EPSG:2056",
        "OUTPUTFORMAT": "application/json; subtype=geojson",
        "BBOX": f"{minx:.1f},{miny:.1f},{maxx:.1f},{maxy:.1f},EPSG:2056",
        "COUNT": count,
    }
    return get_client().get_json(adapter_id, WFS_URL, params, ttl=ttl)


def features(record: Record) -> list[dict[str, Any]]:
    payload = record.payload
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        return [f for f in payload["features"] if isinstance(f, dict)]
    return []
