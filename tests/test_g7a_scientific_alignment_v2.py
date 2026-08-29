from __future__ import annotations

from dataclasses import dataclass

import pytest

import ecobiome.simulation.scientific_alignment_v2 as alignment_v2
from ecobiome.simulation.model_semantic_bridge_v1 import (
    G7A_NITROGEN_OXIDATION_BRIDGE_V1,
)
from ecobiome.simulation.process_v1 import (
    ProcessScientificEvaluationScopeV1,
    ProcessScientificParameterBindingV1,
    ProcessScientificSupportV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    ProcessScientificAlignmentPolicyV1,
    ProcessScientificParticipantRequirementV1,
)
from ecobiome.simulation.scientific_alignment_v2 import (
    ALIGNMENT_V2_CONTRACT_SHA256,
    ProcessScientificAlignmentPolicyV2,
    ScientificProcessAlignmentV2Error,
    align_scientific_assertion_to_process_v2,
)


def _oxidation_base_policy() -> ProcessScientificAlignmentPolicyV1:
    return ProcessScientificAlignmentPolicyV1(
        name="g7a-oxidation-base-v1",
        version="1",
        process_id="nitrogen_transformation_extent_v1",
        process_version="1",
        role="mechanism",
        allowed_predicates=("nitrogen_oxidized_from_to",),
        alignment_class="direct_mechanism_support",
        epistemic_class="explicit_causal_result",
        evaluation_scope=ProcessScientificEvaluationScopeV1(
            process_id="nitrogen_transformation_extent_v1",
            process_version="1",
            role="mechanism",
            required_parameter_bindings=(
                ProcessScientificParameterBindingV1(
                    json_pointer="/source_component_id",
                    expected_value_json='"reduced_inorganic_nitrogen"',
                ),
                ProcessScientificParameterBindingV1(
                    json_pointer="/target_component_id",
                    expected_value_json='"oxidized_inorganic_nitrogen"',
                ),
            ),
        ),
        required_participants=(
            ProcessScientificParticipantRequirementV1(
                role="source_material",
                entity_id="entity-pubchem-cid-223",
                entity_revision=1,
            ),
            ProcessScientificParticipantRequirementV1(
                role="target_material",
                entity_id="entity-pubchem-cid-943",
                entity_revision=1,
            ),
            ProcessScientificParticipantRequirementV1(
                role="process_agent",
                entity_id="entity-ncbitaxon-1715989",
                entity_revision=1,
            ),
        ),
        required_qualifiers_json='{"semantic_type":"nitrogen_oxidation"}',
        participant_match_mode="exact",
        qualifier_match_mode="exact",
    )


def _oxidation_policy_v2() -> ProcessScientificAlignmentPolicyV2:
    return ProcessScientificAlignmentPolicyV2(
        name="g7a-nitrogen-oxidation-alignment-v2-test-only",
        version="2",
        assertion_ref=G7A_NITROGEN_OXIDATION_BRIDGE_V1.assertion_ref,
        base_policy_v1=_oxidation_base_policy(),
        model_semantic_bridge=G7A_NITROGEN_OXIDATION_BRIDGE_V1,
    )


def test_alignment_v2_contract_and_policy_bind_exact_bridge() -> None:
    policy = _oxidation_policy_v2()

    assert ALIGNMENT_V2_CONTRACT_SHA256 == (
        "a17302146a8656ec11363f929ebf2a8e9c23ead9da39779cd399ac1ec57b3fe3"
    )
    assert policy.bridge_sha256 == (
        "82f4ae564dacf41b57172febd09aa1bc7db9ad6cfaa0bb7899bb1b7a5d359b6c"
    )
    assert policy.evaluation_scope_sha256 == (
        policy.base_policy_v1.evaluation_scope.canonical_sha256
    )
    payload = policy.canonical_payload()
    assert payload["reviewed_model_semantic_bridge"]["bridge_sha256"] == (
        policy.bridge_sha256
    )
    assert payload["assertion_ref"] == policy.assertion_ref.canonical_payload()
    assert payload["automatic_acceptance"] is False
    assert payload["automatic_attachment"] is False


def test_alignment_v2_rejects_assertion_ref_mismatch() -> None:
    bridge = G7A_NITROGEN_OXIDATION_BRIDGE_V1
    wrong_ref = type(bridge.assertion_ref)(
        assertion_id="assertion-other",
        assertion_revision=1,
        canonical_payload_sha256=("0" * 64),
    )

    with pytest.raises(
        ScientificProcessAlignmentV2Error,
        match="assertion_ref must exactly match",
    ):
        ProcessScientificAlignmentPolicyV2(
            name="invalid",
            version="2",
            assertion_ref=wrong_ref,
            base_policy_v1=_oxidation_base_policy(),
            model_semantic_bridge=bridge,
        )


