"""EcoBiome project domain model."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ecobiome.core.study import Study


@dataclass(slots=True)
class Project:
    """Group one or more related ecological studies."""

    name: str
    description: str = ""
    id: UUID = field(default_factory=uuid4)
    studies: list[Study] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the project after initialization."""
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("A project must have a non-empty name.")

    def add_study(self, study: Study) -> None:
        """Attach a study while preventing duplicate identifiers."""
        if any(existing.id == study.id for existing in self.studies):
            raise ValueError(f"Study {study.id} is already part of this project.")

        self.studies.append(study)