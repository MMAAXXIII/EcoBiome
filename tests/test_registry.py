"""Tests for KnowledgeRegistry."""

from ecobiome.knowledge import (
    KnowledgeRegistry,
    ScientificRelation,
    ScientificVariable,
)


def test_registry_accepts_relation() -> None:
    registry = KnowledgeRegistry()

    registry.add_variable(
        ScientificVariable(
            identifier="physics.water_volume",
            name="Water volume",
            description="Volume of water",
        )
    )

    relation = ScientificRelation(
        identifier="physics.water_volume.increases_thermal_inertia",
        source="physics.water_volume",
        target="physics.thermal_inertia",
        effect="increases",
        strength="strong",
        confidence="high",
        explanation="Volume increases thermal inertia.",
    )

    registry.add_relation(relation)

    assert len(registry.relations) == 1
    assert registry.relations[0].source == "physics.water_volume"
