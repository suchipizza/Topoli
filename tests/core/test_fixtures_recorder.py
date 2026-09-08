from __future__ import annotations

from pathlib import Path

from topoli.core.adapters.fixtures import list_fixtures, seed_cache, slugify


def test_slugify() -> None:
    assert slugify("Badenerstrasse 171, 8003 Zürich") == "badenerstrasse-171-8003-zurich"
    assert slugify("Rue du Rhône 14, 1204 Genève") == "rue-du-rhone-14-1204-geneve"
    assert slugify("   ") == "site"


def test_recorded_fixtures_have_meta_and_seed(tmp_path: Path) -> None:
    metas = list_fixtures()
    assert metas, "no fixtures recorded"
    for meta in metas:
        for key in ("adapter_id", "address", "recorded_at", "topoli_version", "requests"):
            assert key in meta, meta["folder"]
    spine = [m for m in metas if m["adapter_id"] == "ch/federal/buildings"]
    assert len(spine) >= 5, "WO-02 requires five recorded sites"
    root = Path(__file__).resolve().parents[1] / "fixtures"
    n = seed_cache(tmp_path, root / spine[0]["folder"])
    assert n == len(spine[0]["requests"])
    assert (tmp_path / "ch" / "federal" / "buildings").is_dir()
