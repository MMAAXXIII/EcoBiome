"""Scientific measurement primitives."""

from dataclasses import dataclass

from ecobiome.core.units import Measurement as UnitMeasurement


@dataclass(frozen=True, slots=True)
class ScientificMeasurement:
    """Represent one physical quantity with measurement uncertainty."""

    quantity: UnitMeasurement
    uncertainty: float = 0.0

    def __post_init__(self) -> None:
        """Validate and normalize the uncertainty."""
        uncertainty = float(self.uncertainty)

        if uncertainty < 0:
            raise ValueError(
                "Measurement uncertainty cannot be negative."
            )

        object.__setattr__(self, "uncertainty", uncertainty)

    @property
    def lower_bound(self) -> UnitMeasurement:
        """Return the minimum plausible measured value."""
        return UnitMeasurement(
            value=self.quantity.value - self.uncertainty,
            unit=self.quantity.unit,
        )

    @property
    def upper_bound(self) -> UnitMeasurement:
        """Return the maximum plausible measured value."""
        return UnitMeasurement(
            value=self.quantity.value + self.uncertainty,
            unit=self.quantity.unit,
        )
