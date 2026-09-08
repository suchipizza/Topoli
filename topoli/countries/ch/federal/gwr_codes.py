"""GWR/RegBL code labels, per the official feature catalogue (Merkmalskatalog 4.2).

Source: https://www.housing-stat.ch/files/881-2200.pdf (Bundesamt für Statistik).
Only codes that reach the report are mapped; unknown codes are shown raw. Labels are the
catalogue's German terms with an English gloss; the report shows both via i18n later.
"""

from __future__ import annotations

GSTAT: dict[int, str] = {
    1001: "projektiert (planned)",
    1002: "bewilligt (approved)",
    1003: "im Bau (under construction)",
    1004: "bestehend (existing)",
    1005: "nicht nutzbar (not usable)",
    1007: "abgebrochen (demolished)",
    1008: "nicht realisiert (not built)",
}

GKAT: dict[int, str] = {
    1010: "Provisorische Unterkunft (temporary shelter)",
    1020: "Gebäude mit ausschliesslicher Wohnnutzung (residential only)",
    1030: "Andere Wohngebäude (residential with secondary use)",
    1040: "Gebäude mit teilweiser Wohnnutzung (partly residential)",
    1060: "Gebäude ohne Wohnnutzung (non-residential)",
    1080: "Sonderbau (special structure)",
}

GKLAS: dict[int, str] = {
    1110: "Gebäude mit einer Wohnung (single-family house)",
    1121: "Gebäude mit zwei Wohnungen (two-family house)",
    1122: "Gebäude mit drei und mehr Wohnungen (multi-family house)",
    1130: "Wohngebäude für Gemeinschaften (communal housing)",
    1211: "Hotelgebäude (hotel)",
    1212: "Andere Gebäude für kurzfristige Beherbergung (other short-stay lodging)",
    1220: "Bürogebäude (office building)",
    1230: "Gross- und Einzelhandelsgebäude (retail/wholesale)",
    1231: "Restaurants und Bars (restaurants and bars)",
    1241: "Bahnhöfe, Abfertigungsgebäude (transport buildings)",
    1242: "Garagengebäude (garage building)",
    1251: "Industriegebäude (industrial building)",
    1252: "Behälter, Silos und Lagergebäude (tanks, silos, warehouses)",
    1261: "Gebäude für Kultur- und Freizeitzwecke (culture/leisure)",
    1262: "Museen und Bibliotheken (museums, libraries)",
    1263: "Schul- und Hochschulgebäude (schools, universities)",
    1264: "Krankenhäuser (hospitals)",
    1265: "Sporthallen (sports halls)",
    1271: "Landwirtschaftliche Betriebsgebäude (agricultural)",
    1272: "Kirchen und sonstige Kultgebäude (churches, places of worship)",
    1273: "Denkmäler (monuments)",
    1274: "Sonstige Hochbauten (other buildings)",
    1275: "Andere Gebäude für die kollektive Unterkunft (other collective housing)",
    1276: "Gebäude für die Tierhaltung (livestock buildings)",
    1277: "Gebäude für den Pflanzenbau (crop buildings)",
    1278: "Andere landwirtschaftliche Gebäude (other agricultural)",
}

GBAUP: dict[int, str] = {
    8011: "vor 1919",
    8012: "1919–1945",
    8013: "1946–1960",
    8014: "1961–1970",
    8015: "1971–1980",
    8016: "1981–1985",
    8017: "1986–1990",
    8018: "1991–1995",
    8019: "1996–2000",
    8020: "2001–2005",
    8021: "2006–2010",
    8022: "2011–2015",
    8023: "nach 2015",
}

GWAERZH: dict[int, str] = {
    7400: "kein Wärmeerzeuger (no heat generator)",
    7410: "Wärmepumpe (heat pump)",
    7411: "Wärmepumpe für mehrere Gebäude (shared heat pump)",
    7420: "Thermische Solaranlage (solar thermal)",
    7421: "Thermische Solaranlage für mehrere Gebäude (shared solar thermal)",
    7430: "Heizkessel (boiler)",
    7431: "Heizkessel für mehrere Gebäude (shared boiler)",
    7432: "Heizkessel nicht kondensierend (non-condensing boiler)",
    7433: "Heizkessel nicht kondensierend, mehrere Gebäude",
    7434: "Heizkessel kondensierend (condensing boiler)",
    7435: "Heizkessel kondensierend, mehrere Gebäude",
    7436: "Ofen (stove)",
    7440: "Wärmekraftkopplungsanlage (CHP)",
    7441: "Wärmekraftkopplungsanlage für mehrere Gebäude",
    7450: "Elektrospeicher-Zentralheizung (electric storage heating)",
    7451: "Elektrospeicher-Zentralheizung, mehrere Gebäude",
    7452: "Elektro direkt (direct electric)",
    7460: "Wärmetauscher inkl. Fernwärme (heat exchanger / district heating)",
    7461: "Wärmetauscher inkl. Fernwärme, mehrere Gebäude",
    7499: "Andere (other)",
}

GENH: dict[int, str] = {
    7500: "Keine (none)",
    7501: "Luft (air)",
    7510: "Erdwärme generisch (geothermal)",
    7511: "Erdwärmesonde (borehole heat exchanger)",
    7512: "Erdregister (ground collector)",
    7513: "Wasser inkl. Grundwasser (water)",
    7520: "Gas",
    7530: "Heizöl (heating oil)",
    7540: "Holz generisch (wood)",
    7541: "Holz Stückholz (log wood)",
    7542: "Holz Pellets (pellets)",
    7543: "Holz Schnitzel (wood chips)",
    7550: "Abwärme (waste heat)",
    7560: "Elektrizität (electricity)",
    7570: "Sonne thermisch (solar thermal)",
    7580: "Fernwärme generisch (district heating)",
    7581: "Fernwärme hohe Temperatur (district heating, high temp.)",
    7582: "Fernwärme niedrige Temperatur (district heating, low temp.)",
    7598: "Unbestimmt (undetermined)",
    7599: "Andere (other)",
}


def label(table: dict[int, str], code: object) -> str | None:
    if code is None:
        return None
    try:
        value = int(code)  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return str(code)
    return f"{value} {table[value]}" if value in table else str(value)
