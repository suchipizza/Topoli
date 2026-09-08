"""Adapter contract (PRD §4.3) and the shared HTTP client."""

from topoli.core.adapters.base import Adapter, HealthStatus, Record
from topoli.core.adapters.http import BudgetExceededError, HttpClient, get_client

__all__ = ["Adapter", "BudgetExceededError", "HealthStatus", "HttpClient", "Record", "get_client"]
