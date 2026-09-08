"""Adapter contract (PRD §4.3), cache and the shared HTTP client."""

from topoli.core.adapters.base import Adapter, HealthStatus, Record
from topoli.core.adapters.http import (
    BudgetExceededError,
    HttpClient,
    OfflineError,
    get_client,
    set_client,
)

__all__ = [
    "Adapter",
    "BudgetExceededError",
    "HealthStatus",
    "HttpClient",
    "OfflineError",
    "Record",
    "get_client",
    "set_client",
]
