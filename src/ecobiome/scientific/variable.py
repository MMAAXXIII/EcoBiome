"""Scientific variables."""

from dataclasses import dataclass


@dataclass(slots=True)
class ScientificVariable:
    """Describe a scientific variable independently of its current value."""

    identifier: str
    name: str
    description: str