# Natural-language trigger checklist (WO-10 task 5)

The skill must fire from its `description` on these phrasings without the user typing `/property-audit`. Verified manually in Claude Code; record the result per row (✓ fired / ✗ did not / date / Claude Code version).

| # | Language | Phrasing | Result |
|---|---|---|---|
| 1 | de | Was kann ich an der Badenerstrasse 171 in Zürich bauen? | ☐ |
| 2 | de | Prüf mal diese Adresse: Seefeldstrasse 80, 8008 Zürich | ☐ |
| 3 | de | Gibt es Hochwasser- oder Lärmprobleme am Limmatquai 1 in Zürich? | ☐ |
| 4 | fr | Qu'est-ce que je peux construire au 14 rue du Rhône à Genève ? | ☐ |
| 5 | fr | Vérifie cette parcelle avant que j'achète : Bundesplatz 3, 3011 Berne | ☐ |
| 6 | fr | Y a-t-il des risques d'inondation ou du bruit à cette adresse : Rue de Lausanne 1, Sion ? | ☐ |
| 7 | it | Cosa posso costruire in Via Nassa 5 a Lugano? | ☐ |
| 8 | it | Controlla questo indirizzo prima che compri: Via Nassa 5, 6900 Lugano | ☐ |
| 9 | it | Ci sono rischi di alluvione o rumore a questo indirizzo a Lugano? | ☐ |
| 10 | en | What can I build at Badenerstrasse 171, Zürich? | ☐ |
| 11 | en | Check this address before I buy it: Bundesplatz 3, Bern | ☐ |
| 12 | en | Is this plot in a flood zone or a heritage area? Limmatquai 1, 8001 Zürich | ☐ |

Negative controls (must **not** fire): "What's the weather in Zürich?", "Translate 'Bauordnung' to French", "Find me a flat to rent in Geneva".
