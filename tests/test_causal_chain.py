"""Tests for multi-step causal-chain reasoning."""

from pathlib import Path

import pytest

from ecobiome.knowledge.directory_loader import load_knowledge_directory
from ecobiome.reasoning import CausalChainEngine

KNOWLEDGE_BASE = Path("src/ecobiome/knowledge/base")


def test_trace_complete_causal_chain() -> None:
    registry = load_knowledge_directory(KNOWLEDGE_BASE)
    engine = CausalChainEngine(registry)

    result = engine.trace_to("physics.temperature_fluctuation")

    assert result.found is True
    assert tuple(step.relation_id for step in result.steps) == (
        "physics.water_volume.increases_thermal_inertia",
        (
            "physics.thermal_inertia."
            "decreases_temperature_fluctuation"
        ),
    )

    assert result.steps[0].source == "physics.water_volume"
    assert result.steps[-1].target == "physics.temperature_fluctuation"
    assert "physics.thermal_inertia" in result.text


def test_depth_limit_stops_upstream_traversal() -> None:
    registry = load_knowledge_directory(KNOWLEDGE_BASE)
    engine = CausalChainEngine(registry)

    result = engine.trace_to(
        "physics.temperature_fluctuation",
        maximum_depth=1,
    )

    assert len(result.steps) == 1
    assert result.steps[0].source == "physics.thermal_inertia"


def test_unknown_target_has_no_chain() -> None:
    registry = load_knowledge_directory(KNOWLEDGE_BASE)
    engine = CausalChainEngine(registry)

    result = engine.trace_to("biology.unknown")

    assert result.found is False
    assert result.steps == ()


def test_chain_rejects_invalid_depth() -> None:
    registry = load_knowledge_directory(KNOWLEDGE_BASE)
    engine = CausalChainEngine(registry)

    with pytest.raises(
        ValueError,
        match="maximum_depth must be greater than zero",
    ):
        engine.trace_to(
            "physics.temperature_fluctuation",
            maximum_depth=0,
        )
