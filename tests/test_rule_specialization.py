"""Tests for specialized quality and evidence rule contracts."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    DataQuality,
    Observation,
    ObservationQualityEngine,
    QualityAssessment,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import Evidence, EvidenceRelation
from ecobiome.reasoning.rules import (
    RuleDomain,
    RuleEngine,
    ScientificRule,
)

HYPOTHESIS_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_observation() -> Observation:
    """Create one generic observation."""
    variable = ScientificVariable(
        identifier="physics.water_temperature",
        name="Water temperature",
        description="Temperature of the water.",
        unit="kelvin",
        display_unit="degC",
        category="physics",
    )

    return Observation(
        source="sensor-01",
        variable=variable,
        value=23.5,
        acquisition_method=AcquisitionMethod.SENSOR,
        observed_at=datetime(
            2026,
            8,
            1,
            12,
            0,
            tzinfo=UTC,
        ),
    )


class QualityOnlyRule(ScientificRule):
    """Rule implementing only the quality contract."""

    def assess(
        self,
        observation: Observation,
    ) -> QualityAssessment:
        return QualityAssessment.valid(
            observation.observation_id
        )


class EvidenceOnlyRule(ScientificRule):
    """Rule implementing only the evidence contract."""

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        return (
            Evidence(
                observation_id=observation.observation_id,
                hypothesis_id=HYPOTHESIS_ID,
                relation=EvidenceRelation.SUPPORTS,
                weight=0.50,
                explanation="Observation supports the hypothesis.",
                source_rule=self.identifier,
            ),
        )


def make_quality_rule() -> QualityOnlyRule:
    """Create one quality-only rule."""
    return QualityOnlyRule(
        identifier="hardware.quality_only",
        name="Quality-only rule",
        description="Assess quality without producing evidence.",
        domain=RuleDomain.HARDWARE,
    )


def make_evidence_rule() -> EvidenceOnlyRule:
    """Create one evidence-only rule."""
    return EvidenceOnlyRule(
        identifier="chemistry.evidence_only",
        name="Evidence-only rule",
        description="Produce evidence without assessing quality.",
        domain=RuleDomain.CHEMISTRY,
    )


def test_quality_engine_accepts_quality_only_rule() -> None:
    report = ObservationQualityEngine(
        [make_quality_rule()]
    ).evaluate(make_observation())

    assert report.assessment.quality is DataQuality.VALID
    assert report.failed_rule_count == 0


def test_rule_engine_accepts_evidence_only_rule() -> None:
    report = RuleEngine(
        [make_evidence_rule()]
    ).evaluate(make_observation())

    assert report.evidence_count == 1
    assert report.failed_rule_count == 0


def test_rule_engine_rejects_quality_only_rule() -> None:
    with pytest.raises(
        TypeError,
        match="must implement evaluate",
    ):
        RuleEngine([make_quality_rule()])  # type: ignore[list-item]


def test_quality_engine_rejects_evidence_only_rule() -> None:
    with pytest.raises(
        TypeError,
        match="must implement assess",
    ):
        ObservationQualityEngine(
            [make_evidence_rule()]  # type: ignore[list-item]
        )
