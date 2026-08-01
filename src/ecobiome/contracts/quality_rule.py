"""Neutral contract for observation-quality rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ecobiome.core.observation.observation import Observation
    from ecobiome.core.observation.quality import QualityAssessment


class QualityRule(Protocol):
    """Structurally describe an observation-quality rule."""

    identifier: str

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        """Assess the reliability of one observation."""
