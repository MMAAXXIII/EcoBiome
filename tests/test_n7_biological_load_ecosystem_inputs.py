"""Targeted N7 tests for biological load, ecosystem inputs and operation history."""
from __future__ import annotations

from uuid import UUID

from backend.api import (
    AddMeasurementRequest,
    AdjustLivestockRequest,
    CreateEquipmentRequest,
    CreateLivestockRequest,
    CreateSubstrateLayerRequest,
    CreateWaterBodyRequest,
    CreateWaterSourceRequest,
    FeedingRequest,
    SetFillLevelRequest,
    TopUpRequest,
    WaterExchangeRequest,
    _load_profile,
    _project_dir,
    _project_store,
    add_equipment,
    add_livestock,
    add_measurement,
    add_substrate_layer,
    add_water_source,
    adjust_livestock,
    create_water_body,
    get_ecology,
    list_journal,
    list_measurements,
    record_feeding,
    record_top_up,
    record_water_exchange,
    set_fill_level,
)
from backend.ecology_n7 import read_operations


def _project(tmp_path, monkeypatch) -> UUID:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))
    created = create_water_body(
        CreateWaterBodyRequest(
            name="Bassin scientifique 250 L",
            type="pond",
            volume_liters=250.0,
        )
    )
    return UUID(str(created["id"]))


def test_livestock_feeding_and_hash_chained_operations(tmp_path, monkeypatch) -> None:
    project_id = _project(tmp_path, monkeypatch)

    livestock = add_livestock(
        project_id,
        CreateLivestockRequest(
            common_name="Medaka",
            scientific_name="Oryzias latipes",
            count=12,
            average_mass_g=1.8,
            life_stage="adulte",
        ),
    )
    assert livestock["count"] == 12
    assert livestock["biomass_g"] == 21.6

    profile = _load_profile(project_id)
    assert len(profile.populations) == 1
    assert profile.populations[0].population_type == "animal"
    # N4 dynamic-property guard remains respected: abundance/biomass are not topology.
    assert "biomass" not in profile.populations[0].properties_json
    assert "abundance" not in profile.populations[0].properties_json

    adjusted = adjust_livestock(
        project_id,
        str(livestock["id"]),
        AdjustLivestockRequest(delta_count=-1, reason="death", note="mortalité observée"),
    )
    assert adjusted["count"] == 11

    record_feeding(
        project_id,
        FeedingRequest(food_name="Granulés Medaka", amount_g=0.15, protein_percent=42.0),
    )
    snapshot = get_ecology(project_id)
    assert snapshot["known_livestock_biomass_g"] == 19.8
    assert snapshot["feeding_event_count"] == 1

    operations = read_operations(_project_dir(project_id), str(project_id))
    assert [event["operation_type"] for event in operations] == [
        "livestock_added",
        "livestock_death",
        "feeding",
    ]
    assert operations[0]["previous_event_sha256"] is None
    assert operations[1]["previous_event_sha256"] == operations[0]["event_sha256"]
    assert operations[2]["previous_event_sha256"] == operations[1]["event_sha256"]

    journal = list_journal()
    titles = {str(entry["title"]) for entry in journal}
    assert "Nourrissage" in titles
    assert "Mortalité enregistrée" in titles


