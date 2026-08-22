from __future__ import annotations

from dataclasses import replace

import pytest

from ecobiome.knowledge_persistence.contracts import (
    AssertionClaimLinksRow,
    KnowledgeSynthesesRow,
    ScientificAssertionRevisionsRow,
    ScientificAssertionsRow,
)
from ecobiome.knowledge_persistence.serialization import canonical_json_text
from ecobiome.simulation.ecosystem_state_v1 import QuantityBasisV1
from ecobiome.simulation.material_balance_v1 import (
    NITROGEN_TRANSFORMATION_EXTENT_V1,
)
from ecobiome.simulation.process_v1 import (
    ProcessDefinitionV1,
    ProcessDeltaV1,
    ProcessEvaluationV1,
    ProcessScientificEvaluationScopeV1,
    ProcessScientificParameterBindingV1,
    ScientificAssertionRefV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    ALIGNMENT_POLICY_DESIGN_SHA256,
    ProcessScientificAlignmentPolicyV1,
    ProcessScientificParticipantRequirementV1,
    ScientificProcessAlignmentV1Error,
    align_scientific_assertion_to_process_v1,
    attach_scientific_supports_v1,
)

CREATED_AT = "2026-08-21T00:00:00Z"
STALE_ALIGNMENT_UNKNOWN = (
    "scientific assertion refs supplied but process-to-assertion alignment "
    "is not reviewed in N4 V1"
)
UNRELATED_ALIGNMENT_UNKNOWN = "sensor alignment pending calibration"


class FakeAssertionRepository:
    def __init__(
        self,
        root: ScientificAssertionsRow | None,
        revision: ScientificAssertionRevisionsRow | None,
        links: tuple[AssertionClaimLinksRow, ...],
    ) -> None:
        self.root = root
        self.revision = revision
        self.links = links

    def get_assertion(
        self,
        assertion_id: str,
    ) -> ScientificAssertionsRow | None:
        if self.root is not None and self.root.id == assertion_id:
            return self.root
        return None

    def get_assertion_revision(
        self,
        assertion_id: str,
        revision: int,
    ) -> ScientificAssertionRevisionsRow | None:
        if (
            self.revision is not None
            and self.revision.assertion_id == assertion_id
            and self.revision.revision == revision
        ):
            return self.revision
        return None

    def find_by_canonical_payload_sha256(
        self,
        sha256: str,
    ) -> tuple[ScientificAssertionRevisionsRow, ...]:
        if (
            self.revision is not None
            and self.revision.canonical_payload_sha256 == sha256
        ):
            return (self.revision,)
        return ()

    def list_assertion_claim_links(
        self,
        assertion_id: str,
        revision: int,
    ) -> tuple[AssertionClaimLinksRow, ...]:
        return tuple(
            link
            for link in self.links
            if link.assertion_id == assertion_id
            and link.assertion_revision == revision
        )


class FakeSynthesisRepository:
    def __init__(
        self,
        rows: tuple[KnowledgeSynthesesRow, ...] = (),
    ) -> None:
        self.rows = rows

    def list_for_assertion(
        self,
        assertion_id: str,
        revision: int,
    ) -> tuple[KnowledgeSynthesesRow, ...]:
        return tuple(
            row
            for row in self.rows
            if row.assertion_id == assertion_id
            and row.assertion_revision == revision
        )


def _definition() -> ProcessDefinitionV1:
    return ProcessDefinitionV1(
        process_id="fixture-reviewed-process",
        version="1",
        label="Fixture reviewed process",
        input_variables=("x",),
        output_variables=("x",),
        required_scientific_assertion_roles=("mechanism",),
    )


def _assertion_ref() -> ScientificAssertionRefV1:
    return ScientificAssertionRefV1(
        assertion_id="assertion-1",
        assertion_revision=1,
        canonical_payload_sha256="a" * 64,
    )


def _root(*, retired: bool = False) -> ScientificAssertionsRow:
    return ScientificAssertionsRow(
        id="assertion-1",
        created_at=CREATED_AT,
        retired_at="2026-08-22T00:00:00Z" if retired else None,
    )


def _participants() -> str:
    return canonical_json_text(
        [
            {
                "role": "source",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-source",
                    "entity_revision": 1,
                },
            },
            {
                "role": "target",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-target",
                    "entity_revision": 1,
                },
            },
        ]
    )


def _revision(
    *,
    predicate: str = "fixture_direct_mechanism",
    sha: str = "a" * 64,
    participants_json: str | None = None,
    qualifiers_json: str = "{}",
) -> ScientificAssertionRevisionsRow:
    return ScientificAssertionRevisionsRow(
        assertion_id="assertion-1",
        revision=1,
        schema_version="scientific-assertion-v1.1",
        assertion_kind="relational",
        predicate=predicate,
        participants_json=(
            _participants()
            if participants_json is None
            else participants_json
        ),
        value_json='{"kind":"none"}',
        qualifiers_json=qualifiers_json,
        normalized_text="fixture direct mechanism",
        canonical_payload_sha256=sha,
        created_at=CREATED_AT,
    )


def _link(
    *,
    stance: str = "supports",
    scope_alignment: str = "exact",
    semantic_alignment: str = "exact",
    reviewed_by: str | None = "fixture-reviewer",
    reviewed_at: str | None = CREATED_AT,
) -> AssertionClaimLinksRow:
    return AssertionClaimLinksRow(
        id="link-1",
        assertion_id="assertion-1",
        assertion_revision=1,
        claim_id="claim-1",
        stance=stance,
        support_mode="direct_observation",
        scope_alignment=scope_alignment,
        semantic_alignment=semantic_alignment,
        review_status="reviewed_fixture",
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        created_at=CREATED_AT,
    )


def _synthesis() -> KnowledgeSynthesesRow:
    return KnowledgeSynthesesRow(
        id="synthesis-1",
        assertion_id="assertion-1",
        assertion_revision=1,
        synthesis_revision=2,
        policy_version="fixture",
        evidence_state="supported_with_uncertainty",
        support_link_count=1,
        contradict_link_count=1,
        independent_support_origin_count=1,
        independent_contradict_origin_count=1,
        source_class_distribution_json="{}",
        methodological_diversity_json="{}",
        scope_summary_json="{}",
        uncertainties_json='["temperature scope unresolved"]',
        conflicts_json='["one contradictory source"]',
        review_status="reviewed_fixture",
        reviewed_by="fixture-reviewer",
        created_at=CREATED_AT,
    )


def _fixture_evaluation_scope() -> ProcessScientificEvaluationScopeV1:
    return ProcessScientificEvaluationScopeV1(
        process_id="fixture-reviewed-process",
        process_version="1",
        role="mechanism",
        required_parameter_bindings=(
            ProcessScientificParameterBindingV1(
                json_pointer="/mechanism_kind",
                expected_value_json='"fixture"',
            ),
        ),
    )


def _policy(
    *,
    predicate: str = "fixture_direct_mechanism",
    alignment_class: str = "direct_mechanism_support",
    epistemic_class: str = "explicit_causal_result",
    required_participants: tuple[
        ProcessScientificParticipantRequirementV1, ...
    ] = (
        ProcessScientificParticipantRequirementV1(
            role="source",
            entity_id="entity-source",
            entity_revision=1,
        ),
        ProcessScientificParticipantRequirementV1(
            role="target",
            entity_id="entity-target",
            entity_revision=1,
        ),
    ),
    required_qualifiers_json: str = "{}",
    participant_match_mode: str = "exact",
    qualifier_match_mode: str = "exact",
    evaluation_scope: ProcessScientificEvaluationScopeV1 | None = None,
) -> ProcessScientificAlignmentPolicyV1:
    return ProcessScientificAlignmentPolicyV1(
        name="fixture-process-alignment",
        version="1",
        process_id="fixture-reviewed-process",
        process_version="1",
        role="mechanism",
        allowed_predicates=(predicate,),
        alignment_class=alignment_class,
        epistemic_class=epistemic_class,
        evaluation_scope=(
            _fixture_evaluation_scope()
            if evaluation_scope is None
            else evaluation_scope
        ),
        required_participants=required_participants,
        required_qualifiers_json=required_qualifiers_json,
        participant_match_mode=participant_match_mode,
        qualifier_match_mode=qualifier_match_mode,
    )


