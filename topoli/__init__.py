"""Topoli — open-source construction intelligence for AI agents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("topoli")
except PackageNotFoundError:  # pragma: no cover - running from a plain checkout
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
