"""Canonical project observation/intervention events for EcoBiome N5."""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from uuid import UUID

from ecobiome.core.observation.measurement import ScientificMeasurement
from ecobiome.core.observation.observation import AcquisitionMethod, Observation
from ecobiome.journal.event import JournalEvent
from ecobiome.journal.event_type import JournalEventType
from ecobiome.journal.jsonl_store import JsonlJournalEventStore
from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
    normalize_decimal,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    QuantityBasisV1,
)
from ecobiome.simulation.intervention_v1 import (
    ReplacementCompositionV1,
    WaterExchangeInterventionV1,
)
from ecobiome.simulation.observation_adapter_v1 import canonicalize_observation_v1

CANONICAL_PROJECT_EVENT_SCHEMA_V1 = "ecobiome-canonical-project-event-v1"
PROJECT_OBSERVATION_SCHEMA_V1 = "ecobiome-project-observation-v1"
PROJECT_WATER_EXCHANGE_SCHEMA_V1 = (
    "ecobiome-project-water-exchange-intervention-v1"
)
CANONICAL_PROJECT_EVENT_TAG_V1 = "canonical-project-event-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_EVENT_TYPES = frozenset(
    {
        JournalEventType.OBSERVATION,
        JournalEventType.INTERVENTION,
    }
)
_UNIT_ALIASES_V1 = {
    "L": "L",
    "liter": "L",
    "litre": "L",
    "mL": "mL",
    "mg": "mg",
    "g": "g",
    "mg N": "mg N",
    "g N": "g N",
    "mg/L": "mg/L",
    "g/L": "g/L",
    "mg N/L": "mg N/L",
    "g N/L": "g N/L",
    "dimensionless": "dimensionless",
}

_OBSERVATION_PAYLOAD_KEYS = frozenset(
    {
        "schema_version",
        "observation_id",
        "quantity",
        "source",
        "acquisition_method",
        "observed_at",
        "confidence",
        "raw_reference",
        "measurement_uncertainty",
        "warnings",
    }
)
_QUANTITY_KEYS = frozenset(
    {
        "variable_id",
        "value",
        "unit",
        "basis",
        "zone_id",
        "material_component_id",
    }
)
_BASIS_KEYS = frozenset(
    {
        "kind",
        "reference_id",
        "reference_revision",
        "note",
    }
)
_INTERVENTION_PAYLOAD_KEYS = frozenset(
    {
        "schema_version",
        "intervention",
        "intervention_sha256",
    }
)
_WATER_EXCHANGE_KEYS = frozenset(
    {
        "schema_version",
        "id",
        "water_zone_id",
        "removed_volume",
        "replacement_volume",
        "replacement_composition",
        "basis",
        "logical_step",
    }
)
_REPLACEMENT_COMPOSITION_KEYS = frozenset(
    {
        "material_component_id",
        "concentration",
        "basis",
    }
)
_VALUE_WITH_UNIT_KEYS = frozenset({"value", "unit"})
_TYPED_DECIMAL_KEYS = frozenset({"type", "value"})


def _nonempty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_exact_keys(
    value: Mapping[str, object],
    expected: frozenset[str],
    field_name: str,
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{field_name} fields mismatch; missing={missing!r}, extra={extra!r}"
        )


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise TypeError(f"{field_name} keys must be strings")
    return cast(Mapping[str, object], value)


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    return _nonempty(value, field_name)


def _optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, field_name)


def _typed_decimal_text(value: object, field_name: str) -> str:
    typed = _require_mapping(value, field_name)
    _require_exact_keys(typed, _TYPED_DECIMAL_KEYS, field_name)
    if typed["type"] != "decimal":
        raise ValueError(f"{field_name}.type must be 'decimal'")
    raw_value = typed["value"]
    if not isinstance(raw_value, str):
        raise TypeError(f"{field_name}.value must be a decimal string")
    normalized = normalize_decimal(raw_value)
    if raw_value != normalized:
        raise ValueError(f"{field_name}.value must already be normalized")
    return normalized


def _datetime_from_iso(value: object, field_name: str) -> datetime:
    text = _require_string(value, field_name)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if parsed.isoformat() != text:
        raise ValueError(f"{field_name} must use canonical datetime.isoformat() text")
    return parsed


def canonicalize_unit_text_v1(unit: str) -> str:
    """Normalize admitted N4 unit aliases without performing numeric conversion."""
    normalized = _nonempty(unit, "unit")
    return _UNIT_ALIASES_V1.get(normalized, normalized)


def _basis_from_payload(value: object) -> QuantityBasisV1:
    payload = _require_mapping(value, "quantity basis")
    _require_exact_keys(payload, _BASIS_KEYS, "quantity basis")
    kind = _require_string(payload["kind"], "basis.kind")
    reference_id = _require_string(payload["reference_id"], "basis.reference_id")
    reference_revision_value = payload["reference_revision"]
    if reference_revision_value is not None and (
        isinstance(reference_revision_value, bool)
        or not isinstance(reference_revision_value, int)
    ):
        raise TypeError("basis.reference_revision must be an integer or null")
    note_value = payload["note"]
    if not isinstance(note_value, str):
        raise TypeError("basis.note must be a string")
    return QuantityBasisV1(
        kind=kind,
        reference_id=reference_id,
        reference_revision=cast(int | None, reference_revision_value),
        note=note_value,
    )


def _quantity_from_payload(value: object) -> CanonicalQuantityV1:
    payload = _require_mapping(value, "quantity")
    _require_exact_keys(payload, _QUANTITY_KEYS, "quantity")
    variable_id = _require_string(payload["variable_id"], "quantity.variable_id")
    value_decimal = _typed_decimal_text(payload["value"], "quantity.value")
    unit = _require_string(payload["unit"], "quantity.unit")
    if unit != canonicalize_unit_text_v1(unit):
        raise ValueError("quantity.unit must use the N5 canonical unit lexeme")
    zone_id = _optional_string(payload["zone_id"], "quantity.zone_id")
    material_component_id = _optional_string(
        payload["material_component_id"],
        "quantity.material_component_id",
    )
    quantity = CanonicalQuantityV1(
        variable_id=variable_id,
        value_decimal=value_decimal,
        unit=unit,
        basis=_basis_from_payload(payload["basis"]),
        zone_id=zone_id,
        material_component_id=material_component_id,
    )
    if quantity.canonical_payload() != dict(payload):
        raise ValueError("quantity payload is not canonical CanonicalQuantityV1")
    return quantity


def _value_with_unit(
    value: object,
    field_name: str,
) -> tuple[str, str]:
    payload = _require_mapping(value, field_name)
    _require_exact_keys(payload, _VALUE_WITH_UNIT_KEYS, field_name)
    decimal_text = _typed_decimal_text(payload["value"], f"{field_name}.value")
    unit = _require_string(payload["unit"], f"{field_name}.unit")
    return decimal_text, unit


def _replacement_from_payload(value: object) -> ReplacementCompositionV1:
    payload = _require_mapping(value, "replacement composition")
    _require_exact_keys(
        payload,
        _REPLACEMENT_COMPOSITION_KEYS,
        "replacement composition",
    )
    concentration_decimal, unit = _value_with_unit(
        payload["concentration"],
        "replacement composition concentration",
    )
    replacement = ReplacementCompositionV1(
        material_component_id=_require_string(
            payload["material_component_id"],
            "replacement material_component_id",
        ),
        concentration_decimal=concentration_decimal,
        unit=unit,
        basis=_basis_from_payload(payload["basis"]),
    )
    if replacement.canonical_payload() != dict(payload):
        raise ValueError("replacement composition payload is not canonical")
    return replacement


