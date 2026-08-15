"""Compatibility adapter from legacy observations to canonical N4 quantities."""
from __future__ import annotations

import math
from dataclasses import dataclass

from ecobiome.core.observation.measurement import ScientificMeasurement
from ecobiome.core.observation.observation import Observation
from ecobiome.knowledge_persistence.serialization import normalize_decimal
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    QuantityBasisV1,
)


@dataclass(frozen=True, slots=True)
class ObservationAdapterResultV1:
    quantity: CanonicalQuantityV1
    warnings: tuple[str, ...] = ()


def _legacy_number_to_decimal_text(value: float) -> tuple[str, tuple[str, ...]]:
    if isinstance(value, bool):
        raise TypeError("boolean observations are not quantitative N4 inputs")
    if isinstance(value, int):
        return normalize_decimal(value), ()
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("legacy float observation must be finite")
        return normalize_decimal(str(value)), ("legacy_native_float_canonicalized",)
    raise TypeError(f"unsupported quantitative observation value: {type(value)!r}")


def canonicalize_observation_v1(
    observation: Observation,
    *,
    zone_id: str | None = None,
    material_component_id: str | None = None,
) -> ObservationAdapterResultV1:
    """Create one canonical quantity while retaining the observation identity."""
    warnings: tuple[str, ...]
    if isinstance(observation.value, ScientificMeasurement):
        value_text, warnings = _legacy_number_to_decimal_text(
            observation.value.quantity.value
        )
        unit = observation.value.quantity.unit
    elif isinstance(observation.value, (int, float)) and not isinstance(
        observation.value, bool
    ):
        value_text, warnings = _legacy_number_to_decimal_text(observation.value)
        unit = "dimensionless"
    else:
        raise TypeError(
            "only quantitative legacy observations can become canonical N4 quantities"
        )

    basis = QuantityBasisV1(
        kind="observation",
        reference_id=str(observation.observation_id),
        note=(
            f"source={observation.source}; "
            f"method={observation.acquisition_method.value}; "
            f"observed_at={observation.observed_at.isoformat()}"
        ),
    )
    return ObservationAdapterResultV1(
        quantity=CanonicalQuantityV1(
            variable_id=observation.variable_id,
            value_decimal=value_text,
            unit=unit,
            basis=basis,
            zone_id=zone_id,
            material_component_id=material_component_id,
        ),
        warnings=warnings,
    )
