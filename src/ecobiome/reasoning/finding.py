"""Traceable scientific findings produced by EcoBiome reasoning."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class FindingSeverity(StrEnum):
    """Scientific or operational severity of a finding."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True, kw_only=True)
class Finding:
    """Represent one evidence-based scientific conclusion."""

    identifier: str
    title: str
    statement: str
    severity: FindingSeverity
    confidence: float
    supporting_hypothesis_ids: tuple[UUID, ...] = ()
    supporting_observation_ids: tuple[UUID, ...] = ()
    finding_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate and normalize the scientific finding."""
        identifier = self.identifier.strip()
        title = self.title.strip()
        statement = self.statement.strip()

        if not identifier:
            raise ValueError("A finding requires an identifier.")

        if "." not in identifier:
            raise ValueError(
                "Finding identifier must contain a domain prefix."
            )

        if not title:
            raise ValueError("A finding requires a title.")

        if not statement:
            raise ValueError("A finding requires a statement.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Finding confidence must be between 0 and 1."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Finding created_at must include a timezone."
            )

        hypothesis_ids = tuple(
            dict.fromkeys(self.supporting_hypothesis_ids)
        )
        observation_ids = tuple(
            dict.fromkeys(self.supporting_observation_ids)
        )

        if not hypothesis_ids and not observation_ids:
            raise ValueError(
                "A finding requires at least one supporting "
                "hypothesis or observation."
            )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "statement", statement)
        object.__setattr__(
            self,
            "supporting_hypothesis_ids",
            hypothesis_ids,
        )
        object.__setattr__(
            self,
            "supporting_observation_ids",
            observation_ids,
        )

    @property
    def evidence_count(self) -> int:
        """Return the total number of distinct supporting records."""
        return (
            len(self.supporting_hypothesis_ids)
            + len(self.supporting_observation_ids)
        )

    @property
    def requires_immediate_attention(self) -> bool:
        """Return whether the finding has urgent severity."""
        return self.severity in {
            FindingSeverity.HIGH,
            FindingSeverity.CRITICAL,
        }
