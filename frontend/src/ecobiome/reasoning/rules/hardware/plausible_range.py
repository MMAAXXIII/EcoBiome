"""Quality rule validating physically plausible numerical ranges."""

from dataclasses import dataclass

from ecobiome.core.observation import (
    DataQuality,
    DiagnosticCode,
    Observation,
    QualityAssessment,
    ScientificMeasurement,
)
from ecobiome.core.units import Measurement
from ecobiome.reasoning.rules.rule import ScientificRule


@dataclass(frozen=True, slots=True, kw_only=True)
class PlausibleRangeRule(ScientificRule):
    """Reject numerical observations outside a configured plausible range."""

    variable_id: str
    minimum: Measurement
    maximum: Measurement

    def __post_init__(self) -> None:
        """Validate metadata and range configuration."""
        super().__post_init__()

        variable_id = self.variable_id.strip()

        if not variable_id:
            raise ValueError("variable_id cannot be empty.")

        if "." not in variable_id:
            raise ValueError(
                "variable_id must contain a domain prefix."
            )

        if not self.minimum.is_compatible_with(self.maximum):
            raise ValueError(
                "Range boundaries must use compatible dimensions."
            )

        maximum = self.maximum.to(self.minimum.unit)

        if maximum.value < self.minimum.value:
            raise ValueError(
                "Range maximum cannot be lower than minimum."
            )

        object.__setattr__(self, "variable_id", variable_id)
        object.__setattr__(self, "maximum", maximum)

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        """Assess whether one observation is physically plausible."""
        if observation.variable_id != self.variable_id:
            return QualityAssessment.valid(
                observation.observation_id
            )

        quantity = self._extract_quantity(observation)

        if quantity is None:
            return QualityAssessment(
                observation_id=observation.observation_id,
                quality=DataQuality.INVALID,
                score=0.0,
                diagnostics=(DiagnosticCode.IMPOSSIBLE_VALUE,),
                reasons=(
                    "The configured variable requires a numerical value.",
                ),
            )

        try:
            normalized = quantity.to(self.minimum.unit)
        except ValueError:
            return QualityAssessment(
                observation_id=observation.observation_id,
                quality=DataQuality.INVALID,
                score=0.0,
                diagnostics=(DiagnosticCode.IMPOSSIBLE_VALUE,),
                reasons=(
                    (
                        "The observation unit is incompatible with the "
                        "configured plausible range."
                    ),
                ),
            )

        if (
            self.minimum.value
            <= normalized.value
            <= self.maximum.value
        ):
            return QualityAssessment.valid(
                observation.observation_id
            )

        return QualityAssessment(
            observation_id=observation.observation_id,
            quality=DataQuality.INVALID,
            score=0.0,
            diagnostics=(DiagnosticCode.IMPOSSIBLE_VALUE,),
            reasons=(
                (
                    f"Observed value {normalized.value:.6g} "
                    f"{normalized.unit} is outside the plausible range "
                    f"[{self.minimum.value:.6g}, "
                    f"{self.maximum.value:.6g}] {self.minimum.unit}."
                ),
            ),
        )

    @staticmethod
    def _extract_quantity(
        observation: Observation,
    ) -> Measurement | None:
        """Extract a physical quantity from a supported observation."""
        value = observation.value

        if isinstance(value, bool):
            return None

        if isinstance(value, ScientificMeasurement):
            return value.quantity

        if isinstance(value, int | float):
            unit = observation.variable.display_unit

            if unit is None:
                unit = observation.variable.unit

            if unit is None:
                return Measurement(
                    value=float(value),
                    unit="dimensionless",
                )

            return Measurement(
                value=float(value),
                unit=unit,
            )

        return None
