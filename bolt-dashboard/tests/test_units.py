"""Tests for physical measurements and unit conversions."""

import pytest

from ecobiome.core.units import Measurement


def test_convert_liters_to_cubic_meters() -> None:
    volume = Measurement(300, "liter")

    converted = volume.to("meter ** 3")

    assert converted.value == pytest.approx(0.300)
    assert converted.unit == "meter ** 3"


def test_add_different_compatible_volume_units() -> None:
    first_volume = Measurement(30, "liter")
    second_volume = Measurement(2, "meter ** 3")

    total = first_volume + second_volume

    assert total.value == pytest.approx(2030.0)
    assert total.unit == "liter"


def test_convert_celsius_to_kelvin() -> None:
    temperature = Measurement(22, "degC")

    converted = temperature.to("kelvin")

    assert converted.value == pytest.approx(295.15)
    assert converted.unit == "kelvin"


def test_convert_flow_rate() -> None:
    flow_rate = Measurement(20, "meter ** 3 / hour")

    converted = flow_rate.to("liter / hour")

    assert converted.value == pytest.approx(20_000.0)
    assert converted.unit == "liter / hour"


def test_measurements_report_dimensional_compatibility() -> None:
    liters = Measurement(300, "liter")
    cubic_meters = Measurement(0.3, "meter ** 3")
    temperature = Measurement(22, "degC")

    assert liters.is_compatible_with(cubic_meters) is True
    assert liters.is_compatible_with(temperature) is False


def test_incompatible_addition_is_rejected() -> None:
    volume = Measurement(300, "liter")
    temperature = Measurement(22, "degC")

    with pytest.raises(ValueError, match="Cannot add"):
        _ = volume + temperature


def test_measurement_requires_unit() -> None:
    with pytest.raises(ValueError, match="requires a unit"):
        Measurement(300, "   ")
