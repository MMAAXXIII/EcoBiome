"""Load a complete EcoBiome knowledge directory."""

from pathlib import Path

from ecobiome.knowledge.loader import (
    load_scientific_variable,
    load_yaml,
)
from ecobiome.knowledge.registry import KnowledgeRegistry
from ecobiome.knowledge.relation import ScientificRelation


def _required_string(
    data: dict[str, object],
    field_name: str,
    path: Path,
) -> str:
    """Read and validate one required string field."""
    value = data.get(field_name)

    if not isinstance(value, str):
        raise TypeError(
            f"{path}: field {field_name!r} must be a string."
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{path}: field {field_name!r} cannot be empty."
        )

    return normalized


def load_scientific_relation(path: Path) -> ScientificRelation:
    """Load one scientific relation from a YAML file."""
    data = load_yaml(path)

    return ScientificRelation(
        identifier=_required_string(data, "id", path),
        source=_required_string(data, "source", path),
        target=_required_string(data, "target", path),
        effect=_required_string(data, "effect", path),
        strength=_required_string(data, "strength", path),
        confidence=_required_string(data, "confidence", path),
        explanation=_required_string(data, "explanation", path),
    )


def load_knowledge_directory(path: Path) -> KnowledgeRegistry:
    """Load every supported YAML knowledge item below a directory."""
    if not path.is_dir():
        raise NotADirectoryError(
            f"Knowledge directory not found: {path}"
        )

    registry = KnowledgeRegistry()

    variable_paths = sorted(
        candidate
        for candidate in path.rglob("*.yaml")
        if "variables" in candidate.parts
    )

    relation_paths = sorted(
        candidate
        for candidate in path.rglob("*.yaml")
        if "relations" in candidate.parts
    )

    for variable_path in variable_paths:
        registry.add_variable(
            load_scientific_variable(variable_path)
        )

    for relation_path in relation_paths:
        registry.add_relation(
            load_scientific_relation(relation_path)
        )

    return registry