def _water_exchange_from_payload(value: object) -> WaterExchangeInterventionV1:
    payload = _require_mapping(value, "water exchange intervention")
    _require_exact_keys(payload, _WATER_EXCHANGE_KEYS, "water exchange intervention")
    if payload["schema_version"] != "ecobiome-water-exchange-intervention-v1":
        raise ValueError("unsupported water exchange intervention schema")
    removed_decimal, removed_unit = _value_with_unit(
        payload["removed_volume"],
        "removed_volume",
    )
    replacement_decimal, replacement_unit = _value_with_unit(
        payload["replacement_volume"],
        "replacement_volume",
    )
    raw_composition = payload["replacement_composition"]
    if not isinstance(raw_composition, list):
        raise TypeError("replacement_composition must be an array")
    logical_step_value = payload["logical_step"]
    if logical_step_value is not None and (
        isinstance(logical_step_value, bool)
        or not isinstance(logical_step_value, int)
    ):
        raise TypeError("logical_step must be an integer or null")
    intervention = WaterExchangeInterventionV1(
        id=_require_string(payload["id"], "intervention.id"),
        water_zone_id=_require_string(
            payload["water_zone_id"],
            "intervention.water_zone_id",
        ),
        removed_volume_decimal=removed_decimal,
        removed_volume_unit=removed_unit,
        replacement_volume_decimal=replacement_decimal,
        replacement_volume_unit=replacement_unit,
        replacement_composition=tuple(
            _replacement_from_payload(item) for item in raw_composition
        ),
        basis=_basis_from_payload(payload["basis"]),
        logical_step=cast(int | None, logical_step_value),
    )
    if intervention.canonical_payload() != dict(payload):
        raise ValueError("water exchange intervention payload is not canonical")
    return intervention


def _validate_observation_payload(
    payload: Mapping[str, object],
    *,
    event_id: UUID,
    subject_id: str,
    occurred_at: datetime,
) -> None:
    _require_exact_keys(payload, _OBSERVATION_PAYLOAD_KEYS, "observation payload")
    if payload["schema_version"] != PROJECT_OBSERVATION_SCHEMA_V1:
        raise ValueError("unsupported observation payload schema")
    observation_id = _require_string(
        payload["observation_id"],
        "observation_id",
    )
    if observation_id != str(event_id) or observation_id != subject_id:
        raise ValueError(
            "observation identity must equal event_id and canonical subject_id"
        )
    quantity = _quantity_from_payload(payload["quantity"])
    if quantity.basis.kind != "observation":
        raise ValueError("observation quantity basis must be 'observation'")
    if quantity.basis.reference_id != observation_id:
        raise ValueError(
            "observation quantity basis reference must equal observation_id"
        )
    observed_at = _datetime_from_iso(payload["observed_at"], "observed_at")
    if observed_at != occurred_at:
        raise ValueError("observation observed_at must equal event occurred_at")
    _require_string(payload["source"], "observation source")
    AcquisitionMethod(
        _require_string(payload["acquisition_method"], "acquisition_method")
    )
    confidence_text = _typed_decimal_text(payload["confidence"], "confidence")
    confidence = Decimal(confidence_text)
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be between 0 and 1")
    raw_reference = payload["raw_reference"]
    if raw_reference is not None and not isinstance(raw_reference, str):
        raise TypeError("raw_reference must be a string or null")
    uncertainty = payload["measurement_uncertainty"]
    if uncertainty is not None:
        uncertainty_text = _typed_decimal_text(
            uncertainty,
            "measurement_uncertainty",
        )
        if Decimal(uncertainty_text) < 0:
            raise ValueError("measurement_uncertainty cannot be negative")
    raw_warnings = payload["warnings"]
    if not isinstance(raw_warnings, list):
        raise TypeError("warnings must be an array")
    warnings: list[str] = []
    for item in raw_warnings:
        warnings.append(_require_string(item, "warning"))
    if len(warnings) != len(set(warnings)):
        raise ValueError("warnings must be unique")


def _validate_intervention_payload(
    payload: Mapping[str, object],
    *,
    subject_id: str,
) -> None:
    _require_exact_keys(
        payload,
        _INTERVENTION_PAYLOAD_KEYS,
        "intervention payload",
    )
    if payload["schema_version"] != PROJECT_WATER_EXCHANGE_SCHEMA_V1:
        raise ValueError("unsupported intervention payload schema")
    intervention = _water_exchange_from_payload(payload["intervention"])
    if intervention.id != subject_id:
        raise ValueError("intervention id must equal canonical subject_id")
    supplied_sha = _require_string(
        payload["intervention_sha256"],
        "intervention_sha256",
    )
    if supplied_sha != intervention.canonical_sha256:
        raise ValueError("intervention SHA-256 does not match N4 canonical payload")


def _event_envelope_payload(
    *,
    project_id: UUID,
    event_id: UUID,
    event_type: JournalEventType,
    occurred_at: datetime,
    subject_id: str,
    payload_schema_version: str,
    canonical_payload_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": CANONICAL_PROJECT_EVENT_SCHEMA_V1,
        "project_id": str(project_id),
        "event_id": str(event_id),
        "event_type": event_type.value,
        "occurred_at": occurred_at.isoformat(),
        "subject_id": subject_id,
        "payload_schema_version": payload_schema_version,
        "canonical_payload_sha256": canonical_payload_sha256,
    }


@dataclass(frozen=True, slots=True)
class CanonicalProjectEventV1:
    """Tamper-evident canonical project event persisted through the journal."""

    project_id: UUID
    event_id: UUID
    event_type: JournalEventType
    occurred_at: datetime
    subject_id: str
    payload_schema_version: str
    canonical_payload_json: str
    canonical_payload_sha256: str
    canonical_event_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, UUID):
            raise TypeError("project_id must be UUID")
        if not isinstance(self.event_id, UUID):
            raise TypeError("event_id must be UUID")
        if self.event_type not in _ALLOWED_EVENT_TYPES:
            raise ValueError("N5 V1 supports only observation/intervention events")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        subject_id = _nonempty(self.subject_id, "subject_id")
        schema_version = _nonempty(
            self.payload_schema_version,
            "payload_schema_version",
        )
        object.__setattr__(self, "subject_id", subject_id)
        object.__setattr__(self, "payload_schema_version", schema_version)

        try:
            raw_payload = json.loads(self.canonical_payload_json)
        except json.JSONDecodeError as exc:
            raise ValueError("canonical_payload_json must contain valid JSON") from exc
        payload = _require_mapping(raw_payload, "canonical payload")
        recanonicalized = canonical_json_text(payload)
        if recanonicalized != self.canonical_payload_json:
            raise ValueError("canonical_payload_json is not canonical JSON")
        if payload.get("schema_version") != schema_version:
            raise ValueError(
                "payload schema_version must equal payload_schema_version"
            )

        payload_sha = self.canonical_payload_sha256.strip()
        if not _SHA256_RE.fullmatch(payload_sha):
            raise ValueError("canonical_payload_sha256 must be lowercase SHA-256")
        if canonical_sha256(payload) != payload_sha:
            raise ValueError("canonical payload SHA-256 mismatch")
        object.__setattr__(self, "canonical_payload_sha256", payload_sha)

        if self.event_type is JournalEventType.OBSERVATION:
            if schema_version != PROJECT_OBSERVATION_SCHEMA_V1:
                raise ValueError("observation event requires observation payload schema")
            _validate_observation_payload(
                payload,
                event_id=self.event_id,
                subject_id=subject_id,
                occurred_at=self.occurred_at,
            )
        elif self.event_type is JournalEventType.INTERVENTION:
            if schema_version != PROJECT_WATER_EXCHANGE_SCHEMA_V1:
                raise ValueError(
                    "intervention event requires water-exchange payload schema"
                )
            _validate_intervention_payload(payload, subject_id=subject_id)

        event_sha = self.canonical_event_sha256.strip()
        if not _SHA256_RE.fullmatch(event_sha):
            raise ValueError("canonical_event_sha256 must be lowercase SHA-256")
        expected_event_sha = canonical_sha256(self.canonical_event_payload())
        if event_sha != expected_event_sha:
            raise ValueError("canonical event envelope SHA-256 mismatch")
        object.__setattr__(self, "canonical_event_sha256", event_sha)

    @property
    def canonical_payload(self) -> dict[str, object]:
        value = json.loads(self.canonical_payload_json)
        if not isinstance(value, dict):
            raise TypeError("canonical project event payload must be an object")
        return cast(dict[str, object], value)

    def canonical_event_payload(self) -> dict[str, object]:
        return _event_envelope_payload(
            project_id=self.project_id,
            event_id=self.event_id,
            event_type=self.event_type,
            occurred_at=self.occurred_at,
            subject_id=self.subject_id,
            payload_schema_version=self.payload_schema_version,
            canonical_payload_sha256=self.canonical_payload_sha256,
        )

    def to_journal_event(self) -> JournalEvent:
        noun = (
            "observation"
            if self.event_type is JournalEventType.OBSERVATION
            else "intervention"
        )
        return JournalEvent(
            event_id=self.event_id,
            project_id=self.project_id,
            event_type=self.event_type,
            title=f"Canonical {noun} {self.subject_id}",
            occurred_at=self.occurred_at,
            tags=(CANONICAL_PROJECT_EVENT_TAG_V1,),
            attributes=(
                (
                    "canonical_schema_version",
                    CANONICAL_PROJECT_EVENT_SCHEMA_V1,
                ),
                ("canonical_subject_id", self.subject_id),
                (
                    "canonical_payload_schema_version",
                    self.payload_schema_version,
                ),
                (
                    "canonical_payload_sha256",
                    self.canonical_payload_sha256,
                ),
                ("canonical_event_sha256", self.canonical_event_sha256),
            ),
            payload=(("canonical_payload_json", self.canonical_payload_json),),
        )


