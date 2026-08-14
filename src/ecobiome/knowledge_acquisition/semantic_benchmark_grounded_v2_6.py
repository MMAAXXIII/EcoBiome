"""V2.6 wrapper around the grounded V2.3.3 semantic benchmark evaluator."""

from __future__ import annotations

from typing import Any

from ecobiome.knowledge_acquisition.semantic_benchmark_grounded import (
    evaluate_structured_semantic_benchmark,
)
from ecobiome.knowledge_acquisition.semantic_epistemic import (
    EPISTEMIC_POLICY_V1_SHA256,
    REGISTRY_V2_6_SHA256,
    audit_coordinated_arguments,
    audit_epistemic_overclaims,
    validate_epistemic_policy,
    validate_registry_v2_6,
)


def evaluate_structured_semantic_benchmark_v2_6(
    candidate_payload: Any,
    fixture: Any,
    semantic_export: Any,
    *,
    label: str,
    registry_v2_6: Any,
    epistemic_policy: Any,
    candidate_contract: Any | None = None,
    argument_grounding_policy: Any | None = None,
) -> dict[str, Any]:
    registry = validate_registry_v2_6(registry_v2_6)
    policy = validate_epistemic_policy(epistemic_policy)

    report = evaluate_structured_semantic_benchmark(
        candidate_payload,
        fixture,
        semantic_export,
        label=label,
        candidate_contract=candidate_contract,
        argument_grounding_policy=argument_grounding_policy,
    )

    epistemic = audit_epistemic_overclaims(
        candidate_payload,
        fixture,
        registry,
        policy,
    )
    coordinated = audit_coordinated_arguments(
        candidate_payload,
        semantic_export,
        registry,
        policy,
    )

    blocking_reasons = list(report["benchmark_gate"]["blocking_reasons"])
    if epistemic["violation_count"]:
        blocking_reasons.append(
            f"epistemic_overclaims={epistemic['violation_count']}"
        )
    if coordinated["role_cardinality_conflict_count"]:
        blocking_reasons.append(
            "coordinated_role_cardinality_conflicts="
            f"{coordinated['role_cardinality_conflict_count']}"
        )

    report = dict(report)
    report["schema_version"] = "2.6-grounded-epistemic-v1"
    report["semantic_registry_v2_6"] = {
        "registry_sha256": REGISTRY_V2_6_SHA256,
        "epistemic_policy_sha256": EPISTEMIC_POLICY_V1_SHA256,
    }
    report["epistemic_enforcement"] = epistemic
    report["coordinated_span"] = coordinated
    report["benchmark_gate"] = {
        "pass": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
    }
    return report
