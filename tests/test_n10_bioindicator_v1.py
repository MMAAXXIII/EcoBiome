from __future__ import annotations

from ecobiome.knowledge_graph_v1 import (
    BioindicatorAssessment,
    BioindicatorFactorAssessment,
    EcosystemObservable,
    EcosystemObservation,
    KnowledgeObject,
    build_bioindicator_assessment_v1,
)

NOW = "2026-08-16T15:00:00+00:00"


def test_mulm_is_nonliving_observable_and_missing_data_stays_explicit() -> None:
    mulm_object = KnowledgeObject("mulm", "ecosystem_observable", "Mulm", "mulm", NOW)
    mulm = EcosystemObservable(
        knowledge_object_id=mulm_object.id,
        observable_category="detrital_deposit",
        default_quantification_mode="ordinal_abundance",
    )
    observation = EcosystemObservation(
        id="obs-mulm-1",
        ecosystem_id="pond-1",
        observable_object_id=mulm.knowledge_object_id,
        observed_at=NOW,
        quantification_mode="ordinal_abundance",
        ordinal_value="moderate",
        location_id="bottom-zone",
        trend="stable",
        notes="visual observation; no causal interpretation",
    )
    factors = (
        BioindicatorFactorAssessment(
            id="factor-om",
            assessment_id="assessment-1",
            factor_key="organic_matter",
            state="concordant",
            observed_value="moderate",
            relation_id="reviewed-relation-om",
            rationale="explicit comparison against a reviewed relation",
        ),
        BioindicatorFactorAssessment(
            id="factor-o2",
            assessment_id="assessment-1",
            factor_key="dissolved_oxygen",
            state="missing",
            observed_value=None,
            relation_id=None,
            rationale="no dissolved-oxygen measurement available",
        ),
    )
    result = build_bioindicator_assessment_v1(
        assessment_id="assessment-1",
        observation=observation,
        factors=factors,
        evidence_strength="limited",
        generated_at=NOW,
    )
    assert result.assessment.evaluability == "partially_evaluated"
    assert result.missing_factor_keys == ("dissolved_oxygen",)
    assert result.concordant_factor_keys == ("organic_matter",)
    assert result.warning == BioindicatorAssessment.CORRELATION_WARNING
    assert "causality" in result.warning


def test_no_factor_data_returns_not_evaluated_not_false_reassurance() -> None:
    observation = EcosystemObservation(
        id="obs-algae-coverage",
        ecosystem_id="pond-1",
        observable_object_id="algae-morphotype",
        observed_at=NOW,
        quantification_mode="coverage_percent",
        numeric_value="18",
        unit_key="percent",
        trend="increasing",
    )
    result = build_bioindicator_assessment_v1(
        assessment_id="assessment-empty",
        observation=observation,
        factors=(),
        evidence_strength="unknown",
        generated_at=NOW,
    )
    assert result.assessment.evaluability == "not_evaluated"
    assert result.assessment.data_completeness == "no_factor_data"