def _build_event(
    *,
    project_id: UUID,
    event_id: UUID,
    event_type: JournalEventType,
    occurred_at: datetime,
    subject_id: str,
    payload_schema_version: str,
    payload: Mapping[str, object],
) -> CanonicalProjectEventV1:
    payload_json = canonical_json_text(payload)
    payload_sha = canonical_sha256(payload)
    event_sha = canonical_sha256(
        _event_envelope_payload(
            project_id=project_id,
            event_id=event_id,
            event_type=event_type,
            occurred_at=occurred_at,
            subject_id=subject_id,
            payload_schema_version=payload_schema_version,
            canonical_payload_sha256=payload_sha,
        )
    )
    return CanonicalProjectEventV1(
        project_id=project_id,
        event_id=event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        subject_id=subject_id,
        payload_schema_version=payload_schema_version,
        canonical_payload_json=payload_json,
        canonical_payload_sha256=payload_sha,
        canonical_event_sha256=event_sha,
    )


def build_canonical_observation_event_v1(
    *,
    project_id: UUID,
    observation: Observation,
    zone_id: str | None = None,
    material_component_id: str | None = None,
) -> CanonicalProjectEventV1:
    """Canonicalize one legacy observation and freeze its project-event identity."""
    adapted = canonicalize_observation_v1(
        observation,
        zone_id=zone_id,
        material_component_id=material_component_id,
    )
    source_quantity = adapted.quantity
    quantity = CanonicalQuantityV1(
        variable_id=source_quantity.variable_id,
        value_decimal=source_quantity.value_decimal,
        unit=canonicalize_unit_text_v1(source_quantity.unit),
        basis=source_quantity.basis,
        zone_id=source_quantity.zone_id,
        material_component_id=source_quantity.material_component_id,
    )
    measurement_uncertainty: dict[str, str] | None = None
    if isinstance(observation.value, ScientificMeasurement):
        measurement_uncertainty = {
            "type": "decimal",
            "value": normalize_decimal(str(observation.value.uncertainty)),
        }
    payload: dict[str, object] = {
        "schema_version": PROJECT_OBSERVATION_SCHEMA_V1,
        "observation_id": str(observation.observation_id),
        "quantity": quantity.canonical_payload(),
        "source": observation.source,
        "acquisition_method": observation.acquisition_method.value,
        "observed_at": observation.observed_at.isoformat(),
        "confidence": {
            "type": "decimal",
            "value": normalize_decimal(str(observation.confidence)),
        },
        "raw_reference": observation.raw_reference,
        "measurement_uncertainty": measurement_uncertainty,
        "warnings": list(adapted.warnings),
    }
    return _build_event(
        project_id=project_id,
        event_id=observation.observation_id,
        event_type=JournalEventType.OBSERVATION,
        occurred_at=observation.observed_at,
        subject_id=str(observation.observation_id),
        payload_schema_version=PROJECT_OBSERVATION_SCHEMA_V1,
        payload=payload,
    )