def _repos(
    *,
    root: ScientificAssertionsRow | None = None,
    revision: ScientificAssertionRevisionsRow | None = None,
    links: tuple[AssertionClaimLinksRow, ...] | None = None,
    syntheses: tuple[KnowledgeSynthesesRow, ...] = (),
) -> tuple[FakeAssertionRepository, FakeSynthesisRepository]:
    return (
        FakeAssertionRepository(
            _root() if root is None else root,
            _revision() if revision is None else revision,
            (_link(),) if links is None else links,
        ),
        FakeSynthesisRepository(syntheses),
    )


def _base_evaluation(
    *,
    refs: tuple[ScientificAssertionRefV1, ...] | None = None,
) -> ProcessEvaluationV1:
    ref_tuple = (_assertion_ref(),) if refs is None else refs
    return ProcessEvaluationV1(
        evaluation_id="evaluation-1",
        definition=_definition(),
        profile_id="profile-1",
        input_state_sha256="1" * 64,
        output_state_sha256="2" * 64,
        parameters_json=canonical_json_text({"mechanism_kind": "fixture"}),
        support_status="support_missing",
        parameter_bases=(
            QuantityBasisV1(
                kind="observation",
                reference_id="observation-1",
            ),
        ),
        scientific_assertion_refs=ref_tuple,
        deltas=(
            ProcessDeltaV1(
                variable_id="x",
                zone_id=None,
                material_component_id=None,
                before_decimal=1,
                change_decimal=1,
                after_decimal=2,
                unit="fixture",
            ),
        ),
        unknowns=(STALE_ALIGNMENT_UNKNOWN,),
    )


def test_alignment_policy_is_bound_to_audited_design() -> None:
    assert len(ALIGNMENT_POLICY_DESIGN_SHA256) == 64
    with pytest.raises(ScientificProcessAlignmentV1Error):
        replace(_policy(), design_basis_sha256="f" * 64)


def test_exact_reviewed_alignment_and_attach_preserve_synthesis_uncertainty() -> None:
    assertions, syntheses = _repos(syntheses=(_synthesis(),))
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(),
        assertions=assertions,
        syntheses=syntheses,
    )
    assert support.alignment_class == "direct_mechanism_support"
    assert support.epistemic_class == "explicit_causal_result"
    assert support.evidence_state == "supported_with_uncertainty"
    assert support.warnings == (
        "synthesis_conflict: one contradictory source",
    )
    assert support.uncertainties == (
        "synthesis_uncertainty: temperature scope unresolved",
    )

    aligned = attach_scientific_supports_v1(
        _base_evaluation(),
        (support,),
    )
    assert aligned.support_status == "scientific_alignment_reviewed"
    assert aligned.scientific_assertion_refs == (_assertion_ref(),)
    assert aligned.scientific_supports == (support,)
    assert STALE_ALIGNMENT_UNKNOWN not in aligned.unknowns
    assert aligned.unknowns == (
        "synthesis_uncertainty: temperature scope unresolved",
    )
    assert aligned.warnings == (
        "synthesis_conflict: one contradictory source",
    )
    payload = aligned.canonical_payload()
    assert payload["scientific_supports"][0]["role"] == "mechanism"


def test_interpretive_support_remains_interpretive() -> None:
    assertions, syntheses = _repos()
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(
            alignment_class="interpretive_mechanism_support",
            epistemic_class="interpretive_support",
        ),
        assertions=assertions,
        syntheses=syntheses,
    )
    assert support.alignment_class == "interpretive_mechanism_support"
    assert support.epistemic_class == "interpretive_support"


