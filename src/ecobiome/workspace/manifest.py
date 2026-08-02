"""Persistent metadata describing one EcoBiome project workspace."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from ecobiome.workspace.project_type import ProjectType


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectManifest:
    """Describe one durable EcoBiome project."""

    name: str
    project_type: ProjectType
    description: str = ""
    project_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    tags: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        """Validate and normalize project metadata."""
        name = self.name.strip()
        description = self.description.strip()

        if not name:
            raise ValueError(
                "Project name cannot be empty."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "Project creation timestamp must be timezone-aware."
            )

        if self.updated_at.tzinfo is None:
            raise ValueError(
                "Project update timestamp must be timezone-aware."
            )

        if self.updated_at < self.created_at:
            raise ValueError(
                "Project update timestamp cannot precede creation."
            )

        if self.schema_version <= 0:
            raise ValueError(
                "Project schema version must be positive."
            )

        normalized_tags = tuple(
            dict.fromkeys(
                tag.strip().lower()
                for tag in self.tags
                if tag.strip()
            )
        )

        normalized_attributes: dict[str, str] = {}

        for raw_key, raw_value in self.attributes:
            key = raw_key.strip()
            value = raw_value.strip()

            if not key:
                raise ValueError(
                    "Project attribute keys cannot be empty."
                )

            normalized_attributes[key] = value

        object.__setattr__(self, "name", name)
        object.__setattr__(
            self,
            "description",
            description,
        )
        object.__setattr__(
            self,
            "tags",
            normalized_tags,
        )
        object.__setattr__(
            self,
            "attributes",
            tuple(normalized_attributes.items()),
        )

    @property
    def attribute_map(self) -> dict[str, str]:
        """Return project attributes as a new dictionary."""
        return dict(self.attributes)

    def updated(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tags: tuple[str, ...] | None = None,
        attributes: tuple[tuple[str, str], ...] | None = None,
        updated_at: datetime | None = None,
    ) -> ProjectManifest:
        """Return an updated immutable manifest."""
        return replace(
            self,
            name=self.name if name is None else name,
            description=(
                self.description
                if description is None
                else description
            ),
            tags=self.tags if tags is None else tags,
            attributes=(
                self.attributes
                if attributes is None
                else attributes
            ),
            updated_at=(
                utc_now()
                if updated_at is None
                else updated_at
            ),
        )
