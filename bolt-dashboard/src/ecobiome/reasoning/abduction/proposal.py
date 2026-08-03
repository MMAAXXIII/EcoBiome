"""Provisional explanations generated through abductive reasoning."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class HypothesisProposal:
    """Represent one ranked but unconfirmed scientific explanation."""

    identifier: str
    title: str
    statement: str
    confidence: float
    source_rule: str
    supporting_observation_ids: tuple[UUID, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        """Validate and normalize the proposal."""
        identifier = self.identifier.strip()
        title = self.title.strip()
        statement = self.statement.strip()
        source_rule = self.source_rule.strip()
        rationale = self.rationale.strip()

        if not identifier:
            raise ValueError(
                "A hypothesis proposal requires an identifier."
            )

        if "." not in identifier:
            raise ValueError(
                "Hypothesis proposal identifier must contain "
                "a domain prefix."
            )

        if not title:
            raise ValueError(
                "A hypothesis proposal requires a title."
            )

        if not statement:
            raise ValueError(
                "A hypothesis proposal requires a statement."
            )

        if not source_rule:
            raise ValueError(
                "A hypothesis proposal requires a source rule."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Hypothesis proposal confidence must be "
                "between 0 and 1."
            )

        observation_ids = tuple(
            dict.fromkeys(self.supporting_observation_ids)
        )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "statement", statement)
        object.__setattr__(self, "source_rule", source_rule)
        object.__setattr__(self, "rationale", rationale)
        object.__setattr__(
            self,
            "supporting_observation_ids",
            observation_ids,
        )
