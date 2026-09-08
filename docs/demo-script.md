# 30-second demo GIF — script

Recorded by Noémie with a terminal recorder (e.g. `asciinema` + `agg`, or a screen recording of Claude Code). `topoli demo` replays a recorded Zürich audit with realistic timing so the recording needs no network and never shows a degraded source.

**Setup**: Claude Code open in an empty folder, font ≥ 16 pt, window 100×32, light theme. Run `uv run topoli demo --lang de` (or type the prompt in Claude Code with the skill installed).

| t (s) | On screen |
|---|---|
| 0–3 | Prompt typed: `/property-audit "Badenerstrasse 171, 8003 Zürich"` (or in DE: *Was kann ich an der Badenerstrasse 171 in Zürich bauen?*) |
| 3–9 | Progress lines appear one by one: ✓ Adresse gefunden · ✓ Grundstück AU6979 gefunden · ✓ 3 Gebäude gefunden · ✓ 7 Bundesebenen geprüft · ✓ Zonenvorschrift gelesen · ✓ Baupublikationen … durchsucht |
| 9–20 | Layer 0 prints: header, five findings (runoff, road noise, 40 building applications, zone, solar), confidence line, next step |
| 20–26 | `▸ Vollständigen Bericht öffnen: ./reports/zurich-AU6979/index.html` — click/open: the report with the five cards and the map |
| 26–30 | Language switcher → Français; end on the card image (`card.png`) |

Keep it under 30 s; cut the terminal after the next-step line. Export as GIF ≤ 5 MB, 1200 px wide, save as `docs/demo.gif` (linked from the READMEs).
