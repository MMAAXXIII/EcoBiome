"""Contract for rules producing scientific evidence."""

from typing import Protocol

from ecobiome.core.observation import Observation
from ecobiome.reasoning.evidence import Evidence
from ecobiome.reasoning.rules.rule import RuleDomain


class EvidenceRule(Protocol):
    """Structurally describe an evidence-producing rule."""

    identifier: str
    domain: RuleDomain
    priority: int
    enabled: bool

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        """Produce evidence from one observation."""
