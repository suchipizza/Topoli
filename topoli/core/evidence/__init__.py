"""Evidence rules: validation/downgrading of findings and the audit result container."""

from topoli.core.evidence.report_model import AuditResult, CoverageEntry, CoverageStatus, Timing
from topoli.core.evidence.validate import merge_conflicting, validate, validate_all

__all__ = [
    "AuditResult",
    "CoverageEntry",
    "CoverageStatus",
    "Timing",
    "merge_conflicting",
    "validate",
    "validate_all",
]
