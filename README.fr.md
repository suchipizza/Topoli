<p align="right"><a href="README.md">English</a> · <a href="README.de.md">Deutsch</a> · <a href="README.it.md">Italiano</a></p>

# Topoli

**Intelligence de la construction, open source, pour les agents IA.**

Donnez une adresse suisse à votre IA. Elle rassemble les données officielles, vous dit ce que vous pouvez construire, ce qui pourrait vous bloquer et ce qui se passe autour — avec la preuve derrière chaque conclusion. En français, allemand, italien et anglais. Pas de compte, pas de clé API, rien n'est envoyé ailleurs qu'aux sources publiques officielles.

[![Stars](https://img.shields.io/github/stars/suchipizza/Topoli?style=flat&label=%E2%AD%90%20Star)](https://github.com/suchipizza/Topoli/stargazers) [![CI](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml/badge.svg)](https://github.com/suchipizza/Topoli/actions/workflows/ci.yml) [![Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue.svg)](LICENSE)

![Démo de 30 secondes : une adresse entre, cinq constats et le rapport sortent](docs/demo.gif)

```text
/property-audit "Rue du Rhône 14, 1204 Genève" --lang fr
```

Résultat réel, non retouché : voir les [exemples](examples/) (Zurich ×2, Genève) avec leurs rapports en 18 sections et leurs fichiers de preuves.

## Lancez-le en 3 étapes

Les étapes sont les mêmes partout ; seule l'étape 2 change selon la surface.

<!-- topoli:install:start -->
1. Ouvrez Claude (Claude.ai ou Claude Code).
2. Ajoutez la compétence : collez l'URL du dépôt ou exécutez la commande d'installation en une ligne affichée.
3. Tapez : /property-audit "<votre adresse>"
<!-- topoli:install:end -->

**Claude Code** (macOS, Linux, WSL) — l'étape 2 tient en une ligne :

```bash
curl -fsSL https://raw.githubusercontent.com/suchipizza/Topoli/main/install.sh | sh
```

Windows (PowerShell) : `irm https://raw.githubusercontent.com/suchipizza/Topoli/main/install.ps1 | iex`. Il faut Python 3.11+ et Git ; l'installateur ajoute [`uv`](https://docs.astral.sh/uv/) s'il manque, clone ce dépôt dans `~/.topoli/src` et relie la compétence dans `~/.claude/skills/`. Variante : `/plugin marketplace add suchipizza/Topoli` puis `/plugin install topoli@topoli` (la commande devient `/topoli:property-audit`).

**Claude.ai** — l'étape 2 est « importer la compétence sous Personnaliser → Compétences » (abonnements payants, exécution de code activée). En cours de validation : l'accès du bac à sable aux services géodonnées suisses. D'ici là, Claude Code est la voie sûre. [Détails →](docs/decisions/011-skill-install-paths.md)

Bloqué ? → [GitHub Discussions](https://github.com/suchipizza/Topoli/discussions).

## Essayez ces adresses

| Invite | Pourquoi c'est intéressant |
|---|---|
| `/property-audit "Rue du Rhône 14, 1204 Genève" --lang fr` | couches fédérales uniquement — à quoi ressemble un canton avant ses adaptateurs |
| `/property-audit "Badenerstrasse 171, 8003 Zürich" --lang fr` | zone de préservation du quartier, 40 demandes de permis dans un rayon de 500 m, bruit routier, ruissellement |
| `/property-audit "Freie Strasse 10, 4001 Basel" --lang fr` | vieille ville de Bâle, restrictions de droit public |
| `/property-audit "Via Nassa 5, 6900 Lugano" --lang fr` | bord du lac : crue rare, pas encore de cadastre RDPPF au Tessin |
| `/property-audit "Bundesplatz 3, 3011 Bern" --lang fr` | patrimoine : bien culturel fédéral et vieille ville UNESCO, degrés de sensibilité au bruit |

Ajoutez `--goal "je veux construire 12 appartements"` (ou *acheter*, *rénover*) pour changer l'ordre des constats.

## Ce qu'il vérifie

Dix vérifications fédérales pour toute adresse suisse — adresse, parcelle, bâtiments, étendues de crue/ruissellement/chutes de pierres, bruit routier et ferroviaire, sites pollués, restrictions de droit public (là où le canton publie son cadastre), aptitude solaire des toits, inventaires fédéraux du patrimoine, terrain — plus, pour le canton de Zurich, la zone, les règles du règlement des constructions de la Ville de Zurich avec citation des articles, une estimation du potentiel de développement, les objets protégés et les publications de chantiers dans un rayon de 500 m. Chaque ligne porte sa source, son jeu de données, l'heure de consultation et l'une des quatre classes de fiabilité : **A** fait officiel · **B** calcul · **C** estimation · **D** à faire vérifier par un professionnel.

<!-- topoli:coverage:start -->
| Canton | Couches fédérales | Profondeur cantonale | Chantiers |
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

[aidez-nous à ajouter le vôtre →](https://github.com/suchipizza/Topoli/labels/good%20first%20canton)
<!-- topoli:coverage:end -->

## Ce qu'il ne fait pas

- Jamais d'estimation de valeur, de coût ni de chance d'obtenir un permis.
- Il ne remplace ni un architecte, ni le service de l'urbanisme, ni un notaire, ni le registre foncier, ni un géomètre, un ingénieur ou un conseiller en environnement. Il vous dit quoi leur demander.
- Pas de devinette : quand une règle n'a pas d'article citable ou qu'une source est indisponible, le constat le dit (classe D) au lieu d'inventer un chiffre.
- Fonctionne sur votre machine, ne parle qu'aux sources publiques officielles ([`allowed_hosts.txt`](topoli/countries/ch/allowed_hosts.txt)), n'envoie aucune télémétrie. Le seul compteur est le clic sur le lien de partage, sur le site.

## À venir — votez sur la liste d'attente

`/nearby-construction` · `/development-potential` · `/construction-leads` · `/renovation-opportunities` — [dites-nous lequel vous manque →](https://topoli.ch/run?src=readme&lang=fr)

## Contribuer — ajoutez votre canton en 4 étapes

1. Réservez un ticket [`good first canton`](https://github.com/suchipizza/Topoli/labels/good%20first%20canton) (URL de la source, licence, champs, trois adresses de test).
2. Écrivez l'adaptateur dans `topoli/countries/ch/<canton>/` selon le protocole `Adapter` ; documentez le point d'accès et la licence dans la docstring.
3. Enregistrez les fixtures (`topoli fixtures record …`), ajoutez un test de contrat en direct et les modèles dans les quatre langues.
4. Ajoutez la ligne dans `LICENCES.md` et ouvrez la PR. Voir [CONTRIBUTING.md](CONTRIBUTING.md).

## Licences

Code : [Apache-2.0](LICENSE). Données : consultées à la demande auprès des sources officielles sous leurs propres licences, listées dans [LICENCES.md](LICENCES.md) — jamais redistribuées. Tuiles cartographiques © swisstopo. Police de la carte : Inter (SIL OFL 1.1).

Maintenu par Noémie Rakotomalala · [Impressum et confidentialité](https://topoli.ch/fr#imprint)