@pytest.mark.parametrize(
    ("root", "revision", "links", "policy", "message"),
    [
        (
            _root(retired=True),
            _revision(),
            (_link(),),
            _policy(),
            "retired",
        ),
        (
            _root(),
            _revision(sha="b" * 64),
            (_link(),),
            _policy(),
            "canonical SHA mismatch",
        ),
        (
            _root(),
            _revision(),
            (),
            _policy(),
            "no exact reviewed supporting",
        ),
        (
            _root(),
            _revision(),
            (_link(stance="contradicts"),),
            _policy(),
            "no exact reviewed supporting",
        ),
        (
            _root(),
            _revision(),
            (_link(scope_alignment="source_broader"),),
            _policy(),
            "no exact reviewed supporting",
        ),
        (
            _root(),
            _revision(),
            (_link(semantic_alignment="compatible_partial"),),
            _policy(),
            "no exact reviewed supporting",
        ),
        (
            _root(),
            _revision(),
            (_link(reviewed_by=None),),
            _policy(),
            "no exact reviewed supporting",
        ),
        (
            _root(),
            _revision(),
            (_link(reviewed_at=None),),
            _policy(),
            "no exact reviewed supporting",
        ),
        (
            _root(),
            _revision(predicate="other_predicate"),
            (_link(),),
            _policy(),
            "predicate",
        ),
        (
            _root(),
            _revision(),
            (_link(),),
            _policy(
                required_participants=(
                    ProcessScientificParticipantRequirementV1(
                        role="source",
                        entity_id="entity-missing",
                        entity_revision=1,
                    ),
                ),
                participant_match_mode="contains_exact_required",
            ),
            "missing reviewed role/entity/revision",
        ),
    ],
)
def test_alignment_fail_closed(
    root: ScientificAssertionsRow,
    revision: ScientificAssertionRevisionsRow,
    links: tuple[AssertionClaimLinksRow, ...],
    policy: ProcessScientificAlignmentPolicyV1,
    message: str,
) -> None:
    assertions = FakeAssertionRepository(root, revision, links)
    with pytest.raises(ScientificProcessAlignmentV1Error, match=message):
        align_scientific_assertion_to_process_v1(
            evaluation=_base_evaluation(),
            assertion_ref=_assertion_ref(),
            policy=policy,
            assertions=assertions,
            syntheses=FakeSynthesisRepository(),
        )


def test_attach_requires_exact_declared_role_coverage_and_matching_refs() -> None:
    assertions, syntheses = _repos()
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(),
        assertions=assertions,
        syntheses=syntheses,
    )
    wrong_scope = replace(support.evaluation_scope, role="other-role")
    wrong_role = replace(
        support,
        role="other-role",
        evaluation_scope=wrong_scope,
        evaluation_scope_sha256=wrong_scope.canonical_sha256,
    )
    with pytest.raises(ScientificProcessAlignmentV1Error, match="undeclared"):
        attach_scientific_supports_v1(
            _base_evaluation(),
            (wrong_role,),
        )

    other_ref = ScientificAssertionRefV1(
        assertion_id="assertion-2",
        assertion_revision=1,
        canonical_payload_sha256="b" * 64,
    )
    with pytest.raises(
        ScientificProcessAlignmentV1Error,
        match="do not match",
    ):
        attach_scientific_supports_v1(
            _base_evaluation(refs=(other_ref,)),
            (support,),
        )


def test_positive_status_cannot_exist_without_structured_support() -> None:
    with pytest.raises(ValueError, match="requires scientific_supports"):
        replace(
            _base_evaluation(),
            support_status="scientific_alignment_reviewed",
            scientific_supports=(),
        )


def test_legacy_evaluation_payload_is_stable_when_no_supports_are_attached() -> None:
    payload = _base_evaluation().canonical_payload()
    assert "scientific_supports" not in payload

def test_alignment_rejects_reversed_participant_roles() -> None:
    reversed_participants = canonical_json_text(
        [
            {
                "role": "source",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-target",
                    "entity_revision": 1,
                },
            },
            {
                "role": "target",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-source",
                    "entity_revision": 1,
                },
            },
        ]
    )
    assertions, syntheses = _repos(
        revision=_revision(participants_json=reversed_participants)
    )
    with pytest.raises(
        ScientificProcessAlignmentV1Error,
        match="role/entity/revision",
    ):
        align_scientific_assertion_to_process_v1(
            evaluation=_base_evaluation(),
            assertion_ref=_assertion_ref(),
            policy=_policy(),
            assertions=assertions,
            syntheses=syntheses,
        )


def test_alignment_rejects_entity_revision_mismatch() -> None:
    participants = canonical_json_text(
        [
            {
                "role": "source",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-source",
                    "entity_revision": 2,
                },
            },
            {
                "role": "target",
                "entity": {
                    "type": "entity_ref",
                    "entity_id": "entity-target",
                    "entity_revision": 1,
                },
            },
        ]
    )
    assertions, syntheses = _repos(
        revision=_revision(participants_json=participants)
    )
    with pytest.raises(
        ScientificProcessAlignmentV1Error,
        match="role/entity/revision",
    ):
        align_scientific_assertion_to_process_v1(
            evaluation=_base_evaluation(),
            assertion_ref=_assertion_ref(),
            policy=_policy(),
            assertions=assertions,
            syntheses=syntheses,
        )


def test_alignment_rejects_required_qualifier_mismatch() -> None:
    assertions, syntheses = _repos(
        revision=_revision(qualifiers_json='{"medium":"air"}')
    )
    with pytest.raises(ScientificProcessAlignmentV1Error, match="qualifiers"):
        align_scientific_assertion_to_process_v1(
            evaluation=_base_evaluation(),
            assertion_ref=_assertion_ref(),
            policy=_policy(
                required_qualifiers_json='{"medium":"water"}'
            ),
            assertions=assertions,
            syntheses=syntheses,
        )


def test_alignment_exact_qualifiers_reject_unreviewed_extra_context() -> None:
    assertions, syntheses = _repos(
        revision=_revision(
            qualifiers_json='{"medium":"water","temperature":"20C"}'
        )
    )
    with pytest.raises(
        ScientificProcessAlignmentV1Error,
        match="exactly match reviewed policy",
    ):
        align_scientific_assertion_to_process_v1(
            evaluation=_base_evaluation(),
            assertion_ref=_assertion_ref(),
            policy=_policy(
                required_qualifiers_json='{"medium":"water"}'
            ),
            assertions=assertions,
            syntheses=syntheses,
        )


def test_alignment_subset_qualifiers_require_exact_declared_values() -> None:
    assertions, syntheses = _repos(
        revision=_revision(
            qualifiers_json='{"medium":"water","temperature":"20C"}'
        )
    )
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(
            required_qualifiers_json='{"medium":"water"}',
            qualifier_match_mode="contains_exact_required",
        ),
        assertions=assertions,
        syntheses=syntheses,
    )
    assert support.alignment_class == "direct_mechanism_support"


@pytest.mark.parametrize(
    ("alignment_class", "epistemic_class"),
    [
        ("direct_mechanism_support", "interpretive_support"),
        ("interpretive_mechanism_support", "explicit_causal_result"),
    ],
)
def test_policy_rejects_epistemic_strength_reinterpretation(
    alignment_class: str,
    epistemic_class: str,
) -> None:
    with pytest.raises(
        ScientificProcessAlignmentV1Error,
        match="epistemic strength",
    ):
        _policy(
            alignment_class=alignment_class,
            epistemic_class=epistemic_class,
        )


