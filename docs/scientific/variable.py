"""Scientific variable definitions."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScientificVariable:
    """Describe a scientific variable independently of its current value."""

    identifier: str
    name: str
    description: str
    unit: str | None = None
    display_unit: str | None = None
    category: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize the variable definition."""
        identifier = self.identifier.strip()
        name = self.name.strip()
        description = self.description.strip()

        if not identifier:
            raise ValueError("A scientific variable requires an identifier.")

        if "." not in identifier:
            raise ValueError(
                "A scientific variable identifier must contain a domain prefix."
            )

        if not name:
            raise ValueError("A scientific variable requires a name.")

        if not description:
            raise ValueError("A scientific variable requires a description.")

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)