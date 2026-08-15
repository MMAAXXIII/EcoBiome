from __future__ import annotations

import json
from pathlib import Path

import pytest

from ecobiome.world.ecosystem_profile_v1 import (
    EcosystemProfileV1,
    EnvironmentZoneV1,
    PhysicalStructureV1,
    ScientificEntityRefV1,
    ecosystem_profile_from_mapping_v1,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "ecosystem_profiles"


def _load(name: str) -> EcosystemProfileV1:
    payload = json.loads((_FIXTURES / name).read_text(encoding="utf-8"))
    return ecosystem_profile_from_mapping_v1(payload)


def test_same_generic_contract_represents_aquarium_and_pond() -> None:
    aquarium = _load("aquarium_v1.json")
    pond = _load("pond_v1.json")

    assert isinstance(aquarium, EcosystemProfileV1)
    assert isinstance(pond, EcosystemProfileV1)
    assert aquarium.profile_kind == "aquarium"
    assert pond.profile_kind == "pond"
    assert aquarium.canonical_sha256 != pond.canonical_sha256


def test_profile_hash_is_independent_of_input_array_order() -> None:
    raw = json.loads((_FIXTURES / "aquarium_v1.json").read_text(encoding="utf-8"))
    first = ecosystem_profile_from_mapping_v1(raw)
    raw["zones"] = list(reversed(raw["zones"]))
    raw["populations"] = list(reversed(raw["populations"]))
    raw["flows"] = list(reversed(raw["flows"]))
    second = ecosystem_profile_from_mapping_v1(raw)

    assert first.canonical_sha256 == second.canonical_sha256


def test_profile_rejects_dangling_zone_structure_reference() -> None:
    with pytest.raises(ValueError, match="unknown structure"):
        EcosystemProfileV1(
            id="bad",
            profile_kind="aquarium",
            label="Bad",
            structures=(
                PhysicalStructureV1(
                    id="tank",
                    structure_type="container",
                    label="Tank",
                ),
            ),
            zones=(
                EnvironmentZoneV1(
                    id="water",
                    zone_type="open_water",
                    label="Water",
                    hosted_by_structure_id="missing",
                ),
            ),
        )


def test_profile_rejects_native_float_in_canonical_properties() -> None:
    with pytest.raises(TypeError, match="Native scientific numeric"):
        PhysicalStructureV1(
            id="tank",
            structure_type="container",
            label="Tank",
            properties_json='{"volume": 250.5}',
        )



def test_profile_rejects_dynamic_quantity_in_topology_properties() -> None:
    with pytest.raises(ValueError, match="belongs in ecosystem state"):
        PhysicalStructureV1(
            id="tank",
            structure_type="container",
            label="Tank",
            properties_json='{"temperature": "21.5"}',
        )


def test_scientific_entity_ref_rejects_non_integer_revision() -> None:
    with pytest.raises(ValueError, match="integer >= 1"):
        ScientificEntityRefV1(
            entity_id="entity-1",
            entity_revision=1.5,  # type: ignore[arg-type]
        )



def test_profile_loader_rejects_numeric_identifier_coercion() -> None:
    raw = json.loads((_FIXTURES / "aquarium_v1.json").read_text(encoding="utf-8"))
    raw["id"] = 123
    with pytest.raises(TypeError, match="profile.id must be a string"):
        ecosystem_profile_from_mapping_v1(raw)


def test_profile_loader_rejects_numeric_zone_reference_coercion() -> None:
    raw = json.loads((_FIXTURES / "aquarium_v1.json").read_text(encoding="utf-8"))
    raw["functional_systems"][0]["zone_ids"] = [123]
    with pytest.raises(TypeError, match="zone_ids entries must be strings"):
        ecosystem_profile_from_mapping_v1(raw)
