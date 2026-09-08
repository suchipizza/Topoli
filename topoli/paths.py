"""Locate repo-root assets (i18n, ui, skills) both from a checkout and from an installed wheel.

In a git checkout the assets live next to the ``topoli`` package (``<repo>/i18n``).
In a built wheel they are force-included under ``topoli_data/`` next to the package (see
``pyproject.toml``).
"""

from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_DIR.parent
_WHEEL_DATA = _PACKAGE_DIR.parent / "topoli_data"


def asset_dir(name: str) -> Path:
    """Return the directory for a repo-root asset folder such as ``"i18n"`` or ``"ui"``."""
    checkout = _REPO_ROOT / name
    if checkout.is_dir():
        return checkout
    packaged = _WHEEL_DATA / name
    if packaged.is_dir():
        return packaged
    msg = f"Topoli asset folder {name!r} not found in {checkout} or {packaged}"
    raise FileNotFoundError(msg)


def repo_root() -> Path:
    """The git checkout root (only meaningful in a checkout; used by the fixture recorder)."""
    return _REPO_ROOT


def cache_dir() -> Path:
    """Local on-disk cache root (PRD §4.4). Override with ``TOPOLI_CACHE_DIR``."""
    override = os.environ.get("TOPOLI_CACHE_DIR")
    return Path(override).expanduser() if override else Path.home() / ".topoli" / "cache"
