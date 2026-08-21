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
from ecobiome.simulation.process_v1 import (
    ProcessDefinitionV1,
    ProcessDeltaV1,
    ProcessEvaluationV1,
    ScientificAssertionRefV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    ALIGNMENT_POLICY_DESIGN_SHA256,
    ProcessScientificAlignmentPolicyV1,
    ScientificProcessAlignmentV1Error,
    align_scientific_assertion_to_process_v1,
    attach_scientific_supports_v1,
)

CREATED_AT = "2026-08-21T00:00:00Z"


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
) -> ScientificAssertionRevisionsRow:
    return ScientificAssertionRevisionsRow(
        assertion_id="assertion-1",
        revision=1,
        schema_version="scientific-assertion-v1.1",
        assertion_kind="relational",
        predicate=predicate,
        participants_json=_participants(),
        value_json='{"kind":"none"}',
        qualifiers_json="{}",
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


def _policy(
    *,
    predicate: str = "fixture_direct_mechanism",
    alignment_class: str = "direct_mechanism_support",
    epistemic_class: str = "explicit_causal_result",
    required_entity_ids: tuple[str, ...] = (
        "entity-source",
        "entity-target",
    ),
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
        required_entity_ids=required_entity_ids,
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
        parameters_json="{}",
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
        unknowns=("scientific alignment pending",),
    )


def test_alignment_policy_is_bound_to_audited_design() -> None:
    assert len(ALIGNMENT_POLICY_DESIGN_SHA256) == 64
    with pytest.raises(ScientificProcessAlignmentV1Error):
        replace(_policy(), design_basis_sha256="f" * 64)


def test_exact_reviewed_alignment_and_attach_preserve_synthesis_uncertainty() -> None:
    assertions, syntheses = _repos(syntheses=(_synthesis(),))
    support = align_scientific_assertion_to_process_v1(
        definition=_definition(),
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
    payload = aligned.canonical_payload()
    assert payload["scientific_supports"][0]["role"] == "mechanism"


def test_interpretive_support_remains_interpretive() -> None:
    assertions, syntheses = _repos()
    support = align_scientific_assertion_to_process_v1(
        definition=_definition(),
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
            _policy(required_entity_ids=("entity-missing",)),
            "missing required exact entity",
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
            definition=_definition(),
            assertion_ref=_assertion_ref(),
            policy=policy,
            assertions=assertions,
            syntheses=FakeSynthesisRepository(),
        )


def test_attach_requires_exact_declared_role_coverage_and_matching_refs() -> None:
    assertions, syntheses = _repos()
    support = align_scientific_assertion_to_process_v1(
        definition=_definition(),
        assertion_ref=_assertion_ref(),
        policy=_policy(),
        assertions=assertions,
        syntheses=syntheses,
    )
    wrong_role = replace(support, role="other-role")
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
