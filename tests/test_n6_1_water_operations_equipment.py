"""Targeted N6.1 tests for fill level, water exchange, and equipment inventory."""

from __future__ import annotations

from uuid import UUID

from backend.api import (
    CreateEquipmentRequest,
    CreateWaterBodyRequest,
    SetFillLevelRequest,
    WaterExchangeRequest,
    _load_profile,
    _project_store,
    add_equipment,
    create_water_body,
    delete_equipment,
    list_equipment,
    record_water_exchange,
    set_fill_level,
)


def test_fill_level_and_water_exchange_are_durable_project_events(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))

    created = create_water_body(
        CreateWaterBodyRequest(
            name="Bassin extérieur 250 L",
            type="pond",
            volume_liters=250.0,
        )
    )
    project_id = UUID(str(created["id"]))

    assert created["capacity_liters"] == 250.0
    assert created["current_volume_liters"] == 250.0
    assert created["fill_percent"] == 100.0
    assert created["volume_liters"] == 250.0

    filled = set_fill_level(
        project_id,
        SetFillLevelRequest(fill_percent=80.0),
    )
    assert filled["capacity_liters"] == 250.0
    assert filled["current_volume_liters"] == 200.0
    assert filled["fill_percent"] == 80.0

    exchange = record_water_exchange(
        project_id,
        WaterExchangeRequest(
            removed_volume_liters=50.0,
            replacement_volume_liters=20.0,
            note="smoke test",
        ),
    )
    assert exchange["previous_volume_liters"] == 200.0
    assert exchange["current_volume_liters"] == 170.0
    assert exchange["fill_percent"] == 68.0
    assert exchange["composition_status"] == "unknown"

    events = _project_store(project_id).all()
    assert [event.event_type.value for event in events] == [
        "observation",
        "observation",
        "intervention",
    ]
    intervention_payload = events[-1].canonical_payload["intervention"]
    assert intervention_payload["removed_volume"]["value"]["value"] == "50"
    assert intervention_payload["replacement_volume"]["value"]["value"] == "20"


def test_equipment_is_stored_in_n4_functional_systems(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))

    created = create_water_body(
        CreateWaterBodyRequest(
            name="Aquarium test",
            type="aquarium",
            volume_liters=100.0,
        )
    )
    project_id = UUID(str(created["id"]))

    equipment = add_equipment(
        project_id,
        CreateEquipmentRequest(
            equipment_type="water_pump",
            name="Pompe principale",
            manufacturer="Sera",
            model="110",
            power_watts=3.0,
            daily_runtime_hours=24.0,
            flow_lph=110.0,
        ),
    )

    assert equipment["equipment_type"] == "water_pump"
    assert equipment["manufacturer"] == "Sera"
    assert equipment["model"] == "110"
    assert equipment["flow_lph"] == 110.0
    assert equipment["daily_energy_wh"] == 72.0
    assert equipment["annual_energy_kwh"] == 26.28

    listed = list_equipment(project_id)
    assert listed == [equipment]

    profile = _load_profile(project_id)
    assert len(profile.functional_systems) == 1
    assert profile.functional_systems[0].id == equipment["id"]
    assert profile.functional_systems[0].system_type == "equipment_water_pump"

    deleted = delete_equipment(project_id, str(equipment["id"]))
    assert deleted == {"deleted_equipment_id": equipment["id"]}
    assert list_equipment(project_id) == []
