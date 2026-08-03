"""Tests for abductive camera/lux hypothesis generation."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.abduction import (
    CameraLuxHypothesisRule,
    HypothesisGenerationReport,
    HypothesisGenerator,
    HypothesisProposal,
)
from ecobiome.reasoning.consistency import (
    ConsistencyAssessment,
    ConsistencyStatus,
)

CAMERA_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)

LUX_ID = UUID(
    "22222222-2222-2222-2222-222222222222"
)

OBSERVED_AT = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)


def make_variable(
    identifier: str,
    *,
    name: str,
    unit: str,
    category: str,
) -> ScientificVariable:
    """Create one variable used by the test observations."""
    return ScientificVariable(
        identifier=identifier,
        name=name,
        description=name,
        unit=unit,
        display_unit=unit,
        category=category,
    )


def make_observations() -> tuple[Observation, ...]:
    """Create contradictory camera and lux observations."""
    camera = Observation(
        observation_id=CAMERA_ID,
        source="camera-01",
        variable=make_variable(
            "vision.frame_mean_luminance",
            name="Frame luminance",
            unit="dimensionless",
            category="vision",
        ),
        value=0.01,
        acquisition_method=AcquisitionMethod.CAMERA,
        observed_at=OBSERVED_AT,
    )

    lux = Observation(
        observation_id=LUX_ID,
        source="lux-sensor-01",
        variable=make_variable(
            "weather.ambient_light",
            name="Ambient light",
            unit="lux",
            category="weather",
        ),
        value=40_000.0,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=OBSERVED_AT,
    )

    return camera, lux


def make_assessment(
    status: ConsistencyStatus = ConsistencyStatus.INCONSISTENT,
) -> ConsistencyAssessment:
    """Create one camera/lux consistency assessment."""
    return ConsistencyAssessment(
        status=status,
        confidence=0.98,
        involved_observations=(CAMERA_ID, LUX_ID),
        reason="Camera is black while ambient light is high.",
    )


def test_contradiction_generates_ranked_hypotheses() -> None:
    report = HypothesisGenerator(
        [CameraLuxHypothesisRule()]
    ).generate(
        make_assessment(),
        make_observations(),
    )

    assert report.succeeded is True
    assert report.proposal_count == 4

    assert tuple(
        proposal.identifier
        for proposal in report.proposals
    ) == (
        "hardware.possible_camera_failure",
        "vision.possible_lens_obstruction",
        "hardware.possible_lux_sensor_failure",
        "timing.possible_observation_desynchronization",
    )

    assert tuple(
        proposal.confidence
        for proposal in report.proposals
    ) == pytest.approx((0.45, 0.30, 0.15, 0.10))


def test_consistent_assessment_generates_no_hypothesis() -> None:
    report = HypothesisGenerator(
        [CameraLuxHypothesisRule()]
    ).generate(
        make_assessment(ConsistencyStatus.CONSISTENT),
        make_observations(),
    )

    assert report.proposals == ()


def test_proposals_keep_traceable_observation_ids() -> None:
    report = HypothesisGenerator(
        [CameraLuxHypothesisRule()]
    ).generate(
        make_assessment(),
        make_observations(),
    )

    assert all(
        proposal.supporting_observation_ids
        == (CAMERA_ID, LUX_ID)
        for proposal in report.proposals
    )


def test_unrelated_inconsistency_is_ignored() -> None:
    assessment = ConsistencyAssessment(
        status=ConsistencyStatus.INCONSISTENT,
        confidence=0.90,
        involved_observations=(LUX_ID,),
        reason="Unrelated contradiction.",
    )

    report = HypothesisGenerator(
        [CameraLuxHypothesisRule()]
    ).generate(
        assessment,
        make_observations(),
    )

    assert report.proposals == ()


@dataclass(frozen=True)
class FailingRule:
    """Rule used to verify failure isolation."""

    identifier: str = "abduction.failing_rule"

    def generate(
        self,
        assessment: ConsistencyAssessment,
        observations: tuple[Observation, ...],
    ) -> tuple[HypothesisProposal, ...]:
        raise RuntimeError("Simulated generation failure.")


def test_rule_failure_is_isolated() -> None:
    report: HypothesisGenerationReport = HypothesisGenerator(
        [
            FailingRule(),
            CameraLuxHypothesisRule(),
        ]
    ).generate(
        make_assessment(),
        make_observations(),
    )

    assert report.failed_rule_count == 1
    assert report.proposal_count == 4
    assert report.succeeded is False
    assert report.failures[0].exception_type == "RuntimeError"


def test_duplicate_rule_identifier_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate hypothesis-generation rule",
    ):
        HypothesisGenerator(
            [
                CameraLuxHypothesisRule(),
                CameraLuxHypothesisRule(),
            ]
        )
