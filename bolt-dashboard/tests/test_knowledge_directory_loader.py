"""Tests for automatic knowledge-directory loading."""

from pathlib import Path

import pytest

from ecobiome.knowledge.directory_loader import (
    load_knowledge_directory,
    load_scientific_relation,
)
from ecobiome.reasoning import ExplanationEngine

KNOWLEDGE_BASE = Path("src/ecobiome/knowledge/base")

RELATION_PATH = (
    KNOWLEDGE_BASE
    / "physics"
    / "relations"
    / "water_volume_increases_thermal_inertia.yaml"
)


def test_load_scientific_relation_from_yaml() -> None:
    relation = load_scientific_relation(RELATION_PATH)

    assert relation.source == "physics.water_volume"
    assert relation.target == "physics.thermal_inertia"
    assert relation.effect == "increases"


def test_load_complete_knowledge_directory() -> None:
    registry = load_knowledge_directory(KNOWLEDGE_BASE)

    assert "physics.water_volume" in registry.variables
    assert len(registry.relations) >= 1


def test_loaded_knowledge_can_generate_explanation() -> None:
    registry = load_knowledge_directory(KNOWLEDGE_BASE)
    engine = ExplanationEngine(registry)

    result = engine.explain_why("physics.thermal_inertia")

    assert result.found is True
    assert "physics.water_volume" in result.text
    assert (
        "physics.water_volume.increases_thermal_inertia"
        in result.relation_ids
    )


def test_missing_knowledge_directory_is_rejected(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing"

    with pytest.raises(
        NotADirectoryError,
        match="Knowledge directory not found",
    ):
        load_knowledge_directory(missing_path)
