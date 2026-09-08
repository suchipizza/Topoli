"""Adapter contract (PRD §4.3), cache and the shared HTTP client."""

from topoli.core.adapters.base import Adapter, HealthStatus, Record, SiteContext
from topoli.core.adapters.http import (
    BudgetExceededError,
    EgressError,
    HttpClient,
    OfflineError,
    allowed_hosts,
    get_client,
    set_client,
)

__all__ = [
    "Adapter",
    "BudgetExceededError",
    "EgressError",
    "HealthStatus",
    "HttpClient",
    "OfflineError",
    "Record",
    "SiteContext",
    "allowed_hosts",
    "get_client",
    "set_client",
]
