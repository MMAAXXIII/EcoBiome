"""Experiments for investigating camera and lux contradictions."""

from dataclasses import dataclass
from datetime import timedelta

from ecobiome.reasoning.abduction import HypothesisProposal
from ecobiome.reasoning.experiment.experiment import (
    Experiment,
    ExperimentStep,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CameraLuxExperimentRule:
    """Plan experiments for competing camera/lux hypotheses."""

    identifier: str = "experiment.camera_lux_diagnosis"

    def plan(
        self,
        proposals: tuple[HypothesisProposal, ...],
    ) -> tuple[Experiment, ...]:
        """Generate relevant experiments from known proposal identifiers."""
        proposal_ids = {
            proposal.identifier
            for proposal in proposals
        }

        experiments: list[Experiment] = []

        camera_related = {
            "hardware.possible_camera_failure",
            "vision.possible_lens_obstruction",
        }

        if camera_related & proposal_ids:
            tested = tuple(
                identifier
                for identifier in (
                    "hardware.possible_camera_failure",
                    "vision.possible_lens_obstruction",
                )
                if identifier in proposal_ids
            )

            experiments.append(
                Experiment(
                    identifier="camera.clean_lens_and_recapture",
                    title="Clean the camera lens and capture a new frame",
                    objective=(
                        "Differentiate lens obstruction from a persistent "
                        "camera or exposure failure."
                    ),
                    steps=(
                        ExperimentStep(
                            instruction=(
                                "Record the current camera luminance."
                            ),
                            expected_result=(
                                "A baseline luminance value is preserved."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Inspect and clean the camera lens."
                            ),
                            expected_result=(
                                "Visible dirt, condensation, or obstruction "
                                "is removed."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Wait ten seconds for the image to stabilize."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Capture a new frame and recalculate "
                                "mean luminance."
                            ),
                            expected_result=(
                                "A strong luminance increase supports "
                                "lens obstruction."
                            ),
                        ),
                    ),
                    tested_hypothesis_ids=tested,
                    expected_observation_ids=(
                        "vision.frame_mean_luminance",
                    ),
                    required_devices=(
                        "camera.primary",
                        "human.operator",
                    ),
                    safety_notes=(
                        "Disconnect movable camera hardware before cleaning.",
                        "Use a non-abrasive optical cloth.",
                    ),
                    estimated_information_gain=0.46,
                    estimated_duration=timedelta(minutes=3),
                )
            )

        if (
            "hardware.possible_lux_sensor_failure"
            in proposal_ids
        ):
            experiments.append(
                Experiment(
                    identifier="lighting.compare_independent_lux_meter",
                    title="Compare the lux sensor with an independent meter",
                    objective=(
                        "Determine whether the installed ambient-light "
                        "sensor is reporting an incorrect value."
                    ),
                    steps=(
                        ExperimentStep(
                            instruction=(
                                "Place an independent lux meter beside "
                                "the installed sensor."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Record both lux values at the same moment."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Compare their absolute and relative "
                                "difference."
                            ),
                            expected_result=(
                                "A large discrepancy supports failure or "
                                "miscalibration of one sensor."
                            ),
                        ),
                    ),
                    tested_hypothesis_ids=(
                        "hardware.possible_lux_sensor_failure",
                    ),
                    expected_observation_ids=(
                        "weather.ambient_light",
                    ),
                    required_devices=(
                        "lux_meter.reference",
                        "human.operator",
                    ),
                    estimated_information_gain=0.34,
                    estimated_duration=timedelta(minutes=5),
                )
            )

        if (
            "timing.possible_observation_desynchronization"
            in proposal_ids
        ):
            experiments.append(
                Experiment(
                    identifier="timing.capture_synchronized_camera_lux",
                    title="Capture synchronized camera and lux readings",
                    objective=(
                        "Determine whether the contradiction was caused "
                        "by observations recorded at different moments."
                    ),
                    steps=(
                        ExperimentStep(
                            instruction=(
                                "Synchronize the camera and lux-sensor "
                                "clocks."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Trigger one camera capture and one lux "
                                "reading within the same second."
                            ),
                        ),
                        ExperimentStep(
                            instruction=(
                                "Run the camera/lux consistency rule on "
                                "the synchronized observations."
                            ),
                        ),
                    ),
                    tested_hypothesis_ids=(
                        "timing.possible_observation_desynchronization",
                    ),
                    expected_observation_ids=(
                        "vision.frame_mean_luminance",
                        "weather.ambient_light",
                    ),
                    required_devices=(
                        "camera.primary",
                        "lux_sensor.primary",
                    ),
                    estimated_information_gain=0.29,
                    estimated_duration=timedelta(minutes=2),
                )
            )

        return tuple(experiments)
