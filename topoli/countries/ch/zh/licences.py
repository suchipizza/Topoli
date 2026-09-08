"""Licences for Canton/City of Zürich sources; rows in ``LICENCES.md``."""

from __future__ import annotations

from topoli.core.domain import Licence
from topoli.countries.ch.zh.wfs import TERMS_URL

ZH_OGD = Licence(
    id="zh-ogd",
    name="Kanton Zürich Open Government Data (frei nutzbar)",
    url=TERMS_URL,
    attribution="Source: Kanton Zürich, Amt für Raumentwicklung (ARE) — OGD via maps.zh.ch",
    redistribution_allowed=True,  # allowed by the terms; Topoli still fetches on demand
)

ZH_BZO = Licence(
    id="official-publication",
    name="Amtliche Sammlung der Stadt Zürich, AS 700.100 (official publication, not copyrighted per Art. 5 URG)",
    url="https://oerebdocs.zh.ch/getDoc?docid=6",
    attribution="Source: Stadt Zürich, Bau- und Zonenordnung (BZO 2016), AS 700.100, consolidated text as published on the ÖREB document server",
    redistribution_allowed=True,
)

ZH_BAUGESUCHE = Licence(
    id="opendata-swiss-open",
    name="opendata.swiss terms 'Freie Nutzung' (OPEN) — Baugesuche im Kanton Zürich, Statistisches Amt / FK OGD",
    url="https://opendata.swiss/de/dataset/baugesuche-im-kanton-zurich",
    attribution="Source: Kanton Zürich, Statistisches Amt (Fachstelle OGD) — Baugesuche im Kanton Zürich, from the Amtsblatt (Amtsblattportal API, rubric BP-ZH01)",
    redistribution_allowed=True,
)