def build_canonical_water_exchange_event_v1(
    *,
    project_id: UUID,
    event_id: UUID,
    intervention: WaterExchangeInterventionV1,
    occurred_at: datetime,
) -> CanonicalProjectEventV1:
    """Freeze one N4 water-exchange intervention as a canonical project event."""
    payload: dict[str, object] = {
        "schema_version": PROJECT_WATER_EXCHANGE_SCHEMA_V1,
        "intervention": intervention.canonical_payload(),
        "intervention_sha256": intervention.canonical_sha256,
    }
    return _build_event(
        project_id=project_id,
        event_id=event_id,
        event_type=JournalEventType.INTERVENTION,
        occurred_at=occurred_at,
        subject_id=intervention.id,
        payload_schema_version=PROJECT_WATER_EXCHANGE_SCHEMA_V1,
        payload=payload,
    )


def _required_attribute(event: JournalEvent, key: str) -> str:
    value = event.attribute_map.get(key)
    if value is None:
        raise ValueError(f"canonical journal event missing attribute {key!r}")
    return _nonempty(value, key)


def canonical_project_event_from_journal_event_v1(
    event: JournalEvent,
) -> CanonicalProjectEventV1:
    """Rehydrate and fully verify a journal-backed canonical N5 project event."""
    if CANONICAL_PROJECT_EVENT_TAG_V1 not in event.tags:
        raise ValueError("journal event is not tagged as canonical N5 project event")
    if event.project_id is None:
        raise ValueError("canonical N5 project event requires project_id")
    if (
        _required_attribute(event, "canonical_schema_version")
        != CANONICAL_PROJECT_EVENT_SCHEMA_V1
    ):
        raise ValueError("unsupported canonical project event schema")
    payload_json = event.payload_map.get("canonical_payload_json")
    if not isinstance(payload_json, str):
        raise TypeError("canonical_payload_json journal field must be a string")
    return CanonicalProjectEventV1(
        project_id=event.project_id,
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        subject_id=_required_attribute(event, "canonical_subject_id"),
        payload_schema_version=_required_attribute(
            event,
            "canonical_payload_schema_version",
        ),
        canonical_payload_json=payload_json,
        canonical_payload_sha256=_required_attribute(
            event,
            "canonical_payload_sha256",
        ),
        canonical_event_sha256=_required_attribute(
            event,
            "canonical_event_sha256",
        ),
    )


class CanonicalProjectEventStoreV1:
    """Append/read verified N5 canonical events through the existing JSONL journal."""

    def __init__(self, path: str | Path) -> None:
        self._store = JsonlJournalEventStore(path)

    @property
    def path(self) -> Path:
        return self._store.path

    def append(self, event: CanonicalProjectEventV1) -> None:
        self._store.append(event.to_journal_event())

    def get(self, event_id: UUID) -> CanonicalProjectEventV1:
        return canonical_project_event_from_journal_event_v1(
            self._store.get(event_id)
        )

    def all(self) -> tuple[CanonicalProjectEventV1, ...]:
        result: list[CanonicalProjectEventV1] = []
        for event in self._store.all():
            if CANONICAL_PROJECT_EVENT_TAG_V1 not in event.tags:
                continue
            result.append(canonical_project_event_from_journal_event_v1(event))
        return tuple(result)

    def count(self) -> int:
        return len(self.all())
