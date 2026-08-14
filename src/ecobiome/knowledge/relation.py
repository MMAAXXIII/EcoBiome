"""Scientific relationship definitions."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScientificRelation:
    """Describe a directional relationship between scientific variables."""

    identifier: str
    source: str
    target: str
    effect: str
    strength: str
    confidence: str
    explanation: str

    def __post_init__(self) -> None:
        """Validate and normalize the relation."""
        required_fields = (
            "identifier",
            "source",
            "target",
            "effect",
            "strength",
            "confidence",
            "explanation",
        )

        for field_name in required_fields:
            value = getattr(self, field_name).strip()

            if not value:
                raise ValueError(
                    f"A scientific relation requires {field_name!r}."
                )

            object.__setattr__(self, field_name, value)

        if "." not in self.identifier:
            raise ValueError(
                "A scientific relation identifier must contain a domain prefix."
            )
