"""Targeted N6 tests for the local application / Collector UI bridge."""

from __future__ import annotations

from uuid import UUID

from backend.api import (
    AddMeasurementRequest,
    CollectorAcquireRequest,
    CreateWaterBodyRequest,
    _collector_database_path,
    _load_profile,
    _project_store,
    add_measurement,
    collector_acquire,
    collector_status,
    create_water_body,
    list_journal,
    list_measurements,
    list_water_bodies,
)


def test_local_project_creation_and_n5_measurement_round_trip(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))

    created = create_water_body(
        CreateWaterBodyRequest(
            name="Bassin test 250 L",
            type="pond",
            volume_liters=250.0,
        )
    )

    project_id = UUID(str(created["id"]))
    assert created["name"] == "Bassin test 250 L"
    assert created["type"] == "pond"
    assert created["volume_liters"] == 250.0
    assert created["status"] == "unknown"

    profile = _load_profile(project_id)
    assert profile.id == str(project_id)
    assert profile.profile_kind == "pond"
    assert profile.label == "Bassin test 250 L"

    initial_events = _project_store(project_id).all()
    assert len(initial_events) == 1
    assert (
        initial_events[0].canonical_payload["quantity"]["variable_id"]
        == "hydrology.water_volume"
    )

    measurement = add_measurement(
        project_id,
        AddMeasurementRequest(
            metric="temperature",
            value=22.4,
            uncertainty=0.2,
        ),
    )
    assert measurement["metric"] == "temperature"
    assert measurement["value"] == 22.4
    assert measurement["unit"] == "°C"

    measurements = list_measurements(project_id)
    assert len(measurements) == 1
    assert measurements[0]["metric"] == "temperature"
    assert measurements[0]["value"] == 22.4

    events = _project_store(project_id).all()
    assert len(events) == 2
    payload = events[-1].canonical_payload
    assert payload["quantity"]["variable_id"] == "water.temperature"
    assert payload["measurement_uncertainty"] == {
        "type": "decimal",
        "value": "0.2",
    }

    projects = list_water_bodies()
    assert len(projects) == 1
    assert projects[0]["id"] == str(project_id)

    journal = list_journal()
    assert len(journal) == 2
    assert all("n5" in entry["tags"] for entry in journal)


def test_collector_bridge_acquires_local_text_without_network(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))

    source = tmp_path / "source.txt"
    source.write_text(
        "La nitrification transforme des composés azotés dans un système "
        "aquatique. Cette phrase sert uniquement au smoke test Collector.",
        encoding="utf-8",
    )

    result = collector_acquire(
        CollectorAcquireRequest(
            source=str(source),
            language="fr",
            languages=["fr"],
        )
    )

    assert result["adapter"]["name"] == "local-file"
    assert result["job"]["status"] == "succeeded"
    assert result["source"]["title"] == "source.txt"
    assert result["representations"]
    assert _collector_database_path().is_file()

    status = collector_status()
    assert int(status["sources"]) >= 1
