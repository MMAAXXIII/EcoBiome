"""Tests for KnowledgeRegistry."""

from ecobiome.knowledge import (
    KnowledgeRegistry,
    ScientificRelation,
    ScientificVariable,
)


def make_registry() -> KnowledgeRegistry:
    registry = KnowledgeRegistry()

    registry.add_variable(
        ScientificVariable(
            identifier="physics.water_volume",
            name="Water Volume",
            description="Volume of water.",
        )
    )

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

    return registry


def test_find_relations_from_variable() -> None:
    registry = make_registry()

    relations = registry.relations_from(
        "physics.water_volume"
    )

    assert len(relations) == 1

    assert (
        relations[0].target
        == "physics.thermal_inertia"
    )


def test_unknown_variable_has_no_relations() -> None:
    registry = make_registry()

    assert registry.relations_from(
        "physics.unknown"
    ) == []
