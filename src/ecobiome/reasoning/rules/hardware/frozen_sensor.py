"""Hardware rule detecting sensors that repeatedly return a fixed value."""

from dataclasses import dataclass
from uuid import UUID

from ecobiome.core.observation import (
    Observation,
    ObservationStore,
    ScientificMeasurement,
)
from ecobiome.reasoning.evidence import (
    Evidence,
    EvidenceRelation,
)
from ecobiome.reasoning.rules.rule import ScientificRule


@dataclass(frozen=True, slots=True, kw_only=True)
class FrozenSensorRule(ScientificRule):
    """Detect a source returning nearly constant values for too long."""

    observation_store: ObservationStore
    hypothesis_id: UUID
    minimum_observation_count: int = 5
    minimum_frozen_duration_seconds: float = 300.0
    tolerance: float = 0.0
    evidence_weight: float = 0.75

    def __post_init__(self) -> None:
        """Validate rule metadata and detection parameters."""
        super().__post_init__()

        if self.minimum_observation_count < 2:
            raise ValueError(
                "minimum_observation_count must be at least two."
            )

        if self.minimum_frozen_duration_seconds <= 0:
            raise ValueError(
                "minimum_frozen_duration_seconds must be greater than zero."
            )

        if self.tolerance < 0:
            raise ValueError("tolerance cannot be negative.")

        if not 0.0 <= self.evidence_weight <= 1.0:
            raise ValueError(
                "evidence_weight must be between 0 and 1."
            )

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        """Generate contradictory evidence for a probably frozen sensor."""
        current_value = self._numeric_value(
            observation,
            target_unit=None,
        )

        if current_value is None:
            return ()

        history = self._matching_history(observation)

        observations = (
            *history,
            observation,
        )

        if len(observations) < self.minimum_observation_count:
            return ()

        selected = observations[-self.minimum_observation_count :]
        oldest = selected[0]
        duration_seconds = (
            observation.observed_at - oldest.observed_at
        ).total_seconds()

        if duration_seconds < self.minimum_frozen_duration_seconds:
            return ()

        target_unit = self._measurement_unit(observation)
        values: list[float] = []

        for item in selected:
            value = self._numeric_value(
                item,
                target_unit=target_unit,
            )

            if value is None:
                return ()

            values.append(value)

        variation = max(values) - min(values)

        if variation > self.tolerance:
            return ()

        quality_score = min(
            item.confidence
            for item in selected
        )

        return (
            Evidence(
                observation_id=observation.observation_id,
                hypothesis_id=self.hypothesis_id,
                relation=EvidenceRelation.CONTRADICTS,
                weight=self.evidence_weight,
                quality_score=quality_score,
                explanation=(
                    f"Source {observation.source!r} returned "
                    f"{len(selected)} nearly identical values over "
                    f"{duration_seconds:.1f} seconds. Observed variation "
                    f"was {variation:.6g}, within the configured "
                    f"tolerance of {self.tolerance:.6g}."
                ),
                source_rule=self.identifier,
            ),
        )

    def _matching_history(
        self,
        observation: Observation,
    ) -> tuple[Observation, ...]:
        """Return earlier observations from the same source and variable."""
        matching = (
            item
            for item in self.observation_store.load()
            if item.observation_id != observation.observation_id
            and item.source == observation.source
            and item.variable_id == observation.variable_id
            and item.observed_at <= observation.observed_at
        )

        return tuple(
            sorted(
                matching,
                key=lambda item: (
                    item.observed_at,
                    str(item.observation_id),
                ),
            )
        )

    @staticmethod
    def _measurement_unit(
        observation: Observation,
    ) -> str | None:
        """Return the unit used by a quantitative measurement."""
        if isinstance(observation.value, ScientificMeasurement):
            return observation.value.quantity.unit

        return None

    @staticmethod
    def _numeric_value(
        observation: Observation,
        *,
        target_unit: str | None,
    ) -> float | None:
        """Return a comparable numeric value when supported."""
        value = observation.value

        if isinstance(value, bool):
            return None

        if isinstance(value, int | float):
            return float(value)

        if isinstance(value, ScientificMeasurement):
            quantity = value.quantity

            if target_unit is not None:
                try:
                    quantity = quantity.to(target_unit)
                except ValueError:
                    return None

            return quantity.value

        return None