def test_water_sources_top_up_substrate_and_extended_measurements(tmp_path, monkeypatch) -> None:
    project_id = _project(tmp_path, monkeypatch)
    set_fill_level(project_id, SetFillLevelRequest(fill_percent=80.0))

    source = add_water_source(
        project_id,
        CreateWaterSourceRequest(
            name="Eau du robinet maison",
            source_type="tap",
            temperature_c=18.5,
            ph=7.4,
            kh_dkh=8.0,
            gh_dgh=12.0,
            conductivity_us_cm=610.0,
            nitrate_mg_l=8.0,
            chloride_mg_l=35.0,
        ),
    )
    assert source["kh_dkh"] == 8.0

    top_up = record_top_up(
        project_id,
        TopUpRequest(volume_liters=20.0, water_source_id=str(source["id"])),
    )
    assert top_up["water_body"]["current_volume_liters"] == 220.0

    layer = add_substrate_layer(
        project_id,
        CreateSubstrateLayerRequest(
            material="Pouzzolane",
            thickness_cm=5.0,
            grain_min_mm=4.0,
            grain_max_mm=8.0,
        ),
    )
    assert layer["material"] == "Pouzzolane"

    add_measurement(project_id, AddMeasurementRequest(metric="temperature", value=25.0))
    add_measurement(project_id, AddMeasurementRequest(metric="ph", value=8.0))
    add_measurement(project_id, AddMeasurementRequest(metric="tan", value=1.0))
    derived = get_ecology(project_id)["derived_indicators"]
    assert isinstance(derived, dict)
    ammonia = derived["un_ionized_ammonia"]
    assert isinstance(ammonia, dict)
    assert 0 < float(ammonia["nh3_n_mg_l"]) < 1

    for metric, value in (
        ("conductivity", 610.0),
        ("chloride", 35.0),
        ("tss", 4.0),
        ("calcium", 45.0),
        ("magnesium", 12.0),
        ("salinity", 0.2),
        ("orp", 250.0),
        ("oxygen_saturation", 92.0),
        ("water_depth", 42.0),
        ("par_surface", 120.0),
        ("par_bottom", 55.0),
        ("algae_coverage", 5.0),
        ("periphyton_coverage", 15.0),
    ):
        recorded = add_measurement(
            project_id,
            AddMeasurementRequest(metric=metric, value=value),
        )
        assert recorded["metric"] == metric

    kh = add_measurement(project_id, AddMeasurementRequest(metric="kh", value=10.0))
    assert kh["unit"] == "°dKH"
    assert kh["value"] == 10.0
    measured = list_measurements(project_id)
    kh_read = next(item for item in measured if item["metric"] == "kh")
    assert abs(float(kh_read["value"]) - 10.0) < 1e-9
    kh_event = _project_store(project_id).all()[-1]
    assert kh_event.canonical_payload["quantity"]["unit"] == "mg/L"
    assert abs(
        float(kh_event.canonical_payload["quantity"]["value"]["value"]) - 178.48
    ) < 1e-9

    exchange = record_water_exchange(
        project_id,
        WaterExchangeRequest(
            removed_volume_liters=20.0,
            replacement_volume_liters=20.0,
            water_source_id=str(source["id"]),
        ),
    )
    assert exchange["composition_status"] == "profiled_local"
    assert exchange["water_source_name"] == "Eau du robinet maison"

    journal = list_journal()
    assert any(entry["title"] == "Complément d’eau après évaporation" for entry in journal)
    assert sum(entry["title"] == "Ajustement du niveau d’eau" for entry in journal) == 1


def test_extended_filter_and_lighting_metadata_are_durable(tmp_path, monkeypatch) -> None:
    project_id = _project(tmp_path, monkeypatch)
    filter_item = add_equipment(
        project_id,
        CreateEquipmentRequest(
            equipment_type="filter",
            name="Biofiltre principal",
            model="DIY 30 PPI",
            flow_lph=220.0,
            measured_flow_lph=180.0,
            filter_media="Mousse 30 PPI + pouzzolane",
            media_volume_liters=8.0,
            specific_surface_m2_per_l=350.0,
            biofilter_maturity="mature",
            tan_capacity_mg_n_day=250.0,
            inoculated=True,
        ),
    )
    assert filter_item["measured_flow_lph"] == 180.0
    assert filter_item["media_volume_liters"] == 8.0
    assert filter_item["inoculated"] is True
    assert filter_item["biofilter_maturity"] == "mature"
    assert filter_item["tan_capacity_mg_n_day"] == 250.0

    light = add_equipment(
        project_id,
        CreateEquipmentRequest(
            equipment_type="lighting",
            name="Rampe principale",
            power_watts=30.0,
            daily_runtime_hours=8.0,
            color_temperature_k=6500.0,
            par_surface_umol_m2_s=120.0,
            par_bottom_umol_m2_s=55.0,
        ),
    )
    assert light["par_surface_umol_m2_s"] == 120.0
    assert light["par_bottom_umol_m2_s"] == 55.0
