"""Backend-neutral typed persistence contracts — Scientific Foundation V1.1."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, Self


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    key: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class AcquisitionJobsRow:
    id: str
    source_id: str | None
    adapter_name: str
    adapter_version: str
    requested_locator: str
    requested_language: str | None
    preferred_languages_json: str
    maximum_input_bytes: int | None
    outcome: str
    request_json: str
    diagnostics_json: str
    started_at: str | None
    completed_at: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class AssertionClaimLinksRow:
    id: str
    assertion_id: str
    assertion_revision: int
    claim_id: str
    stance: str
    support_mode: str
    scope_alignment: str
    semantic_alignment: str
    review_status: str
    reviewed_by: str | None
    reviewed_at: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class ClaimEvidenceLinksRow:
    claim_id: str
    evidence_id: str
    evidence_order: int
    link_role: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ClaimReviewEventsRow:
    id: str
    claim_id: str
    decision: str
    reviewer: str | None
    notes: str
    corrected_text: str | None
    corrected_text_sha256: str | None
    review_metadata_json: str
    reviewed_at: str


@dataclass(frozen=True, slots=True)
class SegmentReviewEventsRow:
    id: str
    segment_id: str
    decision: str
    reviewer: str | None
    rationale: str
    corrected_text: str | None
    corrected_text_sha256: str | None
    review_metadata_json: str
    reviewed_at: str


@dataclass(frozen=True, slots=True)
class DerivationsRow:
    id: str
    child_representation_id: str
    parent_raw_artifact_id: str | None
    parent_representation_id: str | None
    derivation_method: str
    tool_name: str | None
    tool_version: str | None
    parameters_json: str
    created_at: str


@dataclass(frozen=True, slots=True)
class EvidenceAssessmentsRow:
    id: str
    assertion_claim_link_id: str
    policy_version: str
    study_design: str
    evidence_directness: str
    endpoint_or_response_json: str
    study_scope_json: str
    methodological_dimensions_json: str
    statistical_result_json: str
    independence_status: str
    limitations_json: str
    assessor: str
    created_at: str
    supersedes_assessment_id: str | None


@dataclass(frozen=True, slots=True)
class KnowledgeSourcesRow:
    id: str
    source_type: str
    canonical_locator: str
    title: str
    author: str | None
    language: str
    description: str
    imported_at: str
    source_metadata_json: str
    logical_identity_sha256: str
    created_at: str


@dataclass(frozen=True, slots=True)
class KnowledgeSynthesesRow:
    id: str
    assertion_id: str
    assertion_revision: int
    synthesis_revision: int
    policy_version: str
    evidence_state: str
    support_link_count: int
    contradict_link_count: int
    independent_support_origin_count: int
    independent_contradict_origin_count: int
    source_class_distribution_json: str
    methodological_diversity_json: str
    scope_summary_json: str
    uncertainties_json: str
    conflicts_json: str
    review_status: str
    reviewed_by: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class RawArtifactsRow:
    id: str
    retrieval_id: str
    payload_role: str
    media_type: str
    size_bytes: int
    content_sha256: str
    artifact_store_key: str
    license_id: str | None
    license_evidence_locator: str | None
    materialization_policy: str
    immutable: int
    created_at: str


@dataclass(frozen=True, slots=True)
class RepresentationsRow:
    id: str
    source_id: str
    origin_raw_artifact_id: str | None
    logical_key: str
    representation_kind: str
    media_type: str
    language: str | None
    content_sha256: str
    artifact_store_key: str | None
    materialization_status: str
    metadata_json: str
    created_at: str


@dataclass(frozen=True, slots=True)
class RetrievalsRow:
    id: str
    acquisition_job_id: str
    retrieval_index: int
    retrieval_method: str
    requested_locator: str
    resolved_locator: str | None
    retrieved_at: str | None
    transport_status: str
    transport_metadata_json: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ScientificAssertionRevisionsRow:
    assertion_id: str
    revision: int
    schema_version: str
    assertion_kind: str
    predicate: str
    participants_json: str
    value_json: str
    qualifiers_json: str
    normalized_text: str
    canonical_payload_sha256: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ScientificAssertionsRow:
    id: str
    created_at: str
    retired_at: str | None


@dataclass(frozen=True, slots=True)
class ScientificEntitiesRow:
    id: str
    entity_kind: str
    created_at: str
    retired_at: str | None


@dataclass(frozen=True, slots=True)
class ScientificEntityIdentifiersRow:
    id: str
    entity_id: str
    scheme: str
    authority_namespace: str
    authority_version: str
    external_id: str
    mapping_status: str
    mapping_review_status: str
    authority_source_id: str | None
    valid_from: str | None
    valid_to: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class ScientificEntityNameUsagesRow:
    id: str
    entity_id: str | None
    source_id: str
    verbatim_name: str
    language: str | None
    script: str | None
    usage_status: str
    nomenclatural_status: str | None
    mapping_review_status: str
    source_version: str | None
    retrieval_id: str | None
    segment_id: str | None
    segment_char_start: int | None
    segment_char_end: int | None
    created_at: str


@dataclass(frozen=True, slots=True)
class ScientificEntityRelationsRow:
    id: str
    subject_entity_id: str
    relation: str
    object_entity_id: str
    semantics_version: str
    qualifiers_json: str
    review_status: str
    valid_from: str | None
    valid_to: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class ScientificEntityRevisionsRow:
    entity_id: str
    revision: int
    schema_version: str
    canonical_label: str
    canonical_payload_json: str
    canonical_payload_sha256: str
    review_status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SegmentsRow:
    id: str
    representation_id: str
    segment_index: int
    text_inline: str | None
    text_sha256: str
    materialization_status: str
    representation_char_start: int | None
    representation_char_end: int | None
    start_seconds_decimal: str | None
    end_seconds_decimal: str | None
    page_number: int | None
    frame_start: int | None
    frame_end: int | None
    review_status: str | None
    metadata_json: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SfSchemaMetadataRow:
    schema_name: str
    schema_version: int
    design_sha256: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SourceAssessmentsRow:
    id: str
    source_id: str
    policy_version: str
    source_class: str
    peer_review_status: str
    publication_status: str
    retraction_status: str
    license_status: str
    institutional_or_publisher_context_json: str
    assessment_notes_json: str
    assessor: str
    created_at: str
    supersedes_assessment_id: str | None


@dataclass(frozen=True, slots=True)
class SourceClaimsRow:
    id: str
    source_id: str
    representation_id: str | None
    parent_claim_id: str | None
    claim_layer: str
    claim_text: str
    claim_text_sha256: str
    claim_kind: str | None
    semantic_type: str | None
    qualifiers_json: str
    extraction_confidence_decimal: str | None
    source_claim_effective_text_sha256: str | None
    notes: str
    initial_review_status: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class SourceEvidenceRow:
    id: str
    segment_id: str
    segment_char_start: int
    segment_char_end: int
    evidence_text_sha256: str
    start_seconds_decimal: str | None
    end_seconds_decimal: str | None
    page_number: int | None
    frame_start: int | None
    frame_end: int | None
    evidence_metadata_json: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SourceLineageEdgesRow:
    id: str
    parent_source_id: str
    child_source_id: str
    relation: str
    basis_claim_id: str | None
    basis_evidence_json: str
    review_status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticProviderRunsRow:
    id: str
    run_kind: str
    provider_name: str
    provider_adapter_name: str
    provider_adapter_version: str
    endpoint: str | None
    model_requested: str
    semantic_contract_name: str
    semantic_contract_version: str
    semantic_contract_sha256: str
    instruction_sha256: str
    output_schema_sha256: str
    source_request_sha256: str
    request_body_sha256: str
    request_artifact_store_key: str
    request_fingerprint_sha256: str
    safe_configuration_json: str
    started_at: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticProviderRunClaimInputsRow:
    run_id: str
    claim_id: str
    input_order: int
    claim_effective_text_sha256: str
    claim_review_status_at_run: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticProviderRunEvidenceInputsRow:
    run_id: str
    claim_id: str
    evidence_id: str
    evidence_order: int
    evidence_text_sha256: str
    segment_review_status_at_run: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticProviderRunEventsRow:
    id: str
    run_id: str
    event_index: int
    event_type: str
    model_returned: str | None
    provider_request_id: str | None
    provider_response_id: str | None
    http_status_code: int | None
    response_status: str | None
    content_type: str | None
    response_body_sha256: str | None
    response_artifact_store_key: str | None
    validated_output_sha256: str | None
    validated_output_artifact_store_key: str | None
    usage_json: str
    diagnostics_json: str
    proposal_count: int | None
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticCandidatesRow:
    id: str
    schema_version: str
    semantic_contract_name: str
    semantic_contract_version: str
    semantic_contract_sha256: str
    relation_type_basis_version: str
    relation_type_registry_sha256: str
    grounding_policy_sha256: str
    claim_scoped_provenance_policy_sha256: str
    source_statement_claim_id: str
    source_claim_effective_text_sha256: str
    semantic_type: str
    relation: str
    epistemic_class: str
    promotion_readiness: str
    automatic_scientific_acceptance: int
    canonical_candidate_sha256: str
    canonical_candidate_document_sha256: str
    canonical_candidate_json: str
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticCandidateEvidenceLinksRow:
    semantic_candidate_id: str
    source_statement_claim_id: str
    evidence_id: str
    evidence_order: int
    created_at: str


@dataclass(frozen=True, slots=True)
class SemanticCandidateEntityResolutionEventsRow:
    id: str
    semantic_candidate_id: str
    semantic_candidate_sha256: str
    role: str
    candidate_argument_sha256: str
    entity_name_usage_id: str
    entity_id: str
    entity_revision: int
    mapping_status: str
    decision: str
    reviewer: str
    rationale: str
    review_policy_name: str
    review_policy_version: str
    review_policy_sha256: str
    reviewed_at: str


@dataclass(frozen=True, slots=True)
class SemanticCandidateReviewEventsRow:
    id: str
    semantic_candidate_id: str
    semantic_candidate_sha256: str
    decision: str
    reviewer: str
    review_text: str
    review_text_sha256: str
    rationale: str
    review_metadata_json: str
    review_policy_name: str
    review_policy_version: str
    review_policy_sha256: str
    replacement_candidate_id: str | None
    replacement_candidate_sha256: str | None
    reviewed_at: str


@dataclass(frozen=True, slots=True)
class SemanticProviderCandidateOriginsRow:
    run_id: str
    proposal_index: int
    semantic_candidate_id: str
    proposal_sha256: str
    created_at: str


class RawArtifactStore(Protocol):
    def put(self, data: bytes) -> StoredArtifact: ...
    def get(self, key: str) -> bytes: ...
    def verify(self, key: str) -> StoredArtifact: ...


class ProvenanceRepository(Protocol):
    def add_knowledge_source(self, row: KnowledgeSourcesRow) -> bool: ...
    def add_acquisition_job(self, row: AcquisitionJobsRow) -> bool: ...
    def add_retrieval(self, row: RetrievalsRow) -> bool: ...
    def add_raw_artifact(self, row: RawArtifactsRow) -> bool: ...
    def add_representation(self, row: RepresentationsRow) -> bool: ...
    def add_derivation(self, row: DerivationsRow) -> bool: ...
    def add_segments(self, rows: Sequence[SegmentsRow]) -> int: ...
    def add_source_evidence(self, rows: Sequence[SourceEvidenceRow]) -> int: ...
    def add_source_claims(self, rows: Sequence[SourceClaimsRow]) -> int: ...
    def add_claim_evidence_links(self, rows: Sequence[ClaimEvidenceLinksRow]) -> int: ...
    def add_claim_review_events(self, rows: Sequence[ClaimReviewEventsRow]) -> int: ...
    def get_claim_review_events(
        self, claim_id: str
    ) -> Sequence[ClaimReviewEventsRow]: ...
    def record_claim_review_event(self, row: ClaimReviewEventsRow) -> bool: ...
    def add_segment_review_events(self, rows: Sequence[SegmentReviewEventsRow]) -> int: ...
    def get_segment_review_events(
        self, segment_id: str
    ) -> Sequence[SegmentReviewEventsRow]: ...
    def record_segment_review_event(self, row: SegmentReviewEventsRow) -> bool: ...
    def get_source_claim(self, claim_id: str) -> SourceClaimsRow | None: ...


class ScientificEntityRepository(Protocol):
    def add_entity(self, row: ScientificEntitiesRow) -> bool: ...
    def add_entity_revision(self, row: ScientificEntityRevisionsRow) -> bool: ...
    def add_identifier(self, row: ScientificEntityIdentifiersRow) -> bool: ...
    def add_name_usage(self, row: ScientificEntityNameUsagesRow) -> bool: ...
    def add_entity_relation(self, row: ScientificEntityRelationsRow) -> bool: ...
    def add_candidate_entity_resolution_event(
        self, row: SemanticCandidateEntityResolutionEventsRow
    ) -> bool: ...
    def list_candidate_entity_resolution_events(
        self, candidate_id: str, role: str | None = None
    ) -> Sequence[SemanticCandidateEntityResolutionEventsRow]: ...
    def get_name_usage(
        self, name_usage_id: str
    ) -> ScientificEntityNameUsagesRow | None: ...
    def get_entity_revision(self, entity_id: str, revision: int) -> ScientificEntityRevisionsRow | None: ...


class ScientificAssertionRepository(Protocol):
    def add_assertion(self, row: ScientificAssertionsRow) -> bool: ...
    def add_assertion_revision(self, row: ScientificAssertionRevisionsRow) -> bool: ...
    def add_assertion_claim_link(self, row: AssertionClaimLinksRow) -> bool: ...
    def get_assertion_revision(self, assertion_id: str, revision: int) -> ScientificAssertionRevisionsRow | None: ...
    def find_by_canonical_payload_sha256(self, sha256: str) -> Sequence[ScientificAssertionRevisionsRow]: ...


class ScientificAssessmentRepository(Protocol):
    def add_source_assessment(self, row: SourceAssessmentsRow) -> bool: ...
    def add_evidence_assessment(self, row: EvidenceAssessmentsRow) -> bool: ...
    def add_source_lineage_edge(self, row: SourceLineageEdgesRow) -> bool: ...


class KnowledgeSynthesisRepository(Protocol):
    def add_knowledge_synthesis(self, row: KnowledgeSynthesesRow) -> bool: ...
    def list_for_assertion(self, assertion_id: str, revision: int) -> Sequence[KnowledgeSynthesesRow]: ...


class SemanticProviderAuditRepository(Protocol):
    def add_provider_run(self, row: SemanticProviderRunsRow) -> bool: ...
    def add_provider_run_claim_inputs(
        self, rows: Sequence[SemanticProviderRunClaimInputsRow]
    ) -> int: ...
    def add_provider_run_evidence_inputs(
        self, rows: Sequence[SemanticProviderRunEvidenceInputsRow]
    ) -> int: ...
    def add_provider_run_events(
        self, rows: Sequence[SemanticProviderRunEventsRow]
    ) -> int: ...
    def list_provider_run_events(
        self, run_id: str
    ) -> Sequence[SemanticProviderRunEventsRow]: ...
    def add_provider_candidate_origins(
        self, rows: Sequence[SemanticProviderCandidateOriginsRow]
    ) -> int: ...


class SemanticCandidateRepository(Protocol):
    def add_candidate(
        self,
        row: SemanticCandidatesRow,
        evidence_links: Sequence[SemanticCandidateEvidenceLinksRow],
    ) -> tuple[SemanticCandidatesRow, bool]: ...
    def add_candidate_evidence_links(
        self, rows: Sequence[SemanticCandidateEvidenceLinksRow]
    ) -> int: ...
    def get_candidate(self, candidate_id: str) -> SemanticCandidatesRow | None: ...
    def list_candidates(
        self, *, limit: int = 50
    ) -> Sequence[SemanticCandidatesRow]: ...
    def get_candidate_evidence_links(
        self, candidate_id: str
    ) -> Sequence[SemanticCandidateEvidenceLinksRow]: ...
    def find_by_canonical_candidate_sha256(
        self, sha256: str
    ) -> SemanticCandidatesRow | None: ...
    def add_review_event(self, row: SemanticCandidateReviewEventsRow) -> bool: ...
    def list_review_events(
        self, candidate_id: str
    ) -> Sequence[SemanticCandidateReviewEventsRow]: ...


class ScientificFoundationUnitOfWork(Protocol):
    provenance: ProvenanceRepository
    entities: ScientificEntityRepository
    assertions: ScientificAssertionRepository
    assessments: ScientificAssessmentRepository
    syntheses: KnowledgeSynthesisRepository
    provider_audit: SemanticProviderAuditRepository
    semantic_candidates: SemanticCandidateRepository
    artifact_store: RawArtifactStore

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def verify_artifact_reference(self, key: str) -> None: ...
