"""Models for claims extracted from knowledge sources."""

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from ecobiome.knowledge_acquisition.source import ReviewStatus


class ClaimKind(StrEnum):
    """Semantic category of an extracted claim."""

    OBSERVATION = "observation"
    MECHANISM = "mechanism"
    CAUSAL_RELATION = "causal_relation"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    HYPOTHESIS = "hypothesis"
    OPINION = "opinion"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExtractedClaim:
    """Represent one unverified statement extracted from a source."""

    source_id: UUID
    text: str
    kind: ClaimKind = ClaimKind.UNKNOWN
    confidence: float = 0.0
    status: ReviewStatus = ReviewStatus.EXTRACTED
    notes: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate the extracted claim."""
        text = self.text.strip()

        if not text:
            raise ValueError("An extracted claim requires text.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Claim confidence must be between 0 and 1.")

        object.__setattr__(self, "text", text)
        object.__setattr__(self, "notes", self.notes.strip())
