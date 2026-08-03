"""Tests for explanation engine."""

from ecobiome.knowledge import (
    KnowledgeRegistry,
    ScientificRelation,
)


def test_explain_relation() -> None:
    registry = KnowledgeRegistry()

    registry.add_relation(
        ScientificRelation(
            identifier="physics.water_volume.increases_thermal_inertia",
            source="physics.water_volume",
            target="physics.thermal_inertia",
            effect="increases",
            strength="strong",
            confidence="high",
            explanation="Volume increases thermal inertia.",
        )
    )

    explanation = registry.explain("physics.water_volume")

    assert "thermal_inertia" in explanation
    assert "Volume increases thermal inertia." in explanation


def test_explain_unknown_variable() -> None:
    registry = KnowledgeRegistry()

    explanation = registry.explain("physics.unknown")

    assert "No scientific relation found" in explanation
