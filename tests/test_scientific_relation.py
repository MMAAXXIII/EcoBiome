"""Tests for ScientificRelation."""

import pytest

from ecobiome.knowledge import ScientificRelation


def test_create_scientific_relation() -> None:
    relation = ScientificRelation(
        identifier="physics.water_volume.increases_thermal_inertia",
        source="physics.water_volume",
        target="physics.thermal_inertia",
        effect="increases",
        strength="strong",
        confidence="high",
        explanation="Volume increases thermal inertia.",
    )

    assert relation.source == "physics.water_volume"
    assert relation.target == "physics.thermal_inertia"
    assert relation.effect == "increases"


def test_relation_rejects_empty_explanation() -> None:
    with pytest.raises(ValueError, match="explanation"):
        ScientificRelation(
            identifier="physics.example",
            source="physics.source",
            target="physics.target",
            effect="increases",
            strength="strong",
            confidence="high",
            explanation="   ",
        )
