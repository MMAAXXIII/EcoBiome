"""Fail-closed bioindicator assessment aggregation for N10 V1."""
from __future__ import annotations

from dataclasses import dataclass

from .models import (
    BioindicatorAssessment,
    BioindicatorFactorAssessment,
    EcosystemObservation,
)


@dataclass(frozen=True, slots=True)
class BioindicatorAssessmentResultV1:
    assessment: BioindicatorAssessment
    factors: tuple[BioindicatorFactorAssessment, ...]
    concordant_factor_keys: tuple[str, ...]
    non_concordant_factor_keys: tuple[str, ...]
    missing_factor_keys: tuple[str, ...]
    unknown_factor_keys: tuple[str, ...]
    warning: str


def build_bioindicator_assessment_v1(
    *,
    assessment_id: str,
    observation: EcosystemObservation,
    factors: tuple[BioindicatorFactorAssessment, ...],
    evidence_strength: str,
    generated_at: str,
) -> BioindicatorAssessmentResultV1:
    """Aggregate explicit factor reviews without inferring causal mechanisms.

    Factor states must have been supplied by a reviewed comparison layer. This function
    only reports concordance/non-concordance/missingness and never upgrades correlation
    into causality.
    """
    if not factors:
        evaluability = "not_evaluated"
        completeness = "no_factor_data"
    else:
        for factor in factors:
            if factor.assessment_id != assessment_id:
                raise ValueError("Bioindicator factor belongs to another assessment")
        missing_count = sum(item.state == "missing" for item in factors)
        unknown_count = sum(item.state == "unknown" for item in factors)
        evaluated_count = len(factors) - missing_count - unknown_count
        if evaluated_count == 0:
            evaluability = "not_evaluated"
        elif missing_count or unknown_count:
            evaluability = "partially_evaluated"
        else:
            evaluability = "evaluated"
        completeness = f"{evaluated_count}/{len(factors)}_factors_evaluated"

    assessment = BioindicatorAssessment(
        id=assessment_id,
        ecosystem_id=observation.ecosystem_id,
        observation_id=observation.id,
        evaluability=evaluability,
        evidence_strength=evidence_strength,
        data_completeness=completeness,
        generated_at=generated_at,
    )
    return BioindicatorAssessmentResultV1(
        assessment=assessment,
        factors=factors,
        concordant_factor_keys=tuple(sorted(item.factor_key for item in factors if item.state == "concordant")),
        non_concordant_factor_keys=tuple(sorted(item.factor_key for item in factors if item.state == "non_concordant")),
        missing_factor_keys=tuple(sorted(item.factor_key for item in factors if item.state == "missing")),
        unknown_factor_keys=tuple(sorted(item.factor_key for item in factors if item.state == "unknown")),
        warning=BioindicatorAssessment.CORRELATION_WARNING,
    )
