"""Validated and traceable scientific knowledge."""

from dataclasses import dataclass
from enum import StrEnum


class KnowledgeStatus(StrEnum):
    """Lifecycle status of scientific knowledge."""

    CANDIDATE = "candidate"
    UNDER_REVIEW = "under_review"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class Knowledge:
    """Represent one traceable scientific knowledge item."""

    identifier: str
    title: str
    statement: str
    domain: str
    status: KnowledgeStatus = KnowledgeStatus.CANDIDATE
    confidence: float = 0.0
    source_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate and normalize the knowledge item."""
        identifier = self.identifier.strip()
        title = self.title.strip()
        statement = self.statement.strip()
        domain = self.domain.strip().lower()

        if not identifier or "." not in identifier:
            raise ValueError(
                "Knowledge identifier must contain a domain prefix."
            )

        if not title:
            raise ValueError("Knowledge requires a title.")

        if not statement:
            raise ValueError("Knowledge requires a statement.")

        if not domain:
            raise ValueError("Knowledge requires a domain.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Knowledge confidence must be between 0 and 1."
            )

        if (
            self.status is KnowledgeStatus.VALIDATED
            and not self.source_ids
            and not self.claim_ids
        ):
            raise ValueError(
                "Validated knowledge requires at least one source or claim."
            )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "statement", statement)
        object.__setattr__(self, "domain", domain)
