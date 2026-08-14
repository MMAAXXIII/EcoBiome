"""Source and provenance models for knowledge acquisition."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class SourceType(StrEnum):
    """Supported types of knowledge sources."""

    YOUTUBE = "youtube"
    TRANSCRIPT = "transcript"
    SCIENTIFIC_ARTICLE = "scientific_article"
    BOOK = "book"
    TECHNICAL_REPORT = "technical_report"
    FIELD_OBSERVATION = "field_observation"
    USER_FEEDBACK = "user_feedback"
    OTHER = "other"


class ReviewStatus(StrEnum):
    """Human-review status of imported knowledge."""

    IMPORTED = "imported"
    EXTRACTED = "extracted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    """Describe the provenance of imported knowledge."""

    title: str
    source_type: SourceType
    locator: str
    author: str | None = None
    language: str = "fr"
    description: str = ""
    id: UUID = field(default_factory=uuid4)
    imported_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        """Validate and normalize the source metadata."""
        title = self.title.strip()
        locator = self.locator.strip()
        language = self.language.strip().lower()

        if not title:
            raise ValueError("A knowledge source requires a title.")

        if not locator:
            raise ValueError("A knowledge source requires a locator.")

        if not language:
            raise ValueError("A knowledge source requires a language.")

        object.__setattr__(self, "title", title)
        object.__setattr__(self, "locator", locator)
        object.__setattr__(self, "language", language)

        if self.author is not None:
            object.__setattr__(self, "author", self.author.strip())

        object.__setattr__(self, "description", self.description.strip())
