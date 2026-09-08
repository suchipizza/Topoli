"""Construction events: parsing units and replay on a dense, a quiet and a Winterthur site."""

from __future__ import annotations

import base64
import gzip
from collections.abc import Callable
from datetime import UTC, date, datetime

from topoli.core.adapters import Record, get_client
from topoli.core.adapters.base import SiteContext
from topoli.core.domain import Coordinates, Jurisdiction, Site
from topoli.core.pipeline import LayerRun, resolve_spine, run_events
from topoli.core.scoring.activity import summarize, timeline
from topoli.countries.ch.zh.construction_events import (
    COLUMNS,
    ConstructionEventsAdapter,
    classify,
    parcel_tokens,
    portal_page,
    reduce_points,
)


def test_parcel_tokens() -> None:
    assert parcel_tokens("AU6979") == ["AU6979"]
    assert parcel_tokens("3147, 3148, 3150 und 4620") == ["3147", "3148", "3150", "4620"]
    assert parcel_tokens("SE3232; SE3667") == ["SE3232", "SE3667"]
    assert parcel_tokens("") == []


def test_classify() -> None:
    assert classify("Neubau Mehrfamilienhaus mit Tiefgarage") == "new_building"
    assert classify("Abbruch und Ersatzneubau") == "demolition"  # demolition rule wins first
    assert classify("Aufstockung um ein Geschoss") == "extension"
    assert classify("Energetische Dachsanierung") == "conversion"
    assert classify("Erstellung Luft-/Wasser-Wärmepumpenanlage") == "energy"
    assert classify("Reklameanlage") == "signage"
    assert classify("Mobilfunkantenne") == "antenna"
    assert classify("Zaun") == "other"


def _csv_record(rows: list[dict[str, str]], retrieved: datetime) -> Record:
    import csv
    import io

    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(COLUMNS))
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in COLUMNS})
    blob = base64.b64encode(gzip.compress(out.getvalue().encode())).decode()
    return Record(
        adapter_id="ch/zh/construction_events",
        url="https://daten.statistik.zh.ch/x.csv",
        retrieved_at=retrieved,
        payload={"csv_gzip_base64": blob, "rows": len(rows)},
    )


def test_events_matching_and_window() -> None:
    site = Site(
        id="261-AU6979",
        input_address="x",
        address="x",
        coordinates=Coordinates(lon=8.52, lat=47.37, east=2681700, north=1247600),
        jurisdiction=Jurisdiction(country="CH", canton="ZH", municipality="Zürich", bfs_number=261),
        resolve_confidence=1,
        lang_default="de",
    )
    ctx = SiteContext(site=site)
    retrieved = datetime(2026, 9, 8, tzinfo=UTC)
    rows = [
        {
            "id": "a",
            "publicationNumber": "BP-1",
            "publicationDate": "2026-08-01",
            "entryDeadline": "2026-08-21",
            "bfs_nr": "261",
            "projectDescription": "Neubau",
            "districtCadastre_relation_cadastre_raw": "AU1",
            "projectLocation_address_street": "Badenerstrasse",
            "projectLocation_address_houseNumber": "1",
            "buildingContractor_legalEntity_selectType": "person",
        },
        {
            "id": "a",
            "publicationNumber": "BP-1",
            "publicationDate": "2026-08-01",
            "entryDeadline": "2026-08-21",
            "bfs_nr": "261",
            "projectDescription": "Neubau",
            "districtCadastre_relation_cadastre_raw": "AU2",
            "projectLocation_address_street": "Badenerstrasse",
            "projectLocation_address_houseNumber": "3",
            "buildingContractor_legalEntity_selectType": "person",
        },
        {
            "id": "b",
            "publicationNumber": "BP-2",
            "publicationDate": "2025-01-01",
            "entryDeadline": "2025-01-21",
            "bfs_nr": "261",
            "projectDescription": "Umbau",
            "districtCadastre_relation_cadastre_raw": "AU1",
        },
        {
            "id": "c",
            "publicationNumber": "BP-3",
            "publicationDate": "2026-09-01",
            "entryDeadline": "2026-09-21",
            "bfs_nr": "230",
            "projectDescription": "Umbau",
            "districtCadastre_relation_cadastre_raw": "AU1",
        },
        {
            "id": "d",
            "publicationNumber": "BP-4",
            "publicationDate": "2026-09-01",
            "entryDeadline": "2026-09-21",
            "bfs_nr": "261",
            "projectDescription": "Umbau",
            "districtCadastre_relation_cadastre_raw": "",
        },
        {
            "id": "e",
            "publicationNumber": "BP-5",
            "publicationDate": "2026-09-01",
            "entryDeadline": "2026-09-21",
            "bfs_nr": "261",
            "projectDescription": "Abbruch",
            "districtCadastre_relation_cadastre_raw": "AU9",
            "buildingContractor_legalEntity_selectType": "company",
            "buildingContractor_company_legalForm_de": "AG",
            "buildingContractor_company_address_town": "Zug",
        },
    ]
    points = Record(
        adapter_id="ch/zh/construction_events",
        url="https://maps.zh.ch/wfs/x",
        retrieved_at=retrieved,
        payload={
            "points": [
                ["AU1", 261, 2681750, 1247600],
                ["AU2", 261, 2681710, 1247600],
                ["AU9", 261, 2682500, 1247600],
            ]
        },
    )
    adapter = ConstructionEventsAdapter()
    events, stats = adapter.events([_csv_record(rows, retrieved), points], ctx)
    assert [e.id for e in events] == ["BP-1"], [e.id for e in events]
    e = events[0]
    assert e.parcels == ["AU2"] and e.distance_m == 10.0, "nearest parcel of the publication wins"
    assert e.type == "new_building" and e.applicant == "Privatperson"
    assert e.status == "published" and e.publication_date == date(2026, 8, 1)
    assert (e.sources[0].url or "").endswith("/publications/a")
    assert portal_page(e).endswith("/detail/a")
    assert stats == {
        "rows_municipality": 4,
        "without_parcel_number": 1,
        "as_of": "2026-09-08",
        "since": "2025-09-08",
    }
    # AU9 is 800 m away → excluded; b is older than 12 months; c is Winterthur
    finding = adapter.to_findings([_csv_record(rows, retrieved), points], ctx)[0]
    assert finding.template_key == "activity.n" and finding.slots["n"] == "1" and finding.cls == "B"
    assert "1 publications without a parcel number" in (finding.derivation or "")
    empty = adapter.to_findings([_csv_record([], retrieved), points], ctx)[0]
    assert empty.template_key == "activity.none"


