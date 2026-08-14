"""Vision rule detecting consecutive nearly black camera frames."""

from dataclasses import dataclass

from ecobiome.core.observation import (
    DataQuality,
    DiagnosticCode,
    Observation,
    ObservationStore,
    QualityAssessment,
    ScientificMeasurement,
)
from ecobiome.reasoning.rules.rule import ScientificRule


@dataclass(frozen=True, slots=True, kw_only=True)
class BlackFrameRule(ScientificRule):
    """Detect a camera producing consecutive nearly black frames."""

    observation_store: ObservationStore
    variable_id: str = "vision.frame_mean_luminance"
    maximum_luminance: float = 0.02
    minimum_frame_count: int = 3
    suspect_score: float = 0.20

    def __post_init__(self) -> None:
        """Validate metadata and detection parameters."""
        super().__post_init__()

        variable_id = self.variable_id.strip()

        if not variable_id:
            raise ValueError("variable_id cannot be empty.")

        if "." not in variable_id:
            raise ValueError(
                "variable_id must contain a domain prefix."
            )

        if not 0.0 <= self.maximum_luminance <= 1.0:
            raise ValueError(
                "maximum_luminance must be between 0 and 1."
            )

        if self.minimum_frame_count < 1:
            raise ValueError(
                "minimum_frame_count must be at least one."
            )

        if not 0.0 <= self.suspect_score <= 1.0:
            raise ValueError(
                "suspect_score must be between 0 and 1."
            )

        object.__setattr__(self, "variable_id", variable_id)

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        """Assess whether recent frames from one camera are nearly black."""
        if observation.variable_id != self.variable_id:
            return QualityAssessment.valid(
                observation.observation_id
            )

        current_luminance = self._extract_luminance(observation)

        if current_luminance is None:
            return QualityAssessment(
                observation_id=observation.observation_id,
                quality=DataQuality.INVALID,
                score=0.0,
                diagnostics=(DiagnosticCode.IMPOSSIBLE_VALUE,),
                reasons=(
                    (
                        "Camera luminance must be a numerical value "
                        "between 0 and 1."
                    ),
                ),
            )

        history = self._matching_history(observation)
        sequence = (*history, observation)

        if len(sequence) < self.minimum_frame_count:
            return QualityAssessment.valid(
                observation.observation_id
            )

        selected = sequence[-self.minimum_frame_count :]
        luminances: list[float] = []

        for item in selected:
            luminance = self._extract_luminance(item)

            if luminance is None:
                return QualityAssessment(
                    observation_id=observation.observation_id,
                    quality=DataQuality.INVALID,
                    score=0.0,
                    diagnostics=(DiagnosticCode.IMPOSSIBLE_VALUE,),
                    reasons=(
                        (
                            "A frame in the evaluated camera sequence "
                            "contains an invalid luminance value."
                        ),
                    ),
                )

            luminances.append(luminance)

        if any(
            luminance > self.maximum_luminance
            for luminance in luminances
        ):
            return QualityAssessment.valid(
                observation.observation_id
            )

        maximum_observed = max(luminances)

        return QualityAssessment(
            observation_id=observation.observation_id,
            quality=DataQuality.SUSPECT,
            score=self.suspect_score,
            diagnostics=(DiagnosticCode.CAMERA_BLACK_FRAME,),
            reasons=(
                (
                    f"Camera source {observation.source!r} produced "
                    f"{len(selected)} consecutive frames with mean "
                    f"luminance at or below "
                    f"{self.maximum_luminance:.4f}. "
                    f"The highest observed luminance was "
                    f"{maximum_observed:.4f}. This may indicate "
                    "darkness, obstruction, exposure failure, "
                    "signal loss, or camera malfunction."
                ),
            ),
        )

    def _matching_history(
        self,
        observation: Observation,
    ) -> tuple[Observation, ...]:
        """Return earlier luminance observations from the same camera."""
        matching = (
            item
            for item in self.observation_store.load()
            if item.observation_id != observation.observation_id
            and item.source == observation.source
            and item.variable_id == self.variable_id
            and item.observed_at <= observation.observed_at
        )

        return tuple(
            sorted(
                matching,
                key=lambda item: (
                    item.observed_at,
                    str(item.observation_id),
                ),
            )
        )

    @staticmethod
    def _extract_luminance(
        observation: Observation,
    ) -> float | None:
        """Extract and validate a normalized mean-luminance value."""
        value = observation.value

        if isinstance(value, bool):
            return None

        if isinstance(value, int | float):
            luminance = float(value)
        elif isinstance(value, ScientificMeasurement):
            quantity = value.quantity

            try:
                normalized = quantity.to("dimensionless")
            except ValueError:
                return None

            luminance = normalized.value
        else:
            return None

        if not 0.0 <= luminance <= 1.0:
            return None

        return luminance
