"""Scientific hypotheses built from traceable observations."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class HypothesisStatus(StrEnum):
    """Lifecycle status of a scientific hypothesis."""

    PENDING = "pending"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    CONFIRMED = "confirmed"


@dataclass(frozen=True, slots=True, kw_only=True)
class Hypothesis:
    """Represent one provisional scientific explanation."""

    identifier: str
    title: str
    statement: str
    confidence: float = 0.0
    status: HypothesisStatus = HypothesisStatus.PENDING
    supporting_observation_ids: tuple[UUID, ...] = ()
    hypothesis_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate and normalize the hypothesis."""
        identifier = self.identifier.strip()
        title = self.title.strip()
        statement = self.statement.strip()

        if not identifier:
            raise ValueError("A hypothesis requires an identifier.")

        if "." not in identifier:
            raise ValueError(
                "Hypothesis identifier must contain a domain prefix."
            )

        if not title:
            raise ValueError("A hypothesis requires a title.")

        if not statement:
            raise ValueError("A hypothesis requires a statement.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Hypothesis confidence must be between 0 and 1."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Hypothesis created_at must include a timezone."
            )

        if self.updated_at.tzinfo is None:
            raise ValueError(
                "Hypothesis updated_at must include a timezone."
            )

        if self.updated_at < self.created_at:
            raise ValueError(
                "Hypothesis updated_at cannot precede created_at."
            )

        unique_observation_ids = tuple(
            dict.fromkeys(self.supporting_observation_ids)
        )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "statement", statement)
        object.__setattr__(
            self,
            "supporting_observation_ids",
            unique_observation_ids,
        )

    @property
    def evidence_count(self) -> int:
        """Return the number of distinct supporting observations."""
        return len(self.supporting_observation_ids)

    def revise(
        self,
        *,
        status: HypothesisStatus | None = None,
        confidence: float | None = None,
        supporting_observation_ids: tuple[UUID, ...] | None = None,
        updated_at: datetime | None = None,
    ) -> Hypothesis:
        """Return a revised immutable hypothesis."""
        return replace(
            self,
            status=status if status is not None else self.status,
            confidence=(
                confidence
                if confidence is not None
                else self.confidence
            ),
            supporting_observation_ids=(
                supporting_observation_ids
                if supporting_observation_ids is not None
                else self.supporting_observation_ids
            ),
            updated_at=updated_at or datetime.now(UTC),
        )
