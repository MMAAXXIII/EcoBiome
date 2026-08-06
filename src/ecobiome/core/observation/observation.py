"""Traceable scientific observations."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from ecobiome.core.observation.measurement import ScientificMeasurement
from ecobiome.knowledge.variable import ScientificVariable


class AcquisitionMethod(StrEnum):
    """Method used to acquire an observation."""

    SENSOR = "sensor"
    CAMERA = "camera"
    HUMAN = "human"
    API = "api"
    CALCULATION = "calculation"
    SIMULATION = "simulation"
    AI_INFERENCE = "ai_inference"
    OTHER = "other"


type ObservationValue = ScientificMeasurement | str | bool | int | float


@dataclass(frozen=True, slots=True, kw_only=True)
class Observation:
    """Represent one traceable observation of a scientific variable."""

    source: str
    variable: ScientificVariable
    value: ObservationValue
    acquisition_method: AcquisitionMethod
    confidence: float = 1.0
    raw_reference: str | None = None
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    observation_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate and normalize the observation."""
        source = self.source.strip()

        raw_reference = (
            self.raw_reference.strip()
            if self.raw_reference is not None
            else None
        )

        if not source:
            raise ValueError("An observation requires a source.")

        if isinstance(self.value, str) and not self.value.strip():
            raise ValueError(
                "A textual observation value cannot be empty."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Observation confidence must be between 0 and 1."
            )

        if self.observed_at.tzinfo is None:
            raise ValueError(
                "Observation timestamp must include a timezone."
            )

        object.__setattr__(self, "source", source)
        object.__setattr__(self, "raw_reference", raw_reference)

        if isinstance(self.value, str):
            object.__setattr__(self, "value", self.value.strip())

    @property
    def variable_id(self) -> str:
        """Return the stable identifier of the observed variable."""
        return self.variable.identifier

    @property
    def is_measurement(self) -> bool:
        """Return whether the value is a quantitative measurement."""
        return isinstance(self.value, ScientificMeasurement)
