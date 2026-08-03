"""Stable identities for hypotheses tracked across reasoning cycles."""

from uuid import UUID, uuid5

HYPOTHESIS_NAMESPACE = UUID(
    "a8476f30-e21c-4f1d-84a6-99b7df7216c2"
)


def hypothesis_uuid(identifier: str) -> UUID:
    """Return a deterministic UUID for one hypothesis identifier."""
    normalized = identifier.strip()

    if not normalized:
        raise ValueError(
            "A hypothesis identifier cannot be empty."
        )

    if "." not in normalized:
        raise ValueError(
            "Hypothesis identifier must contain a domain prefix."
        )

    return uuid5(
        HYPOTHESIS_NAMESPACE,
        normalized,
    )
