"""Ecological study domain model."""

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4


class StudyOrigin(StrEnum):
    """Origin of the ecological system represented by a study."""

    EXISTING = "existing"
    DESIGNED = "designed"
    HYPOTHETICAL = "hypothetical"
    HISTORICAL = "historical"


@dataclass(slots=True)
class Study:
    """Represent one ecological system being observed or designed."""

    name: str
    origin: StudyOrigin
    description: str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Validate the study after initialization."""
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("A study must have a non-empty name.")