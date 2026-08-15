"""Executable universal ecosystem profile contracts for N4."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from ecobiome.knowledge_persistence.serialization import canonical_json_text
from ecobiome.knowledge_persistence.serialization import (
    canonical_sha256 as canonical_payload_sha256,
)

_PROFILE_KINDS = frozenset({"aquarium", "pond"})
_DYNAMIC_PROPERTY_KEYS = frozenset(
    {
        "temperature",
        "ph",
        "concentration",
        "biomass",
        "abundance",
        "water_volume",
        "water_height",
        "dissolved_oxygen",
        "ammonia",
        "nitrite",
        "nitrate",
    }
)


def _reject_dynamic_property_keys(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).strip().lower().replace("-", "_").replace(" ", "_")
            if normalized_key in _DYNAMIC_PROPERTY_KEYS:
                raise ValueError(
                    f"dynamic quantity {key!r} belongs in ecosystem state, not topology"
                )
            _reject_dynamic_property_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_dynamic_property_keys(item)


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _required_string(
    payload: Mapping[str, object],
    key: str,
    context: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"{context}.{key} must be a string")
    return _nonempty(value, f"{context}.{key}")


def _canonical_properties(value: object) -> str:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("properties_json must contain valid JSON") from exc
    elif isinstance(value, Mapping):
        decoded = dict(value)
    else:
        raise TypeError("properties must be a JSON object or canonical JSON text")
    if not isinstance(decoded, dict):
        raise TypeError("properties must decode to a JSON object")
    _reject_dynamic_property_keys(decoded)
    return canonical_json_text(decoded)


@dataclass(frozen=True, slots=True)
class ScientificEntityRefV1:
    entity_id: str
    entity_revision: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "entity_id", _nonempty(self.entity_id, "entity_id"))
        if (
            isinstance(self.entity_revision, bool)
            or not isinstance(self.entity_revision, int)
            or self.entity_revision < 1
        ):
            raise ValueError("entity_revision must be an integer >= 1")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "entity_id": self.entity_id,
            "entity_revision": self.entity_revision,
        }


@dataclass(frozen=True, slots=True)
class PhysicalStructureV1:
    id: str
    structure_type: str
    label: str
    properties_json: str = "{}"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "physical structure id"))
        object.__setattr__(
            self, "structure_type", _nonempty(self.structure_type, "structure_type")
        )
        object.__setattr__(self, "label", _nonempty(self.label, "label"))
        object.__setattr__(self, "properties_json", _canonical_properties(self.properties_json))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "structure_type": self.structure_type,
            "label": self.label,
            "properties": json.loads(self.properties_json),
        }


@dataclass(frozen=True, slots=True)
class EnvironmentZoneV1:
    id: str
    zone_type: str
    label: str
    hosted_by_structure_id: str
    properties_json: str = "{}"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "environment zone id"))
        object.__setattr__(self, "zone_type", _nonempty(self.zone_type, "zone_type"))
        object.__setattr__(self, "label", _nonempty(self.label, "label"))
        object.__setattr__(
            self,
            "hosted_by_structure_id",
            _nonempty(self.hosted_by_structure_id, "hosted_by_structure_id"),
        )
        object.__setattr__(self, "properties_json", _canonical_properties(self.properties_json))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "zone_type": self.zone_type,
            "label": self.label,
            "hosted_by_structure_id": self.hosted_by_structure_id,
            "properties": json.loads(self.properties_json),
        }


@dataclass(frozen=True, slots=True)
class FunctionalSystemV1:
    id: str
    system_type: str
    label: str
    zone_ids: tuple[str, ...]
    properties_json: str = "{}"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "functional system id"))
        object.__setattr__(self, "system_type", _nonempty(self.system_type, "system_type"))
        object.__setattr__(self, "label", _nonempty(self.label, "label"))
        normalized = tuple(_nonempty(item, "zone_id") for item in self.zone_ids)
        if not normalized:
            raise ValueError("functional system must reference at least one zone")
        if len(set(normalized)) != len(normalized):
            raise ValueError("functional system zone_ids must be unique")
        object.__setattr__(self, "zone_ids", normalized)
        object.__setattr__(self, "properties_json", _canonical_properties(self.properties_json))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "system_type": self.system_type,
            "label": self.label,
            "zone_ids": sorted(self.zone_ids),
            "properties": json.loads(self.properties_json),
        }


@dataclass(frozen=True, slots=True)
class BiologicalPopulationV1:
    id: str
    population_type: str
    label: str
    zone_ids: tuple[str, ...]
    scientific_entity: ScientificEntityRefV1 | None = None
    properties_json: str = "{}"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "population id"))
        object.__setattr__(
            self, "population_type", _nonempty(self.population_type, "population_type")
        )
        object.__setattr__(self, "label", _nonempty(self.label, "label"))
        normalized = tuple(_nonempty(item, "zone_id") for item in self.zone_ids)
        if not normalized:
            raise ValueError("population must reference at least one zone")
        if len(set(normalized)) != len(normalized):
            raise ValueError("population zone_ids must be unique")
        object.__setattr__(self, "zone_ids", normalized)
        object.__setattr__(self, "properties_json", _canonical_properties(self.properties_json))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "population_type": self.population_type,
            "label": self.label,
            "zone_ids": sorted(self.zone_ids),
            "scientific_entity": (
                self.scientific_entity.canonical_payload()
                if self.scientific_entity is not None
                else None
            ),
            "properties": json.loads(self.properties_json),
        }


@dataclass(frozen=True, slots=True)
class MaterialComponentV1:
    id: str
    component_type: str
    label: str
    scientific_entity: ScientificEntityRefV1 | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "material component id"))
        object.__setattr__(
            self, "component_type", _nonempty(self.component_type, "component_type")
        )
        object.__setattr__(self, "label", _nonempty(self.label, "label"))

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "component_type": self.component_type,
            "label": self.label,
            "scientific_entity": (
                self.scientific_entity.canonical_payload()
                if self.scientific_entity is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class ResourceFlowV1:
    id: str
    source_node_id: str
    target_node_id: str
    material_component_id: str
    flow_kind: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "resource flow id"))
        object.__setattr__(
            self, "source_node_id", _nonempty(self.source_node_id, "source_node_id")
        )
        object.__setattr__(
            self, "target_node_id", _nonempty(self.target_node_id, "target_node_id")
        )
        object.__setattr__(
            self,
            "material_component_id",
            _nonempty(self.material_component_id, "material_component_id"),
        )
        object.__setattr__(self, "flow_kind", _nonempty(self.flow_kind, "flow_kind"))
        if self.source_node_id == self.target_node_id:
            raise ValueError("resource flow source and target must differ")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "material_component_id": self.material_component_id,
            "flow_kind": self.flow_kind,
        }


@dataclass(frozen=True, slots=True)
class EcosystemProfileV1:
    id: str
    profile_kind: str
    label: str
    structures: tuple[PhysicalStructureV1, ...]
    zones: tuple[EnvironmentZoneV1, ...]
    functional_systems: tuple[FunctionalSystemV1, ...] = ()
    populations: tuple[BiologicalPopulationV1, ...] = ()
    material_components: tuple[MaterialComponentV1, ...] = ()
    flows: tuple[ResourceFlowV1, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _nonempty(self.id, "profile id"))
        kind = self.profile_kind.strip().lower()
        if kind not in _PROFILE_KINDS:
            raise ValueError(f"unsupported profile_kind: {self.profile_kind!r}")
        object.__setattr__(self, "profile_kind", kind)
        object.__setattr__(self, "label", _nonempty(self.label, "label"))
        if not self.structures:
            raise ValueError("ecosystem profile requires at least one physical structure")
        if not self.zones:
            raise ValueError("ecosystem profile requires at least one environment zone")

        node_groups = (
            self.structures,
            self.zones,
            self.functional_systems,
            self.populations,
        )
        node_ids = [item.id for group in node_groups for item in group]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("all ecosystem node ids must be globally unique")

        component_ids = [item.id for item in self.material_components]
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("material component ids must be unique")

        flow_ids = [item.id for item in self.flows]
        if len(set(flow_ids)) != len(flow_ids):
            raise ValueError("resource flow ids must be unique")

        structure_ids = {item.id for item in self.structures}
        zone_ids = {item.id for item in self.zones}
        for zone in self.zones:
            if zone.hosted_by_structure_id not in structure_ids:
                raise ValueError(
                    f"zone {zone.id!r} references unknown structure "
                    f"{zone.hosted_by_structure_id!r}"
                )
        for system in self.functional_systems:
            unknown = set(system.zone_ids) - zone_ids
            if unknown:
                raise ValueError(
                    f"functional system {system.id!r} references unknown zones: "
                    f"{sorted(unknown)!r}"
                )
        for population in self.populations:
            unknown = set(population.zone_ids) - zone_ids
            if unknown:
                raise ValueError(
                    f"population {population.id!r} references unknown zones: "
                    f"{sorted(unknown)!r}"
                )

        node_id_set = set(node_ids)
        component_id_set = set(component_ids)
        for flow in self.flows:
            if flow.source_node_id not in node_id_set:
                raise ValueError(
                    f"flow {flow.id!r} references unknown source node "
                    f"{flow.source_node_id!r}"
                )
            if flow.target_node_id not in node_id_set:
                raise ValueError(
                    f"flow {flow.id!r} references unknown target node "
                    f"{flow.target_node_id!r}"
                )
            if flow.material_component_id not in component_id_set:
                raise ValueError(
                    f"flow {flow.id!r} references unknown material component "
                    f"{flow.material_component_id!r}"
                )

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema_version": "ecobiome-ecosystem-profile-v1",
            "id": self.id,
            "profile_kind": self.profile_kind,
            "label": self.label,
            "structures": [
                item.canonical_payload()
                for item in sorted(self.structures, key=lambda item: item.id)
            ],
            "zones": [
                item.canonical_payload()
                for item in sorted(self.zones, key=lambda item: item.id)
            ],
            "functional_systems": [
                item.canonical_payload()
                for item in sorted(self.functional_systems, key=lambda item: item.id)
            ],
            "populations": [
                item.canonical_payload()
                for item in sorted(self.populations, key=lambda item: item.id)
            ],
            "material_components": [
                item.canonical_payload()
                for item in sorted(self.material_components, key=lambda item: item.id)
            ],
            "flows": [
                item.canonical_payload()
                for item in sorted(self.flows, key=lambda item: item.id)
            ],
        }

    @property
    def canonical_sha256(self) -> str:
        return canonical_payload_sha256(self.canonical_payload())


def _entity_ref_from_mapping(
    value: object,
) -> ScientificEntityRefV1 | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError("scientific_entity must be an object or null")
    raw_revision = value.get("entity_revision")
    if isinstance(raw_revision, bool) or not isinstance(raw_revision, int):
        raise TypeError("scientific_entity.entity_revision must be an integer")
    entity_id = value.get("entity_id")
    if not isinstance(entity_id, str):
        raise TypeError("scientific_entity.entity_id must be a string")
    return ScientificEntityRefV1(
        entity_id=entity_id,
        entity_revision=raw_revision,
    )


def _string_array(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be an array")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise TypeError(f"{field_name} entries must be strings")
        result.append(_nonempty(item, field_name))
    return tuple(result)


def ecosystem_profile_from_mapping_v1(payload: Mapping[str, object]) -> EcosystemProfileV1:
    """Build a strict V1 profile from one JSON-compatible mapping."""
    def object_list(name: str) -> list[Mapping[str, object]]:
        raw = payload.get(name, [])
        if not isinstance(raw, list):
            raise TypeError(f"{name} must be an array")
        result: list[Mapping[str, object]] = []
        for item in raw:
            if not isinstance(item, Mapping):
                raise TypeError(f"{name} entries must be objects")
            result.append(item)
        return result

    structures = tuple(
        PhysicalStructureV1(
            id=_required_string(item, "id", "structure"),
            structure_type=_required_string(item, "structure_type", "structure"),
            label=_required_string(item, "label", "structure"),
            properties_json=_canonical_properties(item.get("properties", {})),
        )
        for item in object_list("structures")
    )
    zones = tuple(
        EnvironmentZoneV1(
            id=_required_string(item, "id", "zone"),
            zone_type=_required_string(item, "zone_type", "zone"),
            label=_required_string(item, "label", "zone"),
            hosted_by_structure_id=_required_string(
                item,
                "hosted_by_structure_id",
                "zone",
            ),
            properties_json=_canonical_properties(item.get("properties", {})),
        )
        for item in object_list("zones")
    )
    systems = tuple(
        FunctionalSystemV1(
            id=_required_string(item, "id", "functional_system"),
            system_type=_required_string(
                item,
                "system_type",
                "functional_system",
            ),
            label=_required_string(item, "label", "functional_system"),
            zone_ids=_string_array(item.get("zone_ids", []), "zone_ids"),
            properties_json=_canonical_properties(item.get("properties", {})),
        )
        for item in object_list("functional_systems")
    )
    populations = tuple(
        BiologicalPopulationV1(
            id=_required_string(item, "id", "population"),
            population_type=_required_string(
                item,
                "population_type",
                "population",
            ),
            label=_required_string(item, "label", "population"),
            zone_ids=_string_array(item.get("zone_ids", []), "zone_ids"),
            scientific_entity=_entity_ref_from_mapping(item.get("scientific_entity")),
            properties_json=_canonical_properties(item.get("properties", {})),
        )
        for item in object_list("populations")
    )
    components = tuple(
        MaterialComponentV1(
            id=_required_string(item, "id", "material_component"),
            component_type=_required_string(
                item,
                "component_type",
                "material_component",
            ),
            label=_required_string(item, "label", "material_component"),
            scientific_entity=_entity_ref_from_mapping(item.get("scientific_entity")),
        )
        for item in object_list("material_components")
    )
    flows = tuple(
        ResourceFlowV1(
            id=_required_string(item, "id", "flow"),
            source_node_id=_required_string(item, "source_node_id", "flow"),
            target_node_id=_required_string(item, "target_node_id", "flow"),
            material_component_id=_required_string(
                item,
                "material_component_id",
                "flow",
            ),
            flow_kind=_required_string(item, "flow_kind", "flow"),
        )
        for item in object_list("flows")
    )
    return EcosystemProfileV1(
        id=_required_string(payload, "id", "profile"),
        profile_kind=_required_string(payload, "profile_kind", "profile"),
        label=_required_string(payload, "label", "profile"),
        structures=structures,
        zones=zones,
        functional_systems=systems,
        populations=populations,
        material_components=components,
        flows=flows,
    )
