"""Storage interfaces for scientific observations."""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from ecobiome.core.observation.observation import Observation


class ObservationStore(Protocol):
    """Storage interface implemented by observation repositories."""

    def append(self, observation: Observation) -> None:
        """Store one scientific observation."""

    def get(self, observation_id: UUID) -> Observation:
        """Return one observation from its stable identifier."""

    def contains(self, observation_id: UUID) -> bool:
        """Return whether an observation is already stored."""

    def load(self) -> tuple[Observation, ...]:
        """Return every observation in insertion order."""

    @property
    def count(self) -> int:
        """Return the number of stored observations."""

    def clear(self) -> None:
        """Remove every stored observation."""


class InMemoryObservationStore:
    """Store observations temporarily in process memory."""

    def __init__(
        self,
        observations: Iterable[Observation] = (),
    ) -> None:
        self._observations: list[Observation] = []
        self._by_id: dict[UUID, Observation] = {}

        for observation in observations:
            self.append(observation)

    def append(self, observation: Observation) -> None:
        """Store an observation while rejecting duplicate identifiers."""
        if observation.observation_id in self._by_id:
            raise ValueError(
                f"Observation {observation.observation_id} "
                "is already stored."
            )

        self._observations.append(observation)
        self._by_id[observation.observation_id] = observation

    def get(self, observation_id: UUID) -> Observation:
        """Return one stored observation."""
        try:
            return self._by_id[observation_id]
        except KeyError as error:
            raise KeyError(
                f"Unknown observation: {observation_id}."
            ) from error

    def contains(self, observation_id: UUID) -> bool:
        """Return whether an observation is already stored."""
        return observation_id in self._by_id

    def load(self) -> tuple[Observation, ...]:
        """Return an immutable snapshot in insertion order."""
        return tuple(self._observations)

    @property
    def count(self) -> int:
        """Return the number of stored observations."""
        return len(self._observations)

    def clear(self) -> None:
        """Remove every stored observation."""
        self._observations.clear()
        self._by_id.clear()
