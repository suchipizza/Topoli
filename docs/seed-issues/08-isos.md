# Add the federal ISOS townscape inventory (not queryable via identify today)
Labels: good first issue,adapter

`ch.bak.bundesinventar-schuetzenswerte-ortsbilder` returns nothing from `identify` and WMS GetFeatureInfo fails server-side (decision 004). Investigate the ISOS GIS (gisos.bak.admin.ch) API or the STAC download, and add ISOS perimeters to `ch/federal/heritage` with a fixture for Bern old town.