def test_positive_evaluation_rejects_pending_alignment_unknown() -> None:
    assertions, syntheses = _repos()
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(),
        assertions=assertions,
        syntheses=syntheses,
    )
    with pytest.raises(ValueError, match="pending/not-reviewed"):
        replace(
            _base_evaluation(),
            support_status="scientific_alignment_reviewed",
            scientific_supports=(support,),
        )

def test_attach_preserves_unrelated_alignment_unknown() -> None:
    assertions, syntheses = _repos(syntheses=(_synthesis(),))
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(),
        assertions=assertions,
        syntheses=syntheses,
    )
    evaluation = replace(
        _base_evaluation(),
        unknowns=(
            STALE_ALIGNMENT_UNKNOWN,
            UNRELATED_ALIGNMENT_UNKNOWN,
        ),
    )
    aligned = attach_scientific_supports_v1(
        evaluation,
        (support,),
    )
    assert STALE_ALIGNMENT_UNKNOWN not in aligned.unknowns
    assert UNRELATED_ALIGNMENT_UNKNOWN in aligned.unknowns
    assert "synthesis_uncertainty: temperature scope unresolved" in aligned.unknowns


def test_positive_evaluation_allows_unrelated_alignment_unknown() -> None:
    assertions, syntheses = _repos()
    support = align_scientific_assertion_to_process_v1(
        evaluation=_base_evaluation(),
        assertion_ref=_assertion_ref(),
        policy=_policy(),
        assertions=assertions,
        syntheses=syntheses,
    )
    evaluation = replace(
        _base_evaluation(),
        unknowns=(UNRELATED_ALIGNMENT_UNKNOWN,),
        support_status="scientific_alignment_reviewed",
        scientific_supports=(support,),
    )
    assert evaluation.unknowns == (UNRELATED_ALIGNMENT_UNKNOWN,)

def _nitrogen_scope(
    source_component_id: str,
    target_component_id: str,
) -> ProcessScientificEvaluationScopeV1:
    return ProcessScientificEvaluationScopeV1(
        process_id=NITROGEN_TRANSFORMATION_EXTENT_V1.process_id,
        process_version=NITROGEN_TRANSFORMATION_EXTENT_V1.version,
        role="mechanism",
        required_parameter_bindings=(
            ProcessScientificParameterBindingV1(
                json_pointer="/source_component_id",
                expected_value_json=canonical_json_text(source_component_id),
            ),
            ProcessScientificParameterBindingV1(
                json_pointer="/target_component_id",
                expected_value_json=canonical_json_text(target_component_id),
            ),
        ),
    )


def _nitrogen_evaluation(
    source_component_id: str,
    target_component_id: str,
    *,
    evaluation_id: str,
    zone_id: str = "water",
    extent: str = "1",
    extent_basis_reference: str = "observation-nitrogen",
) -> ProcessEvaluationV1:
    return ProcessEvaluationV1(
        evaluation_id=evaluation_id,
        definition=NITROGEN_TRANSFORMATION_EXTENT_V1,
        profile_id="profile-nitrogen-scope",
        input_state_sha256="3" * 64,
        output_state_sha256="4" * 64,
        parameters_json=canonical_json_text(
            {
                "zone_id": zone_id,
                "source_component_id": source_component_id,
                "target_component_id": target_component_id,
                "extent": {
                    "value": {"type": "decimal", "value": extent},
                    "unit": "mg N",
                },
                "extent_basis": {
                    "kind": "observation",
                    "reference_id": extent_basis_reference,
                },
            }
        ),
        support_status="support_missing",
        parameter_bases=(
            QuantityBasisV1(kind="observation", reference_id=extent_basis_reference),
        ),
        scientific_assertion_refs=(_assertion_ref(),),
        deltas=(
            ProcessDeltaV1(
                variable_id="material_inventory", zone_id=zone_id,
                material_component_id=source_component_id,
                before_decimal=10, change_decimal=-1, after_decimal=9, unit="mg N",
            ),
            ProcessDeltaV1(
                variable_id="material_inventory", zone_id=zone_id,
                material_component_id=target_component_id,
                before_decimal=1, change_decimal=1, after_decimal=2, unit="mg N",
            ),
        ),
        unknowns=(STALE_ALIGNMENT_UNKNOWN,),
    )


