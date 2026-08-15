"""N5 canonical project observation/intervention persistence seam."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from ecobiome.core.observation.measurement import ScientificMeasurement
from ecobiome.core.observation.observation import AcquisitionMethod, Observation
from ecobiome.core.units import Measurement
from ecobiome.journal.canonical_project_event_v1 import (
    CANONICAL_PROJECT_EVENT_TAG_V1,
    CanonicalProjectEventStoreV1,
    CanonicalProjectEventV1,
    build_canonical_observation_event_v1,
    build_canonical_water_exchange_event_v1,
    canonical_project_event_from_journal_event_v1,
)
from ecobiome.journal.event import JournalEvent
from ecobiome.journal.event_type import JournalEventType
from ecobiome.journal.jsonl_store import JsonlJournalEventStore
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.simulation.ecosystem_state_v1 import QuantityBasisV1
from ecobiome.simulation.intervention_v1 import (
    ReplacementCompositionV1,
    WaterExchangeInterventionV1,
)


def _observation(*, unit: str = "liter") -> Observation:
    variable = ScientificVariable(
        identifier="water.volume",
        name="Water volume",
        description="Measured water volume.",
        unit="L",
    )
    return Observation(
        source="manual-test",
        variable=variable,
        value=ScientificMeasurement(
            quantity=Measurement(value=12.5, unit=unit),
            uncertainty=0.1,
        ),
        acquisition_method=AcquisitionMethod.HUMAN,
        confidence=0.95,
        raw_reference="notebook:1",
        observed_at=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        observation_id=UUID("11111111-1111-4111-8111-111111111111"),
    )


def _intervention() -> WaterExchangeInterventionV1:
    basis = QuantityBasisV1(
        kind="user_assumption",
        reference_id="user:water-change",
    )
    return WaterExchangeInterventionV1(
        id="water-change-001",
        water_zone_id="water-column",
        removed_volume_decimal="10",
        removed_volume_unit="L",
        replacement_volume_decimal="10",
        replacement_volume_unit="L",
        replacement_composition=(
            ReplacementCompositionV1(
                material_component_id="oxidized_inorganic_nitrogen",
                concentration_decimal="0.1",
                unit="mg N/L",
                basis=basis,
            ),
        ),
        basis=basis,
        logical_step=1,
    )


def _assert_no_native_float(value: Any) -> None:
    assert not isinstance(value, float), (
        f"native float found in canonical payload: {value!r}"
    )
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_native_float(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_native_float(item)


def test_observation_event_is_float_free_and_round_trips(tmp_path: Any) -> None:
    project_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    event = build_canonical_observation_event_v1(
        project_id=project_id,
        observation=_observation(),
        zone_id="water-column",
    )
    parsed = json.loads(event.canonical_payload_json)
    _assert_no_native_float(parsed)
    assert parsed["measurement_uncertainty"] == {
        "type": "decimal",
        "value": "0.1",
    }

    store = CanonicalProjectEventStoreV1(tmp_path / "events.jsonl")
    store.append(event)

    assert store.get(event.event_id) == event
    assert store.all() == (event,)
    assert store.count() == 1


def test_known_unit_alias_is_normalized_before_hashing() -> None:
    event = build_canonical_observation_event_v1(
        project_id=uuid4(),
        observation=_observation(unit="liter"),
    )
    quantity = event.canonical_payload["quantity"]
    assert isinstance(quantity, dict)
    assert quantity["unit"] == "L"


def test_observation_hashes_are_deterministic() -> None:
    project_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    observation = _observation()
    first = build_canonical_observation_event_v1(
        project_id=project_id,
        observation=observation,
        zone_id="water-column",
    )
    second = build_canonical_observation_event_v1(
        project_id=project_id,
        observation=observation,
        zone_id="water-column",
    )
    assert first.canonical_payload_sha256 == second.canonical_payload_sha256
    assert first.canonical_event_sha256 == second.canonical_event_sha256
    assert first.canonical_payload_json == second.canonical_payload_json


def test_raw_float_inside_claimed_canonical_payload_is_rejected() -> None:
    event = build_canonical_observation_event_v1(
        project_id=uuid4(),
        observation=_observation(),
    )
    payload = event.canonical_payload
    payload["confidence"] = 0.95
    raw_float_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    with pytest.raises(TypeError):
        replace(event, canonical_payload_json=raw_float_json)


def test_payload_sha_tamper_is_rejected() -> None:
    event = build_canonical_observation_event_v1(
        project_id=uuid4(),
        observation=_observation(),
    )
    with pytest.raises(ValueError, match="payload SHA-256"):
        replace(event, canonical_payload_sha256="0" * 64)


def test_noncanonical_payload_json_is_rejected() -> None:
    event = build_canonical_observation_event_v1(
        project_id=uuid4(),
        observation=_observation(),
    )
    noncanonical = json.dumps(event.canonical_payload, indent=2, sort_keys=False)
    with pytest.raises(ValueError, match="not canonical JSON"):
        replace(event, canonical_payload_json=noncanonical)


def test_naive_intervention_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_canonical_water_exchange_event_v1(
            project_id=uuid4(),
            event_id=uuid4(),
            intervention=_intervention(),
            occurred_at=datetime(2026, 8, 15, 12, 0, tzinfo=UTC).replace(tzinfo=None),
        )


def test_store_ignores_unrelated_generic_journal_events(tmp_path: Any) -> None:
    path = tmp_path / "events.jsonl"
    generic = JsonlJournalEventStore(path)
    generic.append(
        JournalEvent(
            event_id=uuid4(),
            project_id=uuid4(),
            event_type=JournalEventType.NOTE,
            title="Unrelated note",
            occurred_at=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
        )
    )
    canonical = build_canonical_observation_event_v1(
        project_id=uuid4(),
        observation=_observation(),
    )
    store = CanonicalProjectEventStoreV1(path)
    store.append(canonical)

    assert store.all() == (canonical,)


def test_malformed_claimed_canonical_journal_event_fails_closed(
    tmp_path: Any,
) -> None:
    path = tmp_path / "events.jsonl"
    generic = JsonlJournalEventStore(path)
    generic.append(
        JournalEvent(
            event_id=uuid4(),
            project_id=uuid4(),
            event_type=JournalEventType.OBSERVATION,
            title="Malformed claimed canonical event",
            occurred_at=datetime(2026, 8, 15, 11, 0, tzinfo=UTC),
            tags=(CANONICAL_PROJECT_EVENT_TAG_V1,),
            payload=(("canonical_payload_json", "{}"),),
        )
    )

    with pytest.raises(ValueError, match="missing attribute"):
        CanonicalProjectEventStoreV1(path).all()


def test_water_exchange_event_preserves_n4_intervention_identity() -> None:
    intervention = _intervention()
    event = build_canonical_water_exchange_event_v1(
        project_id=uuid4(),
        event_id=uuid4(),
        intervention=intervention,
        occurred_at=datetime(2026, 8, 15, 13, 0, tzinfo=UTC),
    )
    payload = event.canonical_payload
    assert payload["intervention_sha256"] == intervention.canonical_sha256
    assert payload["intervention"] == intervention.canonical_payload()


def test_outer_event_metadata_tamper_is_rejected_by_event_sha() -> None:
    event = build_canonical_water_exchange_event_v1(
        project_id=uuid4(),
        event_id=uuid4(),
        intervention=_intervention(),
        occurred_at=datetime(2026, 8, 15, 13, 0, tzinfo=UTC),
    )
    journal_event = event.to_journal_event()
    tampered = JournalEvent(
        event_id=journal_event.event_id,
        project_id=journal_event.project_id,
        event_type=journal_event.event_type,
        title=journal_event.title,
        occurred_at=journal_event.occurred_at + timedelta(minutes=1),
        description=journal_event.description,
        references=journal_event.references,
        tags=journal_event.tags,
        attributes=journal_event.attributes,
        payload=journal_event.payload,
        recorded_at=journal_event.recorded_at,
    )
    with pytest.raises(ValueError, match="event envelope SHA-256"):
        canonical_project_event_from_journal_event_v1(tampered)


def test_semantically_invalid_rehashed_observation_still_fails_closed() -> None:
    event = build_canonical_observation_event_v1(
        project_id=uuid4(),
        observation=_observation(),
    )
    payload = event.canonical_payload
    quantity = payload["quantity"]
    assert isinstance(quantity, dict)
    basis = quantity["basis"]
    assert isinstance(basis, dict)
    basis["reference_id"] = "different-observation"

    from ecobiome.knowledge_persistence.serialization import (
        canonical_json_text,
        canonical_sha256,
    )

    payload_json = canonical_json_text(payload)
    payload_sha = canonical_sha256(payload)
    envelope = event.canonical_event_payload()
    envelope["canonical_payload_sha256"] = payload_sha
    event_sha = canonical_sha256(envelope)

    with pytest.raises(ValueError, match="basis reference"):
        CanonicalProjectEventV1(
            project_id=event.project_id,
            event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            subject_id=event.subject_id,
            payload_schema_version=event.payload_schema_version,
            canonical_payload_json=payload_json,
            canonical_payload_sha256=payload_sha,
            canonical_event_sha256=event_sha,
        )