def test_reduce_points_and_summary() -> None:
    raw = (
        b'{"features":[{"properties":{"nummer":"AU1","bfsnr":261},'
        b'"geometry":{"coordinates":[1.0,2.0]}},'
        b'{"properties":{"nummer":null},"geometry":{"coordinates":[3,4]}}]}'
    )
    assert reduce_points(raw) == {"points": [["AU1", 261, 1.0, 2.0]], "count": 1}
    assert summarize([], radius_m=500, since=None).count == 0
    assert timeline([]) == []


def _run(replay: Callable[[str, str], int], slug: str, address: str) -> LayerRun:
    replay("ch/zh/construction_events", slug)
    get_client().reset()
    ctx, _, _ = resolve_spine(address)
    return run_events(LayerRun(ctx=ctx))


def test_dense_site(replay: Callable[[str, str], int]) -> None:
    run = _run(replay, "zurich-badenerstrasse-171", "Badenerstrasse 171, 8003 Zürich")
    assert get_client().calls == 0
    cov = next(c for c in run.coverage if c.adapter_id == "ch/zh/construction_events")
    assert cov.status == "ok"
    assert len(run.events) >= 10, "Aussersihl is busy"
    assert all(e.distance_m is not None and e.distance_m <= 500 for e in run.events)
    assert all(
        (e.sources[0].url or "").startswith("https://www.amtsblattportal.ch/api/v1/publications/")
        for e in run.events
    )
    assert run.events == timeline(run.events), "newest first, deduplicated"
    finding = next(f for f in run.findings if f.id == "activity.nearby")
    assert finding.template_key == "activity.n" and int(finding.slots["n"]) == len(run.events)


def test_quiet_edge_of_city(replay: Callable[[str, str], int]) -> None:
    run = _run(replay, "zurich-witikonerstrasse-250", "Witikonerstrasse 250, 8053 Zürich")
    finding = next(f for f in run.findings if f.id == "activity.nearby")
    assert len(run.events) < 15
    assert finding.template_key in ("activity.n", "activity.none")


def test_winterthur_is_covered_by_the_cantonal_register(replay: Callable[[str, str], int]) -> None:
    run = _run(replay, "winterthur-technikumstrasse-9", "Technikumstrasse 9, 8400 Winterthur")
    cov = next(c for c in run.coverage if c.adapter_id == "ch/zh/construction_events")
    assert cov.status == "ok"
    assert all(e.location and e.location.east > 2_690_000 for e in run.events)
