from __future__ import annotations

from pathlib import Path

from ecobiome.knowledge_persistence import (
    AssertionClaimLinksRow,
    FilesystemContentAddressedArtifactStore,
    KnowledgeSourcesRow,
    KnowledgeSynthesesRow,
    PersistenceConfig,
    ScientificAssertionRevisionsRow,
    ScientificAssertionsRow,
    SourceClaimsRow,
    SQLiteScientificFoundationUnitOfWork,
    initialize_database,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_assertion_payload,
    canonical_json_text,
    canonical_sha256,
    entity_ref,
)
from ecobiome.reasoning.ecosystem_explanation_v1 import (
    build_ecosystem_explanation_v1,
)
from ecobiome.simulation.ecosystem_state_v1 import (
    CanonicalQuantityV1,
    EcosystemStateV1,
    QuantityBasisV1,
)
from ecobiome.simulation.process_v1 import (
    ProcessDefinitionV1,
    ProcessDeltaV1,
    ProcessEvaluationV1,
    ScientificAssertionRefV1,
)
from ecobiome.simulation.scientific_alignment_v1 import (
    ProcessScientificAlignmentPolicyV1,
    ProcessScientificParticipantRequirementV1,
    align_scientific_assertion_to_process_v1,
    attach_scientific_supports_v1,
)

CREATED_AT = "2026-08-21T00:00:00Z"
STALE_ALIGNMENT_UNKNOWN = (
    "scientific assertion refs supplied but process-to-assertion alignment "
    "is not reviewed in N4 V1"
)


def _persistence(
    tmp_path: Path,
) -> tuple[
    PersistenceConfig,
    FilesystemContentAddressedArtifactStore,
    Path,
]:
    repo = tmp_path / "repo"
    repo.mkdir()
    storage = tmp_path / "storage"
    config = PersistenceConfig(
        storage / "scientific.sqlite3",
        storage / "artifacts",
    )
    initialize_database(config, repo_root=repo)
    artifacts = FilesystemContentAddressedArtifactStore(
        config.artifact_store_root
    )
    return config, artifacts, repo


def _state(
    value: str,
    *,
    basis: QuantityBasisV1,
) -> EcosystemStateV1:
    return EcosystemStateV1(
        profile_id="profile-reviewed-alignment",
        quantities=(
            CanonicalQuantityV1(
                variable_id="fixture_quantity",
                value_decimal=value,
                unit="fixture-unit",
                basis=basis,
            ),
        ),
    )


