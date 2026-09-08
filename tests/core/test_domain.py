from __future__ import annotations

import json
from collections.abc import Callable

import pytest
from pydantic import ValidationError

from topoli.core.domain import (
    CLASSES,
    LANGS,
    EvidenceSpan,
    Finding,
    Jurisdiction,
    LocalizedText,
    Parcel,
    Regulation,
    Rule,
    Source,
)


def test_langs_and_classes() -> None:
    assert LANGS == ("fr", "de", "it", "en")
    assert CLASSES == ("A", "B", "C", "D")


def test_localized_text_requires_all_four() -> None:
    with pytest.raises(ValidationError):
        LocalizedText(fr="a", de="b", it="c")  # type: ignore[call-arg]
    assert LocalizedText.same("x").get("it") == "x"


def test_finding_dumps_class_alias(make_finding: Callable[..., Finding]) -> None:
    f = make_finding()
    dumped = f.model_dump_json_ready()
    assert dumped["class"] == "A"
    assert "cls" not in dumped
    # round-trips through JSON
    again = Finding.model_validate(json.loads(json.dumps(dumped)))
    assert again == f


def test_finding_rejects_unknown_fields(make_finding: Callable[..., Finding]) -> None:
    with pytest.raises(ValidationError):
        make_finding(valuation_chf=1_000_000)


def test_finding_rejects_bad_class_and_category(make_finding: Callable[..., Finding]) -> None:
    with pytest.raises(ValidationError):
        make_finding(**{"class": "E"})
    with pytest.raises(ValidationError):
        make_finding(category="price")


def test_rule_requires_evidence_span(complete_source: Source) -> None:
    with pytest.raises(ValidationError):
        Rule(key="max_full_floors", value=4, evidence_spans=[], parser_version="0.1")
    rule = Rule(
        key="max_full_floors",
        value=4,
        unit="floors",
        evidence_spans=[EvidenceSpan(document="BZO", article="Art. 13", text="vier Vollgeschosse")],
        parser_version="0.1",
    )
    reg = Regulation(
        jurisdiction=Jurisdiction(country="CH", canton="ZH", municipality="Zürich"),
        zone_code="W3",
        source_document=complete_source,
        rules=[rule],
        unresolved=["grenzabstand"],
        parser_version="0.1",
    )
    assert reg.model_dump(by_alias=True)["class"] == "A"
    assert reg.jurisdiction.path == "ch/zh/zürich"


def test_parcel_slug() -> None:
    p = Parcel(local_id="AL1234", municipality="Zürich Altstetten")
    assert p.slug == "zurich-altstetten-AL1234"
    assert Parcel(local_id="7", municipality="Genève – Cité").slug == "geneve-cite-7"


def test_source_completeness(complete_source: Source) -> None:
    assert complete_source.is_complete
    assert not complete_source.model_copy(update={"url": None}).is_complete
    assert not complete_source.model_copy(update={"retrieved_at": None}).is_complete
