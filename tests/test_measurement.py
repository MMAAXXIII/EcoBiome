"""Tests for scientific measurements."""

import pytest

from ecobiome.core.observation import ScientificMeasurement
from ecobiome.core.units import Measurement


def test_measurement_bounds() -> None:
    measurement = ScientificMeasurement(
        quantity=Measurement(23.5, "degC"),
        uncertainty=0.2,
    )

    assert measurement.lower_bound.value == pytest.approx(23.3)
    assert measurement.upper_bound.value == pytest.approx(23.7)
    assert measurement.lower_bound.unit == "degC"
    assert measurement.upper_bound.unit == "degC"


def test_zero_uncertainty() -> None:
    measurement = ScientificMeasurement(
        quantity=Measurement(7.0, "dimensionless"),
    )

    assert measurement.lower_bound.value == pytest.approx(7.0)
    assert measurement.upper_bound.value == pytest.approx(7.0)


def test_uncertainty_uses_quantity_unit() -> None:
    measurement = ScientificMeasurement(
        quantity=Measurement(1.0, "meter"),
        uncertainty=0.1,
    )

    assert measurement.lower_bound.value == pytest.approx(0.9)
    assert measurement.upper_bound.value == pytest.approx(1.1)
    assert measurement.lower_bound.unit == "meter"


def test_negative_uncertainty_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        ScientificMeasurement(
            quantity=Measurement(20.0, "meter"),
            uncertainty=-0.1,
        )