def test_v6_reviewed_alignment_reaches_explanation_trace(
    tmp_path: Path,
) -> None:
    config, artifacts, repo = _persistence(tmp_path)

    participants = [
        {
            "role": "source",
            "entity": entity_ref("entity-source", 1),
        },
        {
            "role": "target",
            "entity": entity_ref("entity-target", 1),
        },
    ]
    qualifiers = {
        "medium": "water",
        "scope": "fixture-reviewed",
    }
    assertion_payload = canonical_assertion_payload(
        assertion_kind="relational",
        predicate="fixture_direct_mechanism",
        participants=participants,
        value={"kind": "none"},
        qualifiers=qualifiers,
    )
    assertion_sha = canonical_sha256(assertion_payload)

    source = KnowledgeSourcesRow(
        id="source-reviewed",
        source_type="fixture",
        canonical_locator="urn:fixture:reviewed-alignment",
        title="reviewed alignment fixture",
        author=None,
        language="en",
        description="",
        imported_at=CREATED_AT,
        source_metadata_json="{}",
        logical_identity_sha256="1" * 64,
        created_at=CREATED_AT,
    )
    claim = SourceClaimsRow(
        id="claim-reviewed",
        source_id=source.id,
        representation_id=None,
        parent_claim_id=None,
        claim_layer="atomic",
        claim_text="fixture direct mechanism",
        claim_text_sha256="2" * 64,
        claim_kind="fixture",
        semantic_type="fixture",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256="2" * 64,
        notes="",
        initial_review_status="reviewed_fixture",
        created_at=CREATED_AT,
    )
    assertion = ScientificAssertionsRow(
        id="assertion-reviewed",
        created_at=CREATED_AT,
        retired_at=None,
    )
    revision = ScientificAssertionRevisionsRow(
        assertion_id=assertion.id,
        revision=1,
        schema_version="scientific-assertion-v1.1",
        assertion_kind="relational",
        predicate="fixture_direct_mechanism",
        participants_json=canonical_json_text(
            assertion_payload["participants"]
        ),
        value_json=canonical_json_text(assertion_payload["value"]),
        qualifiers_json=canonical_json_text(
            assertion_payload["qualifiers"]
        ),
        normalized_text="fixture direct mechanism",
        canonical_payload_sha256=assertion_sha,
        created_at=CREATED_AT,
    )
    link = AssertionClaimLinksRow(
        id="link-reviewed",
        assertion_id=assertion.id,
        assertion_revision=1,
        claim_id=claim.id,
        stance="supports",
        support_mode="direct_observation",
        scope_alignment="exact",
        semantic_alignment="exact",
        review_status="reviewed_fixture",
        reviewed_by="fixture-reviewer",
        reviewed_at=CREATED_AT,
        created_at=CREATED_AT,
    )
    synthesis = KnowledgeSynthesesRow(
        id="synthesis-reviewed",
        assertion_id=assertion.id,
        assertion_revision=1,
        synthesis_revision=1,
        policy_version="fixture",
        evidence_state="contested",
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

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.add_knowledge_source(source)
        assert uow.provenance.add_source_claims([claim]) == 1
        assert uow.assertions.add_assertion(assertion)
        assert uow.assertions.add_assertion_revision(revision)
        assert uow.assertions.add_assertion_claim_link(link)
        assert uow.syntheses.add_knowledge_synthesis(synthesis)
        uow.commit()

    assertion_ref = ScientificAssertionRefV1(
        assertion_id=assertion.id,
        assertion_revision=1,
        canonical_payload_sha256=assertion_sha,
    )
    definition = ProcessDefinitionV1(
        process_id="fixture-reviewed-process",
        version="1",
        label="Fixture reviewed process",
        input_variables=("fixture_quantity",),
        output_variables=("fixture_quantity",),
        required_scientific_assertion_roles=("mechanism",),
    )
    policy = ProcessScientificAlignmentPolicyV1(
        name="fixture-reviewed-policy",
        version="1",
        process_id=definition.process_id,
        process_version=definition.version,
        role="mechanism",
        allowed_predicates=("fixture_direct_mechanism",),
        alignment_class="direct_mechanism_support",
        epistemic_class="explicit_causal_result",
        required_participants=(
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
        required_qualifiers_json=canonical_json_text(qualifiers),
        participant_match_mode="exact",
        qualifier_match_mode="exact",
    )

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        support = align_scientific_assertion_to_process_v1(
            definition=definition,
            assertion_ref=assertion_ref,
            policy=policy,
            assertions=uow.assertions,
            syntheses=uow.syntheses,
        )

    start = _state(
        "1",
        basis=QuantityBasisV1(
            kind="observation",
            reference_id="observation-reviewed",
        ),
    )
    end = _state(
        "2",
        basis=QuantityBasisV1(
            kind="derived",
            reference_id="evaluation-reviewed",
        ),
    )
    pending = ProcessEvaluationV1(
        evaluation_id="evaluation-reviewed",
        definition=definition,
        profile_id=start.profile_id,
        input_state_sha256=start.canonical_sha256,
        output_state_sha256=end.canonical_sha256,
        parameters_json="{}",
        support_status="support_missing",
        parameter_bases=(
            QuantityBasisV1(
                kind="observation",
                reference_id="observation-reviewed",
            ),
        ),
        scientific_assertion_refs=(assertion_ref,),
        deltas=(
            ProcessDeltaV1(
                variable_id="fixture_quantity",
                zone_id=None,
                material_component_id=None,
                before_decimal=1,
                change_decimal=1,
                after_decimal=2,
                unit="fixture-unit",
            ),
        ),
        unknowns=(STALE_ALIGNMENT_UNKNOWN,),
    )

    aligned = attach_scientific_supports_v1(
        pending,
        (support,),
    )
    assert aligned.support_status == "scientific_alignment_reviewed"
    assert STALE_ALIGNMENT_UNKNOWN not in aligned.unknowns
    assert aligned.unknowns == (
        "synthesis_uncertainty: temperature scope unresolved",
    )
    assert aligned.warnings == (
        "synthesis_conflict: one contradictory source",
    )

    trace = build_ecosystem_explanation_v1(
        start,
        end,
        (aligned,),
    )
    assert trace.causal_steps[0].support_status == (
        "scientific_alignment_reviewed"
    )
    assert trace.scientific_assertion_refs == (assertion_ref,)
    assert trace.scientific_supports == (support,)
    assert trace.causal_steps[0].scientific_supports == (support,)
    assert "synthesis_conflict: one contradictory source" in trace.warnings
    assert (
        "synthesis_uncertainty: temperature scope unresolved"
        in trace.unknowns
    )
    assert STALE_ALIGNMENT_UNKNOWN not in trace.unknowns
    assert trace.canonical_sha256
