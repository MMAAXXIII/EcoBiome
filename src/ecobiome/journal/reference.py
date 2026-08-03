"""Generic links between journal entries and EcoBiome entities."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class JournalReference:
    """Reference an entity without coupling the journal to its module."""

    entity_type: str
    entity_id: UUID
    relation: str = "related"

    def __post_init__(self) -> None:
        """Validate and normalize one journal reference."""
        entity_type = self.entity_type.strip().lower()
        relation = self.relation.strip().lower()

        if not entity_type:
            raise ValueError(
                "Journal reference entity type cannot be empty."
            )

        if not relation:
            raise ValueError(
                "Journal reference relation cannot be empty."
            )

        object.__setattr__(
            self,
            "entity_type",
            entity_type,
        )
        object.__setattr__(
            self,
            "relation",
            relation,
        )
