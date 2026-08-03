"""Tests for scientific experiment modelling and planning."""

from dataclasses import dataclass
from datetime import timedelta

import pytest

from ecobiome.reasoning.abduction import HypothesisProposal
from ecobiome.reasoning.experiment import (
    CameraLuxExperimentRule,
    Experiment,
    ExperimentPlanner,
    ExperimentPlanningReport,
    ExperimentStep,
)


def make_proposal(
    identifier: str,
    *,
    confidence: float,
) -> HypothesisProposal:
    """Create one diagnostic hypothesis proposal."""
    return HypothesisProposal(
        identifier=identifier,
        title=identifier,
        statement=f"Possible cause: {identifier}.",
        confidence=confidence,
        source_rule="abduction.camera_lux_contradiction",
    )


def make_camera_lux_proposals() -> tuple[HypothesisProposal, ...]:
    """Create the four camera/lux diagnostic proposals."""
    return (
        make_proposal(
            "hardware.possible_camera_failure",
            confidence=0.45,
        ),
        make_proposal(
            "vision.possible_lens_obstruction",
            confidence=0.30,
        ),
        make_proposal(
            "hardware.possible_lux_sensor_failure",
            confidence=0.15,
        ),
        make_proposal(
            "timing.possible_observation_desynchronization",
            confidence=0.10,
        ),
    )


def test_experiment_metadata_and_steps_are_normalized() -> None:
    experiment = Experiment(
        identifier="  test.simple_experiment  ",
        title="  Simple experiment  ",
        objective="  Reduce uncertainty.  ",
        steps=(
            ExperimentStep(
                instruction="  Perform measurement.  "
            ),
        ),
        tested_hypothesis_ids=(
            " test.first ",
            "test.first",
        ),
        required_devices=(
            " human.operator ",
            "human.operator",
        ),
        estimated_information_gain=0.50,
        estimated_duration=timedelta(minutes=1),
    )

    assert experiment.identifier == "test.simple_experiment"
    assert experiment.title == "Simple experiment"
    assert experiment.objective == "Reduce uncertainty."
    assert experiment.steps[0].instruction == "Perform measurement."
    assert experiment.tested_hypothesis_ids == ("test.first",)
    assert experiment.required_devices == ("human.operator",)
    assert experiment.step_count == 1
    assert experiment.requires_human_intervention is True


def test_camera_lux_rule_generates_three_experiments() -> None:
    report = ExperimentPlanner(
        [CameraLuxExperimentRule()]
    ).plan(make_camera_lux_proposals())

    assert report.succeeded is True
    assert report.experiment_count == 3

    assert tuple(
        experiment.identifier
        for experiment in report.experiments
    ) == (
        "camera.clean_lens_and_recapture",
        "lighting.compare_independent_lux_meter",
        "timing.capture_synchronized_camera_lux",
    )


def test_experiments_are_ranked_by_information_gain() -> None:
    report = ExperimentPlanner(
        [CameraLuxExperimentRule()]
    ).plan(make_camera_lux_proposals())

    assert tuple(
        experiment.estimated_information_gain
        for experiment in report.experiments
    ) == pytest.approx((0.46, 0.34, 0.29))

    assert report.best_experiment is not None
    assert report.best_experiment.identifier == (
        "camera.clean_lens_and_recapture"
    )


def test_camera_experiment_tests_two_competing_hypotheses() -> None:
    report = ExperimentPlanner(
        [CameraLuxExperimentRule()]
    ).plan(make_camera_lux_proposals())

    experiment = report.experiments[0]

    assert experiment.tested_hypothesis_ids == (
        "hardware.possible_camera_failure",
        "vision.possible_lens_obstruction",
    )
    assert experiment.expected_observation_ids == (
        "vision.frame_mean_luminance",
    )
    assert experiment.step_count == 4


def test_unrelated_proposal_generates_no_experiment() -> None:
    report = ExperimentPlanner(
        [CameraLuxExperimentRule()]
    ).plan(
        (
            make_proposal(
                "chemistry.possible_nitrite_spike",
                confidence=0.80,
            ),
        )
    )

    assert report.experiments == ()
    assert report.best_experiment is None


@dataclass(frozen=True)
class FailingPlanningRule:
    """Planning rule used to test failure isolation."""

    identifier: str = "experiment.failing_rule"

    def plan(
        self,
        proposals: tuple[HypothesisProposal, ...],
    ) -> tuple[Experiment, ...]:
        raise RuntimeError("Simulated planning failure.")


def test_failed_rule_does_not_stop_other_planners() -> None:
    report: ExperimentPlanningReport = ExperimentPlanner(
        [
            FailingPlanningRule(),
            CameraLuxExperimentRule(),
        ]
    ).plan(make_camera_lux_proposals())

    assert report.failed_rule_count == 1
    assert report.experiment_count == 3
    assert report.succeeded is False
    assert report.failures[0].exception_type == "RuntimeError"


def test_duplicate_planning_rule_identifier_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate experiment-planning rule",
    ):
        ExperimentPlanner(
            [
                CameraLuxExperimentRule(),
                CameraLuxExperimentRule(),
            ]
        )


def test_invalid_experiment_configuration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="at least one step",
    ):
        Experiment(
            identifier="test.no_steps",
            title="No steps",
            objective="Invalid experiment.",
            steps=(),
            tested_hypothesis_ids=("test.hypothesis",),
        )

    with pytest.raises(
        ValueError,
        match="information_gain must be between",
    ):
        Experiment(
            identifier="test.invalid_gain",
            title="Invalid gain",
            objective="Invalid experiment.",
            steps=(
                ExperimentStep(instruction="Perform test."),
            ),
            tested_hypothesis_ids=("test.hypothesis",),
            estimated_information_gain=1.20,
        )

    with pytest.raises(
        ValueError,
        match="duration cannot be negative",
    ):
        Experiment(
            identifier="test.invalid_duration",
            title="Invalid duration",
            objective="Invalid experiment.",
            steps=(
                ExperimentStep(instruction="Perform test."),
            ),
            tested_hypothesis_ids=("test.hypothesis",),
            estimated_duration=timedelta(seconds=-1),
        )
