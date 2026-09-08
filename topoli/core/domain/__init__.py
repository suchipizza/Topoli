"""Country-independent domain model (spec §8, PRD §5).

Economic objects, not government agencies: ``Site`` → ``Parcel`` → ``Building`` →
``Regulation`` → ``Finding``. Every model is a pydantic v2 model so that
``evidence.json`` is the JSON dump of these objects and nothing else.
"""

from topoli.core.domain.common import (
    LANGS,
    Coordinates,
    Geometry,
    Jurisdiction,
    Lang,
    Licence,
    LocalizedText,
    StrictModel,
)
from topoli.core.domain.event import ConstructionEvent
from topoli.core.domain.evidence import EvidenceSpan, GeometryIntersection, Source
from topoli.core.domain.finding import (
    CATEGORIES,
    CLASSES,
    SEVERITIES,
    Category,
    Finding,
    FindingClass,
    Severity,
)
from topoli.core.domain.parcel import Building, Parcel
from topoli.core.domain.regulation import Regulation, Rule
from topoli.core.domain.site import Site

__all__ = [
    "CATEGORIES",
    "CLASSES",
    "LANGS",
    "SEVERITIES",
    "Building",
    "Category",
    "ConstructionEvent",
    "Coordinates",
    "EvidenceSpan",
    "Finding",
    "FindingClass",
    "Geometry",
    "GeometryIntersection",
    "Jurisdiction",
    "Lang",
    "Licence",
    "LocalizedText",
    "Parcel",
    "Regulation",
    "Rule",
    "Severity",
    "Site",
    "Source",
    "StrictModel",
]
