# Report UI: map legend and hazard/noise overlays per finding
Labels: report-ui

PRD §6 asks for hazard/noise overlays toggled per finding. The frame math exists (`topoli/core/reporting/static_map.py`); add WMS overlay tiles (e.g. `ch.bafu.aquaprotect_100`, `ch.bafu.laerm-strassenlaerm_tag`) toggled from the finding cards, with a legend and keyboard access.
