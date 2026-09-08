"""``ch/federal/hazards`` — federal natural-hazard rasters intersected with the parcel.

The cantonal hazard maps (Gefahrenkarten) are **not** published as queryable layers on
geo.admin.ch; they reach the report through the ÖREB extract where a canton has introduced it.
The federal, nation-wide rasters used here (all BAFU, WMS ``GetMap`` masked by the parcel
outline, see :mod:`wms`):

* ``ch.bafu.aquaprotect_100`` / ``ch.bafu.aquaprotect_500`` — Aquaprotect flood extent for a
  100-year and a 500-year event (presence).
* ``ch.bafu.gefaehrdungskarte-oberflaechenabfluss`` — surface-runoff hazard map (presence).
* ``ch.bafu.silvaprotect-sturz,ch.bafu.silvaprotect-lawinen,ch.bafu.silvaprotect-hangmuren,
  ch.bafu.silvaprotect-murgang`` — SilvaProtect-CH modelled process areas for rockfall,
  avalanche, shallow landslide and debris flow, fetched as one union image (presence).

Level mapping (documented in ``derivation``): flood — inside the 100-year extent → *medium*,
only inside the 500-year extent → *low* (residual), neither → *none*. Runoff and gravitational
processes → *low* when any pixel of the parcel is covered, else *none*. Levels are ours; the
sources publish extents, not levels. Exposure is class A (published extent), the share of the
parcel is class B (pixel count on a 64×64 grid over the parcel's bounding box).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from topoli.core.adapters import HealthStatus, Record, SiteContext
from topoli.core.domain import Finding, GeometryIntersection, Jurisdiction, Severity
from topoli.countries.ch.federal import geoadmin, wms
from topoli.countries.ch.federal.findings import make_finding, source_for
from topoli.countries.ch.federal.licences import BAFU_HAZARDS

ADAPTER_ID = "ch/federal/hazards"
LAYER_FLOOD_100 = "ch.bafu.aquaprotect_100"
LAYER_FLOOD_500 = "ch.bafu.aquaprotect_500"
LAYER_RUNOFF = "ch.bafu.gefaehrdungskarte-oberflaechenabfluss"
LAYER_GRAVITATIONAL = (
    "ch.bafu.silvaprotect-sturz,ch.bafu.silvaprotect-lawinen,"
    "ch.bafu.silvaprotect-hangmuren,ch.bafu.silvaprotect-murgang"
)
_MIN_FRACTION = 0.01  # below 1 % of the parcel we treat a raster hit as edge noise


class HazardsAdapter:
    id = ADAPTER_ID
    jurisdiction = Jurisdiction(country="CH")
    licence = BAFU_HAZARDS
    ttl = timedelta(days=30)

    def fetch(self, ctx: SiteContext) -> list[Record]:
        geom = ctx.parcel_geometry
        if geom is None:
            return []
        bbox = wms.parcel_bbox(geom)
        return [
            wms.get_map_mask(self.id, layer, bbox)
            for layer in (LAYER_FLOOD_100, LAYER_FLOOD_500, LAYER_RUNOFF, LAYER_GRAVITATIONAL)
        ]

    def to_findings(self, records: list[Record], ctx: SiteContext) -> list[Finding]:
        geom = ctx.parcel_geometry
        if geom is None or not records:
            return []
        by_layer = {geoadmin.layer_of(r): r for r in records}
        findings: list[Finding] = []

        f100 = by_layer.get(LAYER_FLOOD_100)
        f500 = by_layer.get(LAYER_FLOOD_500)
        if f100 is not None and f500 is not None:
            c100 = wms.mask_coverage(f100, geom)
            c500 = wms.mask_coverage(f500, geom)
            level: str
            sev: Severity
            inter: GeometryIntersection | None
            if c100.fraction >= _MIN_FRACTION:
                level, sev, inter, rec = "medium", "high", c100, f100
            elif c500.fraction >= _MIN_FRACTION:
                level, sev, inter, rec = "low", "medium", c500, f500
            else:
                level, sev, inter, rec = "none", "info", None, f100
            findings.append(
                self._finding(
                    "flood",
                    level,
                    sev,
                    rec,
                    inter,
                    f"Aquaprotect 100-year extent covers {c100.fraction:.0%} of the parcel, "
                    f"500-year extent {c500.fraction:.0%} (64×64 px mask over the parcel bbox); "
                    "≥1 % → exposed.",
                )
            )

        runoff = by_layer.get(LAYER_RUNOFF)
        if runoff is not None:
            cov = wms.mask_coverage(runoff, geom)
            exposed = cov.fraction >= _MIN_FRACTION
            findings.append(
                self._finding(
                    "runoff",
                    "low" if exposed else "none",
                    "medium" if exposed else "info",
                    runoff,
                    cov if exposed else None,
                    f"Surface-runoff hazard map covers {cov.fraction:.0%} of the parcel "
                    "(64×64 px mask); ≥1 % → exposed.",
                )
            )

        grav = by_layer.get(LAYER_GRAVITATIONAL)
        if grav is not None:
            cov = wms.mask_coverage(grav, geom)
            exposed = cov.fraction >= _MIN_FRACTION
            findings.append(
                self._finding(
                    "gravitational",
                    "low" if exposed else "none",
                    "medium" if exposed else "info",
                    grav,
                    cov if exposed else None,
                    f"SilvaProtect-CH process areas (rockfall, avalanche, shallow landslide, "
                    f"debris flow) cover {cov.fraction:.0%} of the parcel (64×64 px mask); "
                    "≥1 % → exposed.",
                )
            )
        return findings

    def _finding(  # noqa: PLR0917
        self,
        hazard: str,
        level: str,
        severity: Severity,
        record: Record,
        intersection: GeometryIntersection | None,
        derivation: str,
    ) -> Finding:
        source = source_for(
            self.id,
            record,
            authority="Bundesamt für Umwelt BAFU",
            dataset=geoadmin.layer_of(record),
            licence=self.licence,
        )
        slots = {"pct": f"{intersection.fraction:.0%}" if intersection else "0%"}
        return make_finding(
            finding_id=f"hazard.{hazard}",
            template_key=f"hazard.{hazard}.{level}",
            cls="B" if intersection else "A",
            severity=severity,
            category="hazard",
            source=source,
            icon={"flood": "🌊", "runoff": "🌧", "gravitational": "🏔"}[hazard],
            slots=slots,
            intersection=intersection,
            derivation=derivation,
        )

    def health(self) -> HealthStatus:
        try:
            rec = wms.get_map_mask(self.id, LAYER_FLOOD_100, (2683300, 1247600, 2683400, 1247700))
            ok = bool(rec.payload.get("png_base64"))
            detail = "GetMap returned a PNG" if ok else "empty response"
        except Exception as exc:
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        return HealthStatus(
            adapter_id=self.id, ok=ok, detail=detail, checked_at=datetime.now(tz=UTC)
        )