def _nitrogen_policy(scope: ProcessScientificEvaluationScopeV1) -> ProcessScientificAlignmentPolicyV1:
    return ProcessScientificAlignmentPolicyV1(
        name="fixture-nitrogen-scope-policy", version="1",
        process_id=NITROGEN_TRANSFORMATION_EXTENT_V1.process_id,
        process_version=NITROGEN_TRANSFORMATION_EXTENT_V1.version,
        role="mechanism", allowed_predicates=("fixture_direct_mechanism",),
        alignment_class="direct_mechanism_support",
        epistemic_class="explicit_causal_result",
        evaluation_scope=scope,
        required_participants=(
            ProcessScientificParticipantRequirementV1(
                role="source", entity_id="entity-source", entity_revision=1
            ),
            ProcessScientificParticipantRequirementV1(
                role="target", entity_id="entity-target", entity_revision=1
            ),
        ),
    )


def _nitrogen_support(
    evaluation: ProcessEvaluationV1,
    scope: ProcessScientificEvaluationScopeV1,
):
    assertions, syntheses = _repos()
    return align_scientific_assertion_to_process_v1(
        evaluation=evaluation,
        assertion_ref=_assertion_ref(),
        policy=_nitrogen_policy(scope),
        assertions=assertions,
        syntheses=syntheses,
    )


def test_evaluation_scope_prevents_cross_transformation_support_reuse() -> None:
    oxidation_scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    assimilation_scope = _nitrogen_scope(
        "dissolved_inorganic_nitrogen", "biological_nitrogen"
    )
    assert oxidation_scope.canonical_sha256 == (
        "f673fb12a5234af0bc2857660624555c9b5340255047aca71333c91877f6de2b"
    )
    assert assimilation_scope.canonical_sha256 == (
        "00d4df977ea146ed1208bec93d73ea20b76c26b5276458bb6ef748a3f905484b"
    )
    oxidation = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-oxidation",
    )
    assimilation = _nitrogen_evaluation(
        "dissolved_inorganic_nitrogen", "biological_nitrogen",
        evaluation_id="evaluation-assimilation",
    )
    oxidation_support = _nitrogen_support(oxidation, oxidation_scope)
    assimilation_support = _nitrogen_support(assimilation, assimilation_scope)
    assert attach_scientific_supports_v1(
        oxidation, (oxidation_support,)
    ).support_status == "scientific_alignment_reviewed"
    assert attach_scientific_supports_v1(
        assimilation, (assimilation_support,)
    ).support_status == "scientific_alignment_reviewed"
    with pytest.raises(ScientificProcessAlignmentV1Error, match="evaluation scope"):
        attach_scientific_supports_v1(assimilation, (oxidation_support,))
    with pytest.raises(ScientificProcessAlignmentV1Error, match="evaluation scope"):
        attach_scientific_supports_v1(oxidation, (assimilation_support,))


@pytest.mark.parametrize(
    ("source_component_id", "target_component_id"),
    [
        ("dissolved_inorganic_nitrogen", "oxidized_inorganic_nitrogen"),
        ("reduced_inorganic_nitrogen", "biological_nitrogen"),
    ],
)
def test_evaluation_scope_rejects_single_endpoint_mismatch(
    source_component_id: str,
    target_component_id: str,
) -> None:
    scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    evaluation = _nitrogen_evaluation(
        source_component_id, target_component_id,
        evaluation_id="evaluation-endpoint-mismatch",
    )
    with pytest.raises(ValueError, match="does not match"):
        scope.require_match(
            process_id=evaluation.definition.process_id,
            process_version=evaluation.definition.version,
            role="mechanism",
            parameters=evaluation.parameters_payload,
        )


