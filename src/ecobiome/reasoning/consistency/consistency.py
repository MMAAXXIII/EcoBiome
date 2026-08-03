"""Core consistency assessment primitives."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ConsistencyStatus(StrEnum):
    """Possible consistency states."""

    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    UNKNOWN = "unknown"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConsistencyAssessment:
    """Describe the consistency between one or more observations."""

    status: ConsistencyStatus
    confidence: float
    involved_observations: tuple[UUID, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        """Validate the assessment."""

        if isinstance(self.confidence, bool) or not isinstance(
            self.confidence,
            int | float,
        ):
            raise TypeError(
                "Consistency confidence must be numeric."
            )

        confidence = float(self.confidence)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "Consistency confidence must be between 0 and 1."
            )

        object.__setattr__(self, "confidence", confidence)

    @property
    def is_consistent(self) -> bool:
        """Return whether observations are mutually consistent."""
        return self.status is ConsistencyStatus.CONSISTENT

    @property
    def requires_attention(self) -> bool:
        """Return whether the assessment deserves investigation."""
        return self.status is ConsistencyStatus.INCONSISTENT
