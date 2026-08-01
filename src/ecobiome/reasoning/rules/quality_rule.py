"""Contract for observation-quality rules."""

from typing import Protocol

from ecobiome.core.observation import (
    Observation,
    QualityAssessment,
)


class QualityRule(Protocol):
    """Structurally describe an observation-quality rule."""

    identifier: str

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        """Assess the reliability of one observation."""