def test_evaluation_scope_rejects_missing_bound_parameter() -> None:
    scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    evaluation = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-missing-parameter",
    )
    parameters = evaluation.parameters_payload
    del parameters["target_component_id"]
    with pytest.raises(ValueError, match="is missing"):
        scope.require_match(
            process_id=evaluation.definition.process_id,
            process_version=evaluation.definition.version,
            role="mechanism",
            parameters=parameters,
        )


def test_same_reviewed_pair_allows_execution_parameter_changes() -> None:
    scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    first = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-execution-first", zone_id="water-a", extent="1",
        extent_basis_reference="observation-a",
    )
    support = _nitrogen_support(first, scope)
    second = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-execution-second", zone_id="water-b", extent="3",
        extent_basis_reference="observation-b",
    )
    assert attach_scientific_supports_v1(
        second, (support,)
    ).support_status == "scientific_alignment_reviewed"


def test_positive_evaluation_direct_construction_rejects_scope_bypass() -> None:
    scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    oxidation = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-bypass-source",
    )
    support = _nitrogen_support(oxidation, scope)
    assimilation = _nitrogen_evaluation(
        "dissolved_inorganic_nitrogen", "biological_nitrogen",
        evaluation_id="evaluation-bypass-target",
    )
    with pytest.raises(ValueError, match="evaluation scope mismatch"):
        replace(
            assimilation,
            support_status="scientific_alignment_reviewed",
            scientific_supports=(support,),
            unknowns=(),
        )


def test_support_rejects_evaluation_scope_sha_mismatch() -> None:
    scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    evaluation = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-scope-sha",
    )
    support = _nitrogen_support(evaluation, scope)
    with pytest.raises(ValueError, match="must match evaluation_scope"):
        replace(support, evaluation_scope_sha256="f" * 64)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("process_id", "other-process", "process_id mismatch"),
        ("process_version", "2", "process_version mismatch"),
        ("role", "other-role", "role mismatch"),
    ],
)
def test_evaluation_scope_rejects_process_identity_mismatch(
    field: str,
    value: str,
    message: str,
) -> None:
    scope = _nitrogen_scope(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen"
    )
    kwargs = {
        "process_id": NITROGEN_TRANSFORMATION_EXTENT_V1.process_id,
        "process_version": NITROGEN_TRANSFORMATION_EXTENT_V1.version,
        "role": "mechanism",
    }
    kwargs[field] = value
    evaluation = _nitrogen_evaluation(
        "reduced_inorganic_nitrogen", "oxidized_inorganic_nitrogen",
        evaluation_id="evaluation-process-identity",
    )
    with pytest.raises(ValueError, match=message):
        scope.require_match(
            process_id=kwargs["process_id"],
            process_version=kwargs["process_version"],
            role=kwargs["role"],
            parameters=evaluation.parameters_payload,
        )


def test_parameter_binding_rejects_malformed_json_pointer() -> None:
    with pytest.raises(ValueError, match="absolute JSON Pointer"):
        ProcessScientificParameterBindingV1(
            json_pointer="source_component_id",
            expected_value_json='"reduced_inorganic_nitrogen"',
        )
    with pytest.raises(ValueError, match="invalid escape"):
        ProcessScientificParameterBindingV1(
            json_pointer="/source~2component",
            expected_value_json='"reduced_inorganic_nitrogen"',
        )


def test_evaluation_scope_rejects_duplicate_json_pointer() -> None:
    binding = ProcessScientificParameterBindingV1(
        json_pointer="/source_component_id",
        expected_value_json='"reduced_inorganic_nitrogen"',
    )
    with pytest.raises(ValueError, match="must be unique"):
        ProcessScientificEvaluationScopeV1(
            process_id=NITROGEN_TRANSFORMATION_EXTENT_V1.process_id,
            process_version=NITROGEN_TRANSFORMATION_EXTENT_V1.version,
            role="mechanism",
            required_parameter_bindings=(binding, binding),
        )

