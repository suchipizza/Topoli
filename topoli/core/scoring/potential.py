"""Development potential (PRD §3.2 step 6): a class-C estimate whose formula and inputs are shown.

    allowed_floor_area  = floor_area_ratio × parcel_area              (BZO Ausnützungsziffer)
    existing_floor_area ≈ Σ buildings ( gebf if published else gastw × garea )
                          gebf  = GWR energy reference area (heated gross floor area,
                                  ≤ gastw × garea)
                          gastw = all storeys incl. attic/basement when partly residential
                                  → upper bound
    utilisation         = existing / allowed
    headroom            = allowed − existing

Definitions and their limits are in ``docs/decisions/005-zh-density-definition.md``. Never
apartment counts, values or costs. When any input is missing (no ratio rule for the zone, no
floors/footprint for a building) the result is *undetermined* → class D downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from topoli.core.domain import Building, Parcel, Regulation

_UB = " / storeys × footprint (upper bound)"


@dataclass
class PotentialResult:
    determined: bool
    reason: str = ""
    zone_code: str = ""
    floor_area_ratio_pct: float | None = None
    parcel_area_m2: float | None = None
    allowed_floor_area_m2: float | None = None
    existing_floor_area_m2: float | None = None
    utilisation: float | None = None
    headroom_m2: float | None = None
    inputs: list[str] = field(default_factory=list)
    derivation: str = ""

    @property
    def utilisation_pct(self) -> float | None:
        return None if self.utilisation is None else round(self.utilisation * 100)


def compute_potential(
    parcel: Parcel, buildings: list[Building], regulation: Regulation | None
) -> PotentialResult:
    if regulation is None:
        return PotentialResult(False, "no regulation for this parcel")
    far = next((r for r in regulation.rules if r.key == "floor_area_ratio"), None)
    if far is None:
        return PotentialResult(
            False,
            f"zone {regulation.zone_code}: density is not set by a floor-area ratio "
            f"(unresolved: {', '.join(regulation.unresolved) or 'none'})",
            zone_code=regulation.zone_code,
        )
    if parcel.area_m2 is None:
        return PotentialResult(False, "parcel area unknown", zone_code=regulation.zone_code)
    ratio = float(far.value) / 100.0
    allowed = ratio * parcel.area_m2
    parcel_src = parcel.sources[0].dataset if parcel.sources else "parcel"
    inputs = [
        f"floor_area_ratio = {float(far.value):g} % ({far.evidence_spans[0].article}, "
        f"{regulation.source_document.dataset})",
        f"parcel_area = {parcel.area_m2:.0f} m² (cadastral outline, LV95; source {parcel_src})",
    ]
    existing = 0.0
    upper_bound = False
    for b in buildings:
        if b.floor_area_m2 is not None:
            existing += b.floor_area_m2
            inputs.append(
                f"building {b.id}: energy reference area {b.floor_area_m2:.0f} m² (GWR gebf)"
            )
            continue
        if b.floors is None or b.footprint_m2 is None:
            return PotentialResult(
                False,
                f"building {b.id} lacks floor area, floors or footprint in the register",
                zone_code=regulation.zone_code,
                floor_area_ratio_pct=float(far.value),
                parcel_area_m2=parcel.area_m2,
                allowed_floor_area_m2=round(allowed),
                inputs=inputs,
            )
        area = b.floors * b.footprint_m2
        existing += area
        upper_bound = True
        inputs.append(
            f"building {b.id}: {b.floors} storeys × {b.footprint_m2:.0f} m² footprint "
            f"= {area:.0f} m² (GWR gastw × garea; upper bound, storeys include attic/basement)"
        )
    utilisation = existing / allowed if allowed > 0 else None
    headroom = allowed - existing
    derivation = (
        f"allowed = {float(far.value):g} % × {parcel.area_m2:.0f} m² = {allowed:.0f} m²; "
        f"existing ≈ Σ energy reference area{_UB if upper_bound else ''} "
        f"= {existing:.0f} m² (heated gross floor area approximates the chargeable floor area); "
        f"utilisation = {existing:.0f} / {allowed:.0f} = {utilisation:.0%}; "
        f"headroom = {headroom:.0f} m²"
        if utilisation is not None
        else "allowed floor area is zero"
    )
    return PotentialResult(
        True,
        zone_code=regulation.zone_code,
        floor_area_ratio_pct=float(far.value),
        parcel_area_m2=parcel.area_m2,
        allowed_floor_area_m2=round(allowed),
        existing_floor_area_m2=round(existing),
        utilisation=utilisation,
        headroom_m2=round(headroom),
        inputs=inputs,
        derivation=derivation,
    )
