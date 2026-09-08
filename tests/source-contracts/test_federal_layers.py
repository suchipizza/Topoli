"""Live contract tests (nightly): each registered layer adapter's health(), federal + cantonal."""

from __future__ import annotations

import pytest

from topoli.core.adapters.registry import all_specs

pytestmark = pytest.mark.live


@pytest.mark.parametrize(
    "spec", [*all_specs("federal"), *all_specs("cantonal")], ids=lambda s: s.id
)
def test_adapter_health(spec, request: pytest.FixtureRequest) -> None:  # type: ignore[no-untyped-def]
    request.node.add_marker(pytest.mark.adapter(spec.id))
    status = spec.adapter.health()
    assert status.ok, f"{spec.id}: {status.detail}"
