<p align="right"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.it.md">Italiano</a></p>

# Topoli

**Open-Source-Bauintelligenz für KI-Agenten.**

Geben Sie Ihrer KI eine Schweizer Adresse. Sie sammelt amtliche Daten, sagt Ihnen, was Sie bauen können, was Sie blockieren könnte und was in der Nachbarschaft passiert — mit dem Beleg hinter jeder Aussage. Auf Deutsch, Französisch, Italienisch und Englisch. Kein Konto, kein API-Schlüssel, nichts geht an andere als amtliche öffentliche Quellen.

[![Stars](https://img.shields.io/github/stars/suchipizza/Topoli?style=flat&label=%E2%AD%90%20Star)](https://github.com/suchipizza/Topoli/stargazers) [![CI](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml/badge.svg)](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue.svg)](LICENSE)

![30-Sekunden-Demo: Adresse rein, fünf Ergebnisse und der Bericht raus](docs/demo.gif)

```text
/property-audit "Badenerstrasse 171, 8003 Zürich"
```

```text
IMMOBILIEN-CHECK — Badenerstrasse 171 8003 Zürich, Zürich

🌧  Oberflächenabfluss bei Starkregen: 14% des Grundstücks können bei Starkregen von Oberflächenwasser erreicht werden.
    Eingänge, Lichtschächte und Garagenrampen brauchen unter Umständen Schutz vor Wasser von Strasse oder Hang.

🔊  Strassenlärm: mittel (etwa 64 dB am Tag, 51 dB in der Nacht).
    Schlaf- und Wohnräume müssen unter Umständen von der Strasse abgewandt liegen oder Schallschutzfenster erhalten.

🏘  40 Baugesuche wurden in den letzten 12 Monaten im Umkreis von 500 m publiziert.
    Das Quartier verändert sich (Umbauten, Heizung und Solar, Erweiterungen, Neubauten …).

🗺  Zone: Quartiererhaltung, bis 5 Vollgeschosse und 18 m Gebäudehöhe.
    Neubauten müssen sich ins bestehende Strassenbild einfügen: geschlossene Strassenfronten, vorgegebene Bautiefe und Dachformen.

☀️  Solar: die Dächer eignen sich gut für Solarmodule (97 m² nutzbar, etwa 17 MWh pro Jahr).
    Eine Solaranlage lohnt sich wahrscheinlich; viele Kantone fördern sie.

Verlässlichkeit: 2 amtliche Fakten · 3 Berechnungen · 0 Schätzungen · 0 brauchen eine Fachperson
Nächster Schritt: bestellen Sie bei der kantonalen Fachstelle Naturgefahren (ZH) den Auszug aus der kantonalen Gefahrenkarte für dieses Grundstück
```

Echte, unbearbeitete Ausgabe — siehe die [Beispiele](examples/) (Zürich ×2, Genf) mit ihren 18-teiligen Berichten und Belegdateien.

## In 3 Schritten ausprobieren

Die Schritte sind überall gleich; nur Schritt 2 hängt von der Oberfläche ab.

<!-- topoli:install:start -->
1. Öffnen Sie Claude (Claude.ai oder Claude Code).
2. Fügen Sie den Skill hinzu: Repository-URL einfügen oder den gezeigten Einzeiler ausführen.
3. Tippen Sie: /property-audit "<Ihre Adresse>"
<!-- topoli:install:end -->

**Claude Code** (macOS, Linux, WSL) — Schritt 2 ist ein Einzeiler:

```bash
curl -fsSL https://raw.githubusercontent.com/suchipizza/Topoli/main/install.sh | sh
```

Windows (PowerShell): `irm https://raw.githubusercontent.com/suchipizza/Topoli/main/install.ps1 | iex`. Braucht Python 3.11+ und Git; der Installer richtet [`uv`](https://docs.astral.sh/uv/) ein, falls es fehlt, klont dieses Repository nach `~/.topoli/src` und verknüpft den Skill in `~/.claude/skills/`. Alternative: `/plugin marketplace add suchipizza/Topoli`, dann `/plugin install topoli@topoli` (der Befehl heisst dann `/topoli:property-audit`).

**Claude.ai** — Schritt 2 ist «Skill unter Anpassen → Skills hochladen» (bezahlte Pläne, Code-Ausführung aktiviert). In Prüfung: ob die Sandbox die Schweizer Geodatendienste erreicht. Bis dahin ist Claude Code der sichere Weg. [Details →](docs/decisions/011-skill-install-paths.md)

Hängen geblieben? → [GitHub Discussions](https://github.com/suchipizza/Topoli/discussions).

## Diese Adressen ausprobieren

| Eingabe | Warum spannend |
|---|---|
| `/property-audit "Badenerstrasse 171, 8003 Zürich"` | Quartiererhaltungszone, 40 Baugesuche im Umkreis von 500 m, Strassenlärm, Oberflächenabfluss |
| `/property-audit "Rue du Rhône 14, 1204 Genève" --lang de` | nur Bundesebenen — so sieht ein Kanton aus, bevor seine Adapter existieren |
| `/property-audit "Freie Strasse 10, 4001 Basel"` | Basler Altstadt, öffentlich-rechtliche Eigentumsbeschränkungen |
| `/property-audit "Via Nassa 5, 6900 Lugano" --lang de` | Seeufer: seltenes Hochwasser, im Tessin noch kein ÖREB-Kataster |
| `/property-audit "Bundesplatz 3, 3011 Bern"` | Denkmalschutz: Kulturgut des Bundes und UNESCO-Altstadt, Lärmempfindlichkeitsstufen |

Mit `--goal "Ich will 12 Wohnungen bauen"` (oder *kaufen*, *sanieren*) ändert sich, welche Ergebnisse zuerst kommen.

## Was geprüft wird

Zehn Bundesprüfungen für jede Schweizer Adresse — Adresse, Grundstück, Gebäude, Hochwasser-/Abfluss-/Steinschlagflächen, Strassen- und Bahnlärm, belastete Standorte, öffentlich-rechtliche Eigentumsbeschränkungen (wo der Kanton seinen Kataster publiziert), Solareignung der Dächer, Bundesinventare zum Denkmalschutz, Gelände — plus für den Kanton Zürich die Zone, die Regeln der Bauordnung der Stadt Zürich mit Artikelzitaten, eine Schätzung des Entwicklungspotenzials, Schutzobjekte und Baupublikationen im Umkreis von 500 m. Jede Zeile trägt Quelle, Datensatz, Abrufzeitpunkt und eine von vier Verlässlichkeitsklassen: **A** amtlicher Fakt · **B** Berechnung · **C** Schätzung · **D** braucht eine Fachperson.

<!-- topoli:coverage:start -->
| Kanton | Bundesebenen | Kantonale Tiefe | Bautätigkeit |
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

[helfen Sie mit, Ihren hinzuzufügen →](https://github.com/suchipizza/Topoli/labels/good%20first%20canton)
<!-- topoli:coverage:end -->

## Was es nicht tut

- Nie Bewertungen, Kostenschätzungen oder Bewilligungschancen.
- Es ersetzt weder Architektin noch Bauamt, Notar, Grundbuch, Geometer, Ingenieurin oder Umweltberatung. Es sagt Ihnen, was Sie diese fragen sollen.
- Kein Raten: hat eine Regel keinen zitierbaren Artikel oder ist eine Quelle nicht erreichbar, sagt das Ergebnis das (Klasse D), statt eine Zahl zu erfinden.
- Läuft auf Ihrem Rechner, spricht nur mit amtlichen öffentlichen Quellen ([`allowed_hosts.txt`](topoli/countries/ch/allowed_hosts.txt)), sendet keine Telemetrie. Der einzige Zähler ist der Klick auf den Teilen-Link, auf der Website.

## Als Nächstes — abstimmen auf der Warteliste

`/nearby-construction` · `/development-potential` · `/construction-leads` · `/renovation-opportunities` — [sagen Sie uns, was Ihnen fehlt →](https://topoli.ch/run?src=readme&lang=de)

## Mitmachen — Ihren Kanton in 4 Schritten hinzufügen

1. Übernehmen Sie ein [`good first canton`](https://github.com/suchipizza/Topoli/labels/good%20first%20canton)-Issue (Quellen-URL, Lizenz, Felder, drei Testadressen).
2. Schreiben Sie den Adapter in `topoli/countries/ch/<kanton>/` nach dem `Adapter`-Protokoll; Endpunkt und Lizenz gehören in den Docstring.
3. Zeichnen Sie Fixtures auf (`topoli fixtures record …`), ergänzen Sie einen Live-Vertragstest und die Vorlagen in allen vier Sprachen.
4. Fügen Sie die Zeile in `LICENCES.md` hinzu und eröffnen Sie den PR. Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## Lizenzen

Code: [Apache-2.0](LICENSE). Daten: bei Bedarf von amtlichen Quellen unter deren Lizenzen abgerufen, aufgeführt in [LICENCES.md](LICENCES.md) — nie weiterverbreitet. Kartenkacheln © swisstopo. Schrift der Karte: Inter (SIL OFL 1.1).

Betreut von Noémie Rakotomalala · [Impressum und Datenschutz](https://topoli.ch/de#imprint)
