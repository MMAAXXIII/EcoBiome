"""Safe physical measurements and unit conversions."""

from dataclasses import dataclass

from pint import DimensionalityError, UnitRegistry
from pint.registry import UnitRegistry as UnitRegistryType

_UNITS: UnitRegistryType = UnitRegistry()


@dataclass(frozen=True, slots=True)
class Measurement:
    """Represent a numerical value accompanied by a physical unit."""

    value: float
    unit: str

    def __post_init__(self) -> None:
        """Validate and normalize the measurement."""
        unit = self.unit.strip()

        if not unit:
            raise ValueError("A measurement requires a unit.")

        try:
            _UNITS.Quantity(self.value, unit)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Unknown or invalid unit: {unit!r}.") from error

        object.__setattr__(self, "value", float(self.value))
        object.__setattr__(self, "unit", unit)

    def to(self, unit: str) -> Measurement:
        """Convert this measurement to a compatible unit."""
        target_unit = unit.strip()

        if not target_unit:
            raise ValueError("A target unit is required.")

        try:
            converted = _UNITS.Quantity(
                self.value,
                self.unit,
            ).to(target_unit)
        except DimensionalityError as error:
            raise ValueError(
                f"Cannot convert {self.unit!r} to {target_unit!r}."
            ) from error

        return Measurement(
            value=float(converted.magnitude),
            unit=str(converted.units),
        )

    def to_si(self) -> Measurement:
        """Convert this measurement to coherent SI base units."""
        converted = _UNITS.Quantity(
            self.value,
            self.unit,
        ).to_base_units()

        return Measurement(
            value=float(converted.magnitude),
            unit=str(converted.units),
        )

    def is_compatible_with(self, other: Measurement) -> bool:
        """Return whether two measurements share the same dimension."""
        first = _UNITS.Quantity(self.value, self.unit)
        second = _UNITS.Quantity(other.value, other.unit)

        return bool(first.is_compatible_with(second))

    def __add__(self, other: Measurement) -> Measurement:
        """Add a compatible measurement and preserve this unit."""
        try:
            result = (
                _UNITS.Quantity(self.value, self.unit)
                + _UNITS.Quantity(other.value, other.unit)
            )
        except DimensionalityError as error:
            raise ValueError(
                f"Cannot add {self.unit!r} and {other.unit!r}."
            ) from error

        converted = result.to(self.unit)

        return Measurement(
            value=float(converted.magnitude),
            unit=str(converted.units),
        )

    def __sub__(self, other: Measurement) -> Measurement:
        """Subtract a compatible measurement and preserve this unit."""
        try:
            result = (
                _UNITS.Quantity(self.value, self.unit)
                - _UNITS.Quantity(other.value, other.unit)
            )
        except DimensionalityError as error:
            raise ValueError(
                f"Cannot subtract {other.unit!r} from {self.unit!r}."
            ) from error

        converted = result.to(self.unit)

        return Measurement(
            value=float(converted.magnitude),
            unit=str(converted.units),
        )
