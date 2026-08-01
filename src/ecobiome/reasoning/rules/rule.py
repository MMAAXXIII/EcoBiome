"""Shared metadata for extensible EcoBiome rules."""

from dataclasses import dataclass
from enum import StrEnum


class RuleDomain(StrEnum):
    """Scientific domain in which a rule operates."""

    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    VISION = "vision"
    HARDWARE = "hardware"
    WEATHER = "weather"
    GENETICS = "genetics"
    ECOLOGY = "ecology"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True, kw_only=True)
class ScientificRule:
    """Shared metadata for every EcoBiome rule."""

    identifier: str
    name: str
    description: str
    domain: RuleDomain
    priority: int = 0
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize rule metadata."""
        identifier = self.identifier.strip()
        name = self.name.strip()
        description = self.description.strip()

        if not identifier:
            raise ValueError("A scientific rule requires an identifier.")

        if "." not in identifier:
            raise ValueError(
                "Rule identifier must contain a domain prefix."
            )

        if not name:
            raise ValueError("A scientific rule requires a name.")

        if not description:
            raise ValueError(
                "A scientific rule requires a description."
            )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
