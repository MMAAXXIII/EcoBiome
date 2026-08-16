"""Targeted N8 tests for progressive guidance and data completeness."""
from __future__ import annotations

from uuid import UUID

from backend.api import (
    AddMeasurementRequest,
    CreateEquipmentRequest,
    CreateLivestockRequest,
    CreatePlantRequest,
    CreateWaterBodyRequest,
    CreateWaterSourceRequest,
    FeedingRequest,
    add_equipment,
    add_livestock,
    add_measurement,
    add_plant,
    add_water_source,
    create_water_body,
    get_guidance,
    health,
    record_feeding,
)


def _project(tmp_path, monkeypatch) -> UUID:
    monkeypatch.setenv("ECOBIOME_LOCAL_DATA_DIR", str(tmp_path / "runtime"))
    created = create_water_body(
        CreateWaterBodyRequest(
            name="Bassin guidé 250 L",
            type="pond",
            volume_liters=250.0,
        )
    )
    return UUID(str(created["id"]))


def _items_by_key(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    raw = payload["items"]
    assert isinstance(raw, list)
    result: dict[str, dict[str, object]] = {}
    for item in raw:
        assert isinstance(item, dict)
        result[str(item["key"])] = item
    return result


def test_beginner_guidance_is_completeness_not_health_score(tmp_path, monkeypatch) -> None:
    health_payload = health()
    assert health_payload["status"] == "ok"
    assert health_payload["service"] == "ecobiome-local-api"

    project_id = _project(tmp_path, monkeypatch)

    initial = get_guidance(project_id, "beginner")
    assert initial["level"] == "beginner"
    assert initial["is_diagnostic"] is False
    assert initial["required_count"] == 6
    assert initial["known_required_count"] == 0
    items = _items_by_key(initial)
    assert items["livestock-inventory"]["status"] == "check"
    assert items["filtration-inventory"]["status"] == "check"

    for metric, value in (
        ("temperature", 22.5),
        ("ph", 7.4),
        ("nitrite", 0.0),
        ("nitrate", 12.0),
        ("kh", 6.0),
    ):
        add_measurement(project_id, AddMeasurementRequest(metric=metric, value=value))
    add_water_source(
        project_id,
        CreateWaterSourceRequest(
            name="Robinet maison",
            source_type="tap",
            ph=7.5,
            kh_dkh=7.0,
            gh_dgh=11.0,
            conductivity_us_cm=540.0,
        ),
    )

    completed = get_guidance(project_id, "beginner")
    assert completed["known_required_count"] == completed["required_count"] == 6
    assert completed["next_actions"] == []


def test_intermediate_guidance_becomes_contextual_when_livestock_and_filter_exist(
    tmp_path,
    monkeypatch,
) -> None:
    project_id = _project(tmp_path, monkeypatch)
    add_water_source(
        project_id,
        CreateWaterSourceRequest(
            name="Robinet maison",
            source_type="tap",
            ph=7.5,
            kh_dkh=7.0,
            gh_dgh=11.0,
            conductivity_us_cm=540.0,
        ),
    )
    add_livestock(
        project_id,
        CreateLivestockRequest(
            common_name="Medaka",
            count=12,
        ),
    )
    add_equipment(
        project_id,
        CreateEquipmentRequest(
            equipment_type="filter",
            name="Biofiltre principal",
            flow_lph=220.0,
        ),
    )

    guidance = get_guidance(project_id, "intermediate")
    items = _items_by_key(guidance)
    assert items["livestock-mass"]["status"] == "missing"
    assert items["feeding-history"]["status"] == "missing"
    assert items["filter-measured-flow"]["status"] == "missing"
    assert items["biofilter-maturity"]["status"] == "missing"
    assert items["metric:tan"]["required"] is True
    assert items["metric:oxygen"]["required"] is True
    assert items["water-source-core-chemistry"]["status"] == "known"

    record_feeding(
        project_id,
        FeedingRequest(food_name="Granulés", amount_g=0.15),
    )
    after_feeding = _items_by_key(get_guidance(project_id, "intermediate"))
    assert after_feeding["feeding-history"]["status"] == "known"


def test_advanced_guidance_requires_par_only_when_light_or_plants_make_it_applicable(
    tmp_path,
    monkeypatch,
) -> None:
    project_id = _project(tmp_path, monkeypatch)
    without_primary_producers = _items_by_key(get_guidance(project_id, "advanced"))
    assert without_primary_producers["metric:par_surface"]["required"] is False
    assert without_primary_producers["metric:par_surface"]["status"] == "check"
    assert without_primary_producers["metric:orp"]["required"] is False

    add_plant(
        project_id,
        CreatePlantRequest(
            common_name="Egeria",
            scientific_name="Egeria densa",
            coverage_percent=30.0,
        ),
    )
    with_plants = _items_by_key(get_guidance(project_id, "advanced"))
    assert with_plants["metric:par_surface"]["required"] is True
    assert with_plants["metric:par_surface"]["status"] == "missing"
    assert with_plants["metric:par_bottom"]["required"] is True
