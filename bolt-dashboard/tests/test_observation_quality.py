"""Tests for observation quality assessments."""

from datetime import datetime
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    DataQuality,
    DiagnosticCode,
    QualityAssessment,
)

OBSERVATION_ID = UUID(
    "12345678-1234-5678-1234-567812345678"
)


def test_valid_assessment_is_usable() -> None:
    assessment = QualityAssessment.valid(
        OBSERVATION_ID,
        score=0.98,
    )

    assert assessment.quality is DataQuality.VALID
    assert assessment.score == pytest.approx(0.98)
    assert assessment.diagnostics == ()
    assert assessment.is_usable_for_reasoning is True
    assert assessment.requires_attention is False


def test_suspect_assessment_remains_usable_with_reduced_score() -> None:
    assessment = QualityAssessment(
        observation_id=OBSERVATION_ID,
        quality=DataQuality.SUSPECT,
        score=0.35,
        diagnostics=(
            DiagnosticCode.SOURCE_CONTRADICTION,
        ),
        reasons=(
            "The value conflicts with an independent sensor.",
        ),
    )

    assert assessment.is_usable_for_reasoning is True
    assert assessment.requires_attention is True
    assert assessment.score == pytest.approx(0.35)


def test_stale_assessment_is_not_usable() -> None:
    assessment = QualityAssessment(
        observation_id=OBSERVATION_ID,
        quality=DataQuality.STALE,
        score=0.20,
        diagnostics=(
            DiagnosticCode.STALE_OBSERVATION,
        ),
        reasons=("Observation exceeds its maximum age.",),
    )

    assert assessment.is_usable_for_reasoning is False
    assert assessment.requires_attention is True


def test_rejected_invalid_assessment_has_zero_score() -> None:
    assessment = QualityAssessment.rejected(
        OBSERVATION_ID,
        quality=DataQuality.INVALID,
        diagnostic=DiagnosticCode.IMPOSSIBLE_VALUE,
        reason="A negative concentration is physically impossible.",
    )

    assert assessment.score == pytest.approx(0.0)
    assert assessment.is_usable_for_reasoning is False
    assert assessment.diagnostics == (
        DiagnosticCode.IMPOSSIBLE_VALUE,
    )


def test_rejected_factory_refuses_suspect_quality() -> None:
    with pytest.raises(
        ValueError,
        match="INVALID or MISSING",
    ):
        QualityAssessment.rejected(
            OBSERVATION_ID,
            quality=DataQuality.SUSPECT,
            diagnostic=DiagnosticCode.SOURCE_CONTRADICTION,
            reason="Conflicting sources.",
        )


def test_non_valid_assessment_requires_diagnostic() -> None:
    with pytest.raises(
        ValueError,
        match="requires a diagnostic",
    ):
        QualityAssessment(
            observation_id=OBSERVATION_ID,
            quality=DataQuality.SUSPECT,
            score=0.50,
        )


def test_valid_assessment_refuses_diagnostics() -> None:
    with pytest.raises(
        ValueError,
        match="cannot contain diagnostics",
    ):
        QualityAssessment(
            observation_id=OBSERVATION_ID,
            quality=DataQuality.VALID,
            score=1.0,
            diagnostics=(
                DiagnosticCode.UNKNOWN,
            ),
        )


def test_invalid_assessment_requires_zero_score() -> None:
    with pytest.raises(
        ValueError,
        match="must have a zero score",
    ):
        QualityAssessment(
            observation_id=OBSERVATION_ID,
            quality=DataQuality.INVALID,
            score=0.10,
            diagnostics=(
                DiagnosticCode.SENSOR_FAILURE,
            ),
        )


def test_diagnostics_and_reasons_are_deduplicated() -> None:
    assessment = QualityAssessment(
        observation_id=OBSERVATION_ID,
        quality=DataQuality.SUSPECT,
        score=0.40,
        diagnostics=(
            DiagnosticCode.FROZEN_SENSOR,
            DiagnosticCode.FROZEN_SENSOR,
        ),
        reasons=(
            "  Repeated constant value.  ",
            "Repeated constant value.",
            "   ",
        ),
    )

    assert assessment.diagnostics == (
        DiagnosticCode.FROZEN_SENSOR,
    )
    assert assessment.reasons == (
        "Repeated constant value.",
    )


def test_score_must_be_between_zero_and_one() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        QualityAssessment.valid(
            OBSERVATION_ID,
            score=1.20,
        )


def test_boolean_score_is_rejected() -> None:
    with pytest.raises(TypeError, match="must be numeric"):
        QualityAssessment.valid(
            OBSERVATION_ID,
            score=True,
        )


def test_naive_timestamp_is_rejected() -> None:
    naive_datetime = datetime(2026, 8, 1, 12, 0)  # noqa: DTZ001

    with pytest.raises(ValueError, match="include a timezone"):
        QualityAssessment.valid(
            OBSERVATION_ID,
            assessed_at=naive_datetime,
        )
