"""Tests for ScientificVariable."""

from ecobiome.knowledge.variable import ScientificVariable


def test_create_scientific_variable() -> None:
    variable = ScientificVariable(
        identifier="physics.water_temperature",
        name="Water Temperature",
        description="Temperature of the water.",
    )

    assert variable.identifier == "physics.water_temperature"
    assert variable.name == "Water Temperature"
    assert variable.description == "Temperature of the water."
