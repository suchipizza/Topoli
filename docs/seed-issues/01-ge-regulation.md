# Geneva: zoning and regulation parsing (LCI / RDPPF)
Labels: good first canton,adapter,i18n/fr

Geneva already returns the federal layers; the cantonal depth is missing.

**Sources to start from**
- Zoning: SITG open data "Plan d'affectation du sol" (RDPPF theme *ch.Nutzungsplanung*) via the SITG ESRI REST / WFS services, and the RDPPF extract (`https://ge.ch/terecadastrews/RdppfSVC.svc/extract/json/?EGRID=`, currently answers HTTP 500 — investigate the required parameters).
- Rules: LCI (loi sur les constructions et les installations diverses, RS/GE L 5 05) — zones 1–5, indices d'utilisation du sol (IUS), gabarits (art. 18 ff.).

**Done when**: `ch/ge/zoning` returns the zone for three Geneva addresses; `ch/ge/regulation` extracts IUS and gabarit per zone with article spans; fixtures + live contract test; LICENCES row; templates in fr/de/it/en.

See CONTRIBUTING.md → *Add your canton in 4 steps* and `topoli/countries/ch/zh/` as the reference implementation.
