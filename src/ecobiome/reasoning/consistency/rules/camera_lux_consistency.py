"""Consistency rule comparing camera luminance with ambient lux."""

from dataclasses import dataclass

from ecobiome.core.observation import (
    Observation,
    ScientificMeasurement,
)
from ecobiome.reasoning.consistency import (
    ConsistencyAssessment,
    ConsistencyStatus,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CameraLuxConsistencyRule:
    """Compare camera darkness with independent ambient-light data."""

    identifier: str = "consistency.camera_lux"
    camera_variable_id: str = "vision.frame_mean_luminance"
    lux_variable_id: str = "weather.ambient_light"
    maximum_black_luminance: float = 0.02
    maximum_dark_lux: float = 2.0
    minimum_daylight_lux: float = 20_000.0
    consistent_confidence: float = 0.95
    inconsistent_confidence: float = 0.98

    def __post_init__(self) -> None:
        """Validate the consistency-rule configuration."""
        identifier = self.identifier.strip()
        camera_variable_id = self.camera_variable_id.strip()
        lux_variable_id = self.lux_variable_id.strip()

        if not identifier:
            raise ValueError("identifier cannot be empty.")

        if not camera_variable_id:
            raise ValueError("camera_variable_id cannot be empty.")

        if not lux_variable_id:
            raise ValueError("lux_variable_id cannot be empty.")

        if not 0.0 <= self.maximum_black_luminance <= 1.0:
            raise ValueError(
                "maximum_black_luminance must be between 0 and 1."
            )

        if self.maximum_dark_lux < 0:
            raise ValueError(
                "maximum_dark_lux cannot be negative."
            )

        if self.minimum_daylight_lux <= self.maximum_dark_lux:
            raise ValueError(
                "minimum_daylight_lux must be greater than "
                "maximum_dark_lux."
            )

        for name, value in (
            ("consistent_confidence", self.consistent_confidence),
            ("inconsistent_confidence", self.inconsistent_confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1."
                )

        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(
            self,
            "camera_variable_id",
            camera_variable_id,
        )
        object.__setattr__(
            self,
            "lux_variable_id",
            lux_variable_id,
        )

    def evaluate(
        self,
        observations: tuple[Observation, ...],
    ) -> ConsistencyAssessment:
        """Compare the most recent relevant camera and lux observations."""
        camera_observation = self._latest_observation(
            observations,
            self.camera_variable_id,
        )
        lux_observation = self._latest_observation(
            observations,
            self.lux_variable_id,
        )

        involved_ids = tuple(
            observation.observation_id
            for observation in (
                camera_observation,
                lux_observation,
            )
            if observation is not None
        )

        if camera_observation is None or lux_observation is None:
            return ConsistencyAssessment(
                status=ConsistencyStatus.INSUFFICIENT_DATA,
                confidence=0.0,
                involved_observations=involved_ids,
                reason=(
                    "Camera luminance and ambient-light observations "
                    "are both required."
                ),
            )

        camera_luminance = self._extract_dimensionless(
            camera_observation
        )
        ambient_lux = self._extract_lux(lux_observation)

        if camera_luminance is None or ambient_lux is None:
            return ConsistencyAssessment(
                status=ConsistencyStatus.UNKNOWN,
                confidence=0.0,
                involved_observations=involved_ids,
                reason=(
                    "One or more observations contain an unsupported "
                    "or incompatible value."
                ),
            )

        camera_is_black = (
            camera_luminance <= self.maximum_black_luminance
        )

        if (
            camera_is_black
            and ambient_lux >= self.minimum_daylight_lux
        ):
            return ConsistencyAssessment(
                status=ConsistencyStatus.INCONSISTENT,
                confidence=self.inconsistent_confidence,
                involved_observations=involved_ids,
                reason=(
                    f"Camera mean luminance is {camera_luminance:.4f}, "
                    f"indicating an almost black image, while the "
                    f"independent light sensor reports "
                    f"{ambient_lux:.1f} lux. The camera may be "
                    "obstructed, misconfigured, disconnected, or faulty."
                ),
            )

        if (
            camera_is_black
            and ambient_lux <= self.maximum_dark_lux
        ):
            return ConsistencyAssessment(
                status=ConsistencyStatus.CONSISTENT,
                confidence=self.consistent_confidence,
                involved_observations=involved_ids,
                reason=(
                    f"Camera mean luminance is {camera_luminance:.4f} "
                    f"and ambient light is {ambient_lux:.1f} lux. "
                    "Both observations indicate a dark environment."
                ),
            )

        if (
            not camera_is_black
            and ambient_lux >= self.minimum_daylight_lux
        ):
            return ConsistencyAssessment(
                status=ConsistencyStatus.CONSISTENT,
                confidence=self.consistent_confidence,
                involved_observations=involved_ids,
                reason=(
                    f"Camera mean luminance is {camera_luminance:.4f} "
                    f"and ambient light is {ambient_lux:.1f} lux. "
                    "Both observations indicate a lit environment."
                ),
            )

        return ConsistencyAssessment(
            status=ConsistencyStatus.UNKNOWN,
            confidence=0.25,
            involved_observations=involved_ids,
            reason=(
                f"Camera mean luminance is {camera_luminance:.4f} "
                f"and ambient light is {ambient_lux:.1f} lux. "
                "The configured thresholds do not support a strong "
                "consistency conclusion."
            ),
        )

    @staticmethod
    def _latest_observation(
        observations: tuple[Observation, ...],
        variable_id: str,
    ) -> Observation | None:
        """Return the most recent observation for one variable."""
        matching = (
            observation
            for observation in observations
            if observation.variable_id == variable_id
        )

        return max(
            matching,
            key=lambda observation: (
                observation.observed_at,
                str(observation.observation_id),
            ),
            default=None,
        )

    @staticmethod
    def _extract_dimensionless(
        observation: Observation,
    ) -> float | None:
        """Extract a normalized dimensionless numeric value."""
        value = observation.value

        if isinstance(value, bool):
            return None

        if isinstance(value, int | float):
            normalized = float(value)
        elif isinstance(value, ScientificMeasurement):
            try:
                quantity = value.quantity.to("dimensionless")
            except ValueError:
                return None

            normalized = quantity.value
        else:
            return None

        if not 0.0 <= normalized <= 1.0:
            return None

        return normalized

    @staticmethod
    def _extract_lux(
        observation: Observation,
    ) -> float | None:
        """Extract an ambient-light value in lux."""
        value = observation.value

        if isinstance(value, bool):
            return None

        if isinstance(value, int | float):
            lux = float(value)
        elif isinstance(value, ScientificMeasurement):
            try:
                quantity = value.quantity.to("lux")
            except ValueError:
                return None

            lux = quantity.value
        else:
            return None

        if lux < 0:
            return None

        return lux
