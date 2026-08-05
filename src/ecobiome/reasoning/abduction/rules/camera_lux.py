"""Abductive explanations for camera and lux contradictions."""

from dataclasses import dataclass

from ecobiome.core.observation import Observation
from ecobiome.reasoning.abduction.proposal import (
    HypothesisProposal,
)
from ecobiome.reasoning.consistency import (
    ConsistencyAssessment,
    ConsistencyStatus,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CameraLuxHypothesisRule:
    """Propose competing causes for a camera/lux contradiction."""

    identifier: str = "abduction.camera_lux_contradiction"

    def generate(
        self,
        assessment: ConsistencyAssessment,
        observations: tuple[Observation, ...],
    ) -> tuple[HypothesisProposal, ...]:
        """Generate explanations only for a confirmed inconsistency."""
        if assessment.status is not ConsistencyStatus.INCONSISTENT:
            return ()

        observations_by_id = {
            observation.observation_id: observation
            for observation in observations
        }

        involved = tuple(
            observations_by_id[observation_id]
            for observation_id in assessment.involved_observations
            if observation_id in observations_by_id
        )

        variable_ids = {
            observation.variable_id
            for observation in involved
        }

        required_variables = {
            "vision.frame_mean_luminance",
            "weather.ambient_light",
        }

        if not required_variables.issubset(variable_ids):
            return ()

        observation_ids = tuple(
            observation.observation_id
            for observation in involved
        )

        rationale = assessment.reason or (
            "Camera luminance contradicts ambient-light data."
        )

        return (
            HypothesisProposal(
                identifier="hardware.possible_camera_failure",
                title="Possible camera failure",
                statement=(
                    "The camera may be unable to produce "
                    "a valid exposed image."
                ),
                confidence=0.45,
                source_rule=self.identifier,
                supporting_observation_ids=observation_ids,
                rationale=rationale,
            ),
            HypothesisProposal(
                identifier="vision.possible_lens_obstruction",
                title="Possible lens obstruction",
                statement=(
                    "The camera lens may be covered, dirty, "
                    "condensed, or physically obstructed."
                ),
                confidence=0.30,
                source_rule=self.identifier,
                supporting_observation_ids=observation_ids,
                rationale=rationale,
            ),
            HypothesisProposal(
                identifier="hardware.possible_lux_sensor_failure",
                title="Possible ambient-light sensor failure",
                statement=(
                    "The independent lux sensor may be reporting "
                    "an incorrect high-light value."
                ),
                confidence=0.15,
                source_rule=self.identifier,
                supporting_observation_ids=observation_ids,
                rationale=rationale,
            ),
            HypothesisProposal(
                identifier="timing.possible_observation_desynchronization",
                title="Possible observation desynchronization",
                statement=(
                    "The camera and lux observations may not "
                    "represent the same physical moment."
                ),
                confidence=0.10,
                source_rule=self.identifier,
                supporting_observation_ids=observation_ids,
                rationale=rationale,
            ),
        )
