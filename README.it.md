<p align="right"><a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.de.md">Deutsch</a></p>

# Topoli

**Intelligenza edilizia open source per agenti IA.**

Dia alla sua IA un indirizzo svizzero. Raccoglie i dati ufficiali, le dice che cosa può costruire, che cosa potrebbe bloccarla e che cosa succede nei dintorni — con la prova dietro ogni conclusione. In italiano, tedesco, francese e inglese. Nessun account, nessuna chiave API, nulla viene inviato altrove che alle fonti pubbliche ufficiali.

[![Stars](https://img.shields.io/github/stars/suchipizza/Topoli?style=flat&label=%E2%AD%90%20Star)](https://github.com/suchipizza/Topoli/stargazers) [![CI](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml/badge.svg)](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue.svg)](LICENSE)

![Demo di 30 secondi: un indirizzo entra, cinque risultati e il rapporto escono](docs/demo.gif)

```text
/property-audit "Via Nassa 5, 6900 Lugano" --lang it
```

Output reale, non ritoccato: vedi gli [esempi](examples/) (Zurigo ×2, Ginevra) con i rapporti in 18 sezioni e i file di prova.

## Lo provi in 3 passi

I passi sono gli stessi ovunque; solo il passo 2 dipende dalla superficie.

<!-- topoli:install:start -->
1. Apra Claude (Claude.ai o Claude Code).
2. Aggiunga la skill: incolli l'URL del repository o esegua il comando di installazione in una riga mostrato.
3. Scriva: /property-audit "<il suo indirizzo>"
<!-- topoli:install:end -->

**Claude Code** (macOS, Linux, WSL) — il passo 2 è una riga:

```bash
curl -fsSL https://raw.githubusercontent.com/suchipizza/Topoli/main/install.sh | sh
```

Windows (PowerShell): `irm https://raw.githubusercontent.com/suchipizza/Topoli/main/install.ps1 | iex`. Servono Python 3.11+ e Git; l'installatore aggiunge [`uv`](https://docs.astral.sh/uv/) se manca, clona questo repository in `~/.topoli/src` e collega la skill in `~/.claude/skills/`. Alternativa: `/plugin marketplace add suchipizza/Topoli` e poi `/plugin install topoli@topoli` (il comando diventa `/topoli:property-audit`).

**Claude.ai** — il passo 2 è «caricare la skill sotto Personalizza → Skill» (piani a pagamento, esecuzione di codice attiva). In fase di verifica: se la sandbox raggiunge i servizi geodati svizzeri. Fino ad allora Claude Code è la via sicura. [Dettagli →](docs/decisions/011-skill-install-paths.md)

Bloccato? → [GitHub Discussions](https://github.com/suchipizza/Topoli/discussions).

## Provi questi indirizzi

| Comando | Perché è interessante |
|---|---|
| `/property-audit "Via Nassa 5, 6900 Lugano" --lang it` | lungolago: piena rara, in Ticino non c'è ancora il catasto RDPP |
| `/property-audit "Badenerstrasse 171, 8003 Zürich" --lang it` | zona di conservazione del quartiere, 40 domande di costruzione entro 500 m, rumore stradale, ruscellamento |
| `/property-audit "Rue du Rhône 14, 1204 Genève" --lang it` | solo livelli federali — com'è un cantone prima dei suoi adattatori |
| `/property-audit "Freie Strasse 10, 4001 Basel" --lang it` | centro storico di Basilea, restrizioni di diritto pubblico |
| `/property-audit "Bundesplatz 3, 3011 Bern" --lang it` | beni culturali: bene federale e centro storico UNESCO, gradi di sensibilità al rumore |

Aggiunga `--goal "voglio costruire 12 appartamenti"` (o *comprare*, *ristrutturare*) per cambiare quali risultati vengono prima.

## Che cosa verifica

Dieci verifiche federali per ogni indirizzo svizzero — indirizzo, fondo, edifici, aree di piena/ruscellamento/caduta massi, rumore stradale e ferroviario, siti inquinati, restrizioni di diritto pubblico (dove il cantone pubblica il catasto), idoneità solare dei tetti, inventari federali dei beni culturali, terreno — e in più, per il Canton Zurigo, la zona, le regole del regolamento edilizio della Città di Zurigo con citazione degli articoli, una stima del potenziale di sviluppo, gli oggetti protetti e le pubblicazioni edilizie entro 500 m. Ogni riga porta fonte, set di dati, data di consultazione e una delle quattro classi di affidabilità: **A** fatto ufficiale · **B** calcolo · **C** stima · **D** da far verificare a un professionista.

<!-- topoli:coverage:start -->
| Cantone | Livelli federali | Profondità cantonale | Cantieri |
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

[aiutaci ad aggiungere il tuo →](https://github.com/suchipizza/Topoli/labels/good%20first%20canton)
<!-- topoli:coverage:end -->

## Che cosa non fa

- Mai valutazioni, stime di costo o probabilità di ottenere una licenza.
- Non sostituisce un architetto, l'ufficio tecnico, un notaio, il registro fondiario, un geometra, un ingegnere o un consulente ambientale. Le dice che cosa chiedere loro.
- Niente supposizioni: quando una regola non ha un articolo citabile o una fonte non è disponibile, il risultato lo dice (classe D) invece di inventare un numero.
- Funziona sul suo computer, parla solo con fonti pubbliche ufficiali ([`allowed_hosts.txt`](topoli/countries/ch/allowed_hosts.txt)), non invia telemetria. L'unico contatore è il clic sul link di condivisione, sul sito.

## Prossimamente — voti nella lista d'attesa

`/nearby-construction` · `/development-potential` · `/construction-leads` · `/renovation-opportunities` — [ci dica quale le manca →](https://topoli.ch/run?src=readme&lang=it)

## Contribuire — aggiunga il suo cantone in 4 passi

1. Prenda in carico un ticket [`good first canton`](https://github.com/suchipizza/Topoli/labels/good%20first%20canton) (URL della fonte, licenza, campi, tre indirizzi di prova).
2. Scriva l'adattatore in `topoli/countries/ch/<cantone>/` secondo il protocollo `Adapter`; documenti endpoint e licenza nella docstring.
3. Registri le fixture (`topoli fixtures record …`), aggiunga un test di contratto live e i modelli nelle quattro lingue.
4. Aggiunga la riga in `LICENCES.md` e apra la PR. Vedi [CONTRIBUTING.md](CONTRIBUTING.md).

## Licenze

Codice: [Apache-2.0](LICENSE). Dati: consultati su richiesta da fonti ufficiali con le loro licenze, elencate in [LICENCES.md](LICENCES.md) — mai ridistribuiti. Tasselli della mappa © swisstopo. Font della scheda: Inter (SIL OFL 1.1).

Curato da Noémie Rakotomalala · [Impressum e privacy](https://topoli.ch/it#imprint)
