"""Neutral contract for observation-quality rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ecobiome.core.observation.observation import Observation
    from ecobiome.core.observation.quality import QualityAssessment


class QualityRule(Protocol):
    """Structurally describe an observation-quality rule."""

    @property
    def identifier(self) -> str:
        """Return the component identifier."""
        ...

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        """Assess the reliability of one observation."""
