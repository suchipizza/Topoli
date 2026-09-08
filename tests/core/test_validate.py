from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from topoli.core.domain import EvidenceSpan, Finding, LocalizedText, Source
from topoli.core.evidence import merge_conflicting, validate, validate_all


def test_complete_class_a_is_unchanged(make_finding: Callable[..., Finding]) -> None:
    f = make_finding()
    assert validate(f) is f


@pytest.mark.parametrize("cls", ["A", "B"])
@pytest.mark.parametrize("missing", ["url", "retrieved_at"])
def test_missing_source_downgrades_to_d(
    make_finding: Callable[..., Finding],
    complete_source: Source,
    cls: str,
    missing: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    f = make_finding(**{"class": cls, "source": complete_source.model_copy(update={missing: None})})
    with caplog.at_level(logging.WARNING, logger="topoli.evidence"):
        out = validate(f)
    assert out.cls == "D"
    assert f.cls == cls, "input must not be mutated"
    assert "downgraded:missing_source" in out.validation_notes[0]
    assert "official source" in out.caveat.en
    assert out.caveat.fr  # rendered in every language (EN fallback until WO-07)
    record = [r for r in caplog.records if r.name == "topoli.evidence"][-1]
    assert record.getMessage() == "finding.downgraded"
    assert vars(record)["reason"] == "missing_source"
    assert vars(record)["from_class"] == cls


@pytest.mark.parametrize("cls", ["C", "D"])
def test_estimates_are_not_downgraded_for_missing_url(
    make_finding: Callable[..., Finding], complete_source: Source, cls: str
) -> None:
    f = make_finding(**{"class": cls, "source": complete_source.model_copy(update={"url": None})})
    assert validate(f).cls == cls


def test_rule_without_span_downgrades(make_finding: Callable[..., Finding]) -> None:
    f = make_finding(**{"class": "A", "category": "zoning", "rule_ref": "ausnuetzungsziffer"})
    out = validate(f)
    assert out.cls == "D"
    assert "ausnuetzungsziffer" in out.caveat.en
    with_span = make_finding(
        **{
            "class": "A",
            "category": "zoning",
            "rule_ref": "ausnuetzungsziffer",
            "evidence_spans": [EvidenceSpan(document="BZO", article="Art. 5", text="AZ 90 %")],
        }
    )
    assert validate(with_span).cls == "A"


def test_conflicting_sources_lists_both(
    make_finding: Callable[..., Finding], complete_source: Source
) -> None:
    other_source = complete_source.model_copy(
        update={
            "adapter_id": "ch/zh/hazards",
            "authority": "Kanton Zürich",
            "dataset": "Gefahrenkarte ZH",
        }
    )
    a = make_finding()
    b = make_finding(id="hazard.flood.zh", source=other_source, **{"class": "A"})
    merged = merge_conflicting(a, b)
    assert merged.cls == "D"
    assert merged.source == a.source
    assert merged.alternatives == [other_source]
    assert "Kanton Zürich" in merged.caveat.en
    assert "BAFU" in merged.caveat.en


def test_stale_marker_keeps_class_and_adds_caveat(
    make_finding: Callable[..., Finding], complete_source: Source
) -> None:
    stale = complete_source.model_copy(update={"stale_as_of": datetime(2026, 8, 1, tzinfo=UTC)})
    f = make_finding(source=stale, caveat=LocalizedText.same("Existing caveat."))
    out = validate(f)
    assert out.cls == "A"
    assert "1 August 2026" in out.caveat.en
    assert "01.08.2026" in out.caveat.de
    assert out.caveat.en.startswith("Existing caveat.")
    # idempotent
    assert validate(out) == out


def test_validate_all_preserves_order(
    make_finding: Callable[..., Finding], complete_source: Source
) -> None:
    good = make_finding(id="one")
    bad = make_finding(id="two", source=complete_source.model_copy(update={"url": None}))
    out = validate_all([good, bad])
    assert [f.id for f in out] == ["one", "two"]
    assert [f.cls for f in out] == ["A", "D"]