def test_alignment_v2_rejects_scope_not_equal_to_bridge() -> None:
    base = _oxidation_base_policy()
    wrong_scope = ProcessScientificEvaluationScopeV1(
        process_id="nitrogen_transformation_extent_v1",
        process_version="1",
        role="mechanism",
        required_parameter_bindings=(
            ProcessScientificParameterBindingV1(
                json_pointer="/source_component_id",
                expected_value_json='"dissolved_inorganic_nitrogen"',
            ),
            ProcessScientificParameterBindingV1(
                json_pointer="/target_component_id",
                expected_value_json='"oxidized_inorganic_nitrogen"',
            ),
        ),
    )
    wrong_base = ProcessScientificAlignmentPolicyV1(
        name=base.name,
        version=base.version,
        process_id=base.process_id,
        process_version=base.process_version,
        role=base.role,
        allowed_predicates=base.allowed_predicates,
        alignment_class=base.alignment_class,
        epistemic_class=base.epistemic_class,
        evaluation_scope=wrong_scope,
        required_participants=base.required_participants,
        required_qualifiers_json=base.required_qualifiers_json,
        participant_match_mode=base.participant_match_mode,
        qualifier_match_mode=base.qualifier_match_mode,
    )
    with pytest.raises(
        ScientificProcessAlignmentV2Error,
        match="source component scope must match bridge",
    ):
        ProcessScientificAlignmentPolicyV2(
            name="invalid-scope",
            version="2",
            assertion_ref=G7A_NITROGEN_OXIDATION_BRIDGE_V1.assertion_ref,
            base_policy_v1=wrong_base,
            model_semantic_bridge=G7A_NITROGEN_OXIDATION_BRIDGE_V1,
        )


@dataclass
class _FakeDefinition:
    process_id: str = "nitrogen_transformation_extent_v1"
    version: str = "1"


@dataclass
class _FakeEvaluation:
    definition: _FakeDefinition
    parameters_payload: dict[str, object]


def test_alignment_v2_support_sha_transitively_binds_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _oxidation_policy_v2()
    base_support = ProcessScientificSupportV1(
        role="mechanism",
        assertion_ref=policy.assertion_ref,
        alignment_class="direct_mechanism_support",
        epistemic_class="explicit_causal_result",
        alignment_policy_name=policy.base_policy_v1.name,
        alignment_policy_version=policy.base_policy_v1.version,
        alignment_policy_sha256=policy.base_policy_v1.canonical_sha256,
        evaluation_scope=policy.base_policy_v1.evaluation_scope,
        evaluation_scope_sha256=(
            policy.base_policy_v1.evaluation_scope.canonical_sha256
        ),
    )

    def _fake_v1(**_kwargs: object) -> ProcessScientificSupportV1:
        return base_support

    monkeypatch.setattr(
        alignment_v2,
        "align_scientific_assertion_to_process_v1",
        _fake_v1,
    )

    evaluation = _FakeEvaluation(
        definition=_FakeDefinition(),
        parameters_payload={
            "source_component_id": "reduced_inorganic_nitrogen",
            "target_component_id": "oxidized_inorganic_nitrogen",
        },
    )
    support = align_scientific_assertion_to_process_v2(
        evaluation=evaluation,  # type: ignore[arg-type]
        assertion_ref=policy.assertion_ref,
        policy=policy,
        assertions=object(),  # type: ignore[arg-type]
        syntheses=object(),  # type: ignore[arg-type]
    )

    assert support.alignment_policy_name == policy.name
    assert support.alignment_policy_version == policy.version
    assert support.alignment_policy_sha256 == policy.canonical_sha256
    assert policy.bridge_sha256 in str(policy.canonical_payload())


def test_alignment_v2_fails_before_v1_if_evaluation_uses_wrong_n4_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _oxidation_policy_v2()
    called = False

    def _fake_v1(**_kwargs: object) -> ProcessScientificSupportV1:
        nonlocal called
        called = True
        raise AssertionError("V1 should not be called outside bridge scope")

    monkeypatch.setattr(
        alignment_v2,
        "align_scientific_assertion_to_process_v1",
        _fake_v1,
    )

    evaluation = _FakeEvaluation(
        definition=_FakeDefinition(),
        parameters_payload={
            "source_component_id": "dissolved_inorganic_nitrogen",
            "target_component_id": "biological_nitrogen",
        },
    )
    with pytest.raises(
        ScientificProcessAlignmentV2Error,
        match="outside reviewed model-semantic bridge scope",
    ):
        align_scientific_assertion_to_process_v2(
            evaluation=evaluation,  # type: ignore[arg-type]
            assertion_ref=policy.assertion_ref,
            policy=policy,
            assertions=object(),  # type: ignore[arg-type]
            syntheses=object(),  # type: ignore[arg-type]
        )
    assert called is False
