"""Tests for causal explanations."""

import pytest

from ecobiome.knowledge import KnowledgeRegistry, ScientificRelation
from ecobiome.reasoning import ExplanationEngine


def make_registry() -> KnowledgeRegistry:
    """Create a registry containing one causal relation."""
    registry = KnowledgeRegistry()

    registry.add_relation(
        ScientificRelation(
            identifier=(
                "physics.water_volume."
                "increases_thermal_inertia"
            ),
            source="physics.water_volume",
            target="physics.thermal_inertia",
            effect="increases",
            strength="strong",
            confidence="high",
            explanation=(
                "A larger water volume stores more thermal energy "
                "and therefore increases thermal inertia."
            ),
        )
    )

    return registry


def test_explain_why_target_is_influenced() -> None:
    engine = ExplanationEngine(make_registry())

    result = engine.explain_why("physics.thermal_inertia")

    assert result.found is True
    assert result.target == "physics.thermal_inertia"
    assert "physics.water_volume" in result.text
    assert "increases physics.thermal_inertia" in result.text
    assert result.relation_ids == (
        "physics.water_volume.increases_thermal_inertia",
    )


def test_explain_unknown_target() -> None:
    engine = ExplanationEngine(make_registry())

    result = engine.explain_why("chemistry.unknown")

    assert result.found is False
    assert result.relation_ids == ()
    assert "No causal relation" in result.text


def test_explanation_rejects_empty_target() -> None:
    engine = ExplanationEngine(make_registry())

    with pytest.raises(ValueError, match="target is required"):
        engine.explain_why("   ")
