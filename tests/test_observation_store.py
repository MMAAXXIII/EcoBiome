"""Tests for scientific observation storage."""

from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    InMemoryObservationStore,
    Observation,
    ScientificMeasurement,
)
from ecobiome.core.units import Measurement
from ecobiome.knowledge.variable import ScientificVariable

OBSERVATION_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)


def make_observation(
    *,
    observation_id: UUID = OBSERVATION_ID,
) -> Observation:
    """Create one deterministic temperature observation."""
    variable = ScientificVariable(
        identifier="physics.water_temperature",
        name="Water temperature",
        description="Temperature of the water body.",
        unit="kelvin",
        display_unit="degC",
        category="physics",
    )

    return Observation(
        observation_id=observation_id,
        source="DS18B20-01",
        variable=variable,
        value=ScientificMeasurement(
            quantity=Measurement(23.5, "degC"),
            uncertainty=0.1,
        ),
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
    )


def test_store_appends_and_retrieves_observation() -> None:
    store = InMemoryObservationStore()
    observation = make_observation()

    store.append(observation)

    assert store.count == 1
    assert store.contains(observation.observation_id) is True
    assert store.get(observation.observation_id) == observation
    assert store.load() == (observation,)


def test_store_preserves_insertion_order() -> None:
    first = make_observation()

    second = make_observation(
        observation_id=UUID(
            "87654321-4321-8765-4321-876543218765"
        )
    )

    store = InMemoryObservationStore([first, second])

    assert store.load() == (first, second)


def test_duplicate_identifier_is_rejected() -> None:
    store = InMemoryObservationStore()
    observation = make_observation()

    store.append(observation)

    with pytest.raises(ValueError, match="already stored"):
        store.append(observation)

    assert store.count == 1


def test_unknown_observation_is_reported() -> None:
    store = InMemoryObservationStore()

    unknown_id = UUID(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )

    with pytest.raises(KeyError, match="Unknown observation"):
        store.get(unknown_id)


def test_clear_removes_observations_and_index() -> None:
    store = InMemoryObservationStore()
    observation = make_observation()

    store.append(observation)
    store.clear()

    assert store.count == 0
    assert store.load() == ()
    assert store.contains(observation.observation_id) is False
