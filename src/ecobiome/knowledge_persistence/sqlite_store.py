"""SQLite Scientific Foundation adapter candidate."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from contextlib import suppress
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

from .config import PersistenceConfig
from .contracts import (
    AcquisitionJobsRow,
    AssertionClaimLinksRow,
    ClaimEvidenceLinksRow,
    ClaimReviewEventsRow,
    DerivationsRow,
    EvidenceAssessmentsRow,
    KnowledgeSourcesRow,
    KnowledgeSynthesesRow,
    RawArtifactsRow,
    RawArtifactStore,
    RepresentationsRow,
    RetrievalsRow,
    ScientificAssertionRevisionsRow,
    ScientificAssertionsRow,
    ScientificEntitiesRow,
    ScientificEntityIdentifiersRow,
    ScientificEntityNameUsagesRow,
    ScientificEntityRelationsRow,
    ScientificEntityRevisionsRow,
    SegmentReviewEventsRow,
    SegmentsRow,
    SemanticCandidateEntityResolutionEventsRow,
    SemanticCandidateEvidenceLinksRow,
    SemanticCandidateReviewEventsRow,
    SemanticCandidatesRow,
    SemanticProviderCandidateOriginsRow,
    SemanticProviderRunClaimInputsRow,
    SemanticProviderRunEventsRow,
    SemanticProviderRunEvidenceInputsRow,
    SemanticProviderRunsRow,
    SfSchemaMetadataRow,
    SourceAssessmentsRow,
    SourceClaimsRow,
    SourceEvidenceRow,
    SourceLineageEdgesRow,
)
from .errors import (
    DuplicateIdentityConflict,
    PersistenceIntegrityError,
    SchemaIdentityError,
    ScopeAlignmentError,
)
from .serialization import (
    canonical_assertion_payload,
    canonical_json_text,
    canonical_sha256,
)
from .sqlite_schema import (
    COMPLETE_DDL,
    EXPECTED_INDEXES,
    EXPECTED_TABLES,
    INDEX_ADDENDUM,
    RUNTIME_SCHEMA_DESIGN_SHA256,
    SCHEMA_VERSION,
)

_STANCE_VALUES = frozenset({
    "supports",
    "contradicts",
    "qualifies",
    "context_only",
    "duplicate_report",
})
_SUPPORT_MODE_VALUES = frozenset({
    "direct_observation",
    "direct_measurement",
    "statistical_analysis",
    "author_interpretation",
    "secondary_report",
    "independent_reanalysis",
    "method_or_scope_context",
    "unknown",
})
_SCOPE_ALIGNMENT_VALUES = frozenset({
    "exact",
    "source_narrower",
    "source_broader",
    "partially_overlapping",
    "incompatible",
    "unresolved",
})
_SEMANTIC_ALIGNMENT_VALUES = frozenset({
    "exact",
    "compatible_partial",
    "contradictory",
    "insufficient_to_link",
    "unresolved",
})
_CLAIM_REVIEW_DECISIONS = frozenset({"accept", "correct", "reject"})
_SEGMENT_REVIEW_DECISIONS = frozenset({"accept", "correct", "reject"})
_SEGMENT_REVIEW_STATUS_BY_DECISION = {
    "accept": "accepted",
    "correct": "corrected",
    "reject": "rejected",
}


_TABLE_SPECS = {
    AcquisitionJobsRow: ('acquisition_jobs', ('id', 'source_id', 'adapter_name', 'adapter_version', 'requested_locator', 'requested_language', 'preferred_languages_json', 'maximum_input_bytes', 'outcome', 'request_json', 'diagnostics_json', 'started_at', 'completed_at', 'created_at'), ('id',)),
    AssertionClaimLinksRow: ('assertion_claim_links', ('id', 'assertion_id', 'assertion_revision', 'claim_id', 'stance', 'support_mode', 'scope_alignment', 'semantic_alignment', 'review_status', 'reviewed_by', 'reviewed_at', 'created_at'), ('id',)),
    ClaimEvidenceLinksRow: ('claim_evidence_links', ('claim_id', 'evidence_id', 'evidence_order', 'link_role', 'created_at'), ('claim_id', 'evidence_id')),
    ClaimReviewEventsRow: ('claim_review_events', ('id', 'claim_id', 'decision', 'reviewer', 'notes', 'corrected_text', 'corrected_text_sha256', 'review_metadata_json', 'reviewed_at'), ('id',)),
    SegmentReviewEventsRow: ('segment_review_events', ('id', 'segment_id', 'decision', 'reviewer', 'rationale', 'corrected_text', 'corrected_text_sha256', 'review_metadata_json', 'reviewed_at'), ('id',)),
    DerivationsRow: ('derivations', ('id', 'child_representation_id', 'parent_raw_artifact_id', 'parent_representation_id', 'derivation_method', 'tool_name', 'tool_version', 'parameters_json', 'created_at'), ('id',)),
    EvidenceAssessmentsRow: ('evidence_assessments', ('id', 'assertion_claim_link_id', 'policy_version', 'study_design', 'evidence_directness', 'endpoint_or_response_json', 'study_scope_json', 'methodological_dimensions_json', 'statistical_result_json', 'independence_status', 'limitations_json', 'assessor', 'created_at', 'supersedes_assessment_id'), ('id',)),
    KnowledgeSourcesRow: ('knowledge_sources', ('id', 'source_type', 'canonical_locator', 'title', 'author', 'language', 'description', 'imported_at', 'source_metadata_json', 'logical_identity_sha256', 'created_at'), ('id',)),
    KnowledgeSynthesesRow: ('knowledge_syntheses', ('id', 'assertion_id', 'assertion_revision', 'synthesis_revision', 'policy_version', 'evidence_state', 'support_link_count', 'contradict_link_count', 'independent_support_origin_count', 'independent_contradict_origin_count', 'source_class_distribution_json', 'methodological_diversity_json', 'scope_summary_json', 'uncertainties_json', 'conflicts_json', 'review_status', 'reviewed_by', 'created_at'), ('id',)),
    RawArtifactsRow: ('raw_artifacts', ('id', 'retrieval_id', 'payload_role', 'media_type', 'size_bytes', 'content_sha256', 'artifact_store_key', 'license_id', 'license_evidence_locator', 'materialization_policy', 'immutable', 'created_at'), ('id',)),
    RepresentationsRow: ('representations', ('id', 'source_id', 'origin_raw_artifact_id', 'logical_key', 'representation_kind', 'media_type', 'language', 'content_sha256', 'artifact_store_key', 'materialization_status', 'metadata_json', 'created_at'), ('id',)),
    RetrievalsRow: ('retrievals', ('id', 'acquisition_job_id', 'retrieval_index', 'retrieval_method', 'requested_locator', 'resolved_locator', 'retrieved_at', 'transport_status', 'transport_metadata_json', 'created_at'), ('id',)),
    ScientificAssertionRevisionsRow: ('scientific_assertion_revisions', ('assertion_id', 'revision', 'schema_version', 'assertion_kind', 'predicate', 'participants_json', 'value_json', 'qualifiers_json', 'normalized_text', 'canonical_payload_sha256', 'created_at'), ('assertion_id', 'revision')),
    ScientificAssertionsRow: ('scientific_assertions', ('id', 'created_at', 'retired_at'), ('id',)),
    ScientificEntitiesRow: ('scientific_entities', ('id', 'entity_kind', 'created_at', 'retired_at'), ('id',)),
    ScientificEntityIdentifiersRow: ('scientific_entity_identifiers', ('id', 'entity_id', 'scheme', 'authority_namespace', 'authority_version', 'external_id', 'mapping_status', 'mapping_review_status', 'authority_source_id', 'valid_from', 'valid_to', 'created_at'), ('id',)),
    ScientificEntityNameUsagesRow: ('scientific_entity_name_usages', ('id', 'entity_id', 'source_id', 'verbatim_name', 'language', 'script', 'usage_status', 'nomenclatural_status', 'mapping_review_status', 'source_version', 'retrieval_id', 'segment_id', 'segment_char_start', 'segment_char_end', 'created_at'), ('id',)),
    ScientificEntityRelationsRow: ('scientific_entity_relations', ('id', 'subject_entity_id', 'relation', 'object_entity_id', 'semantics_version', 'qualifiers_json', 'review_status', 'valid_from', 'valid_to', 'created_at'), ('id',)),
    ScientificEntityRevisionsRow: ('scientific_entity_revisions', ('entity_id', 'revision', 'schema_version', 'canonical_label', 'canonical_payload_json', 'canonical_payload_sha256', 'review_status', 'created_at'), ('entity_id', 'revision')),
    SegmentsRow: ('segments', ('id', 'representation_id', 'segment_index', 'text_inline', 'text_sha256', 'materialization_status', 'representation_char_start', 'representation_char_end', 'start_seconds_decimal', 'end_seconds_decimal', 'page_number', 'frame_start', 'frame_end', 'review_status', 'metadata_json', 'created_at'), ('id',)),
    SfSchemaMetadataRow: ('sf_schema_metadata', ('schema_name', 'schema_version', 'design_sha256', 'created_at'), ('schema_name',)),
    SourceAssessmentsRow: ('source_assessments', ('id', 'source_id', 'policy_version', 'source_class', 'peer_review_status', 'publication_status', 'retraction_status', 'license_status', 'institutional_or_publisher_context_json', 'assessment_notes_json', 'assessor', 'created_at', 'supersedes_assessment_id'), ('id',)),
    SourceClaimsRow: ('source_claims', ('id', 'source_id', 'representation_id', 'parent_claim_id', 'claim_layer', 'claim_text', 'claim_text_sha256', 'claim_kind', 'semantic_type', 'qualifiers_json', 'extraction_confidence_decimal', 'source_claim_effective_text_sha256', 'notes', 'initial_review_status', 'created_at'), ('id',)),
    SourceEvidenceRow: ('source_evidence', ('id', 'segment_id', 'segment_char_start', 'segment_char_end', 'evidence_text_sha256', 'start_seconds_decimal', 'end_seconds_decimal', 'page_number', 'frame_start', 'frame_end', 'evidence_metadata_json', 'created_at'), ('id',)),
    SourceLineageEdgesRow: ('source_lineage_edges', ('id', 'parent_source_id', 'child_source_id', 'relation', 'basis_claim_id', 'basis_evidence_json', 'review_status', 'created_at'), ('id',)),
    SemanticProviderRunsRow: ('semantic_provider_runs', ('id', 'run_kind', 'provider_name', 'provider_adapter_name', 'provider_adapter_version', 'endpoint', 'model_requested', 'semantic_contract_name', 'semantic_contract_version', 'semantic_contract_sha256', 'instruction_sha256', 'output_schema_sha256', 'source_request_sha256', 'request_body_sha256', 'request_artifact_store_key', 'request_fingerprint_sha256', 'safe_configuration_json', 'started_at', 'created_at'), ('id',)),
    SemanticProviderRunClaimInputsRow: ('semantic_provider_run_claim_inputs', ('run_id', 'claim_id', 'input_order', 'claim_effective_text_sha256', 'claim_review_status_at_run', 'created_at'), ('run_id', 'claim_id')),
    SemanticProviderRunEvidenceInputsRow: ('semantic_provider_run_evidence_inputs', ('run_id', 'claim_id', 'evidence_id', 'evidence_order', 'evidence_text_sha256', 'segment_review_status_at_run', 'created_at'), ('run_id', 'evidence_id')),
    SemanticProviderRunEventsRow: ('semantic_provider_run_events', ('id', 'run_id', 'event_index', 'event_type', 'model_returned', 'provider_request_id', 'provider_response_id', 'http_status_code', 'response_status', 'content_type', 'response_body_sha256', 'response_artifact_store_key', 'validated_output_sha256', 'validated_output_artifact_store_key', 'usage_json', 'diagnostics_json', 'proposal_count', 'created_at'), ('id',)),
    SemanticCandidatesRow: ('semantic_candidates', ('id', 'schema_version', 'semantic_contract_name', 'semantic_contract_version', 'semantic_contract_sha256', 'relation_type_basis_version', 'relation_type_registry_sha256', 'grounding_policy_sha256', 'claim_scoped_provenance_policy_sha256', 'source_statement_claim_id', 'source_claim_effective_text_sha256', 'semantic_type', 'relation', 'epistemic_class', 'promotion_readiness', 'automatic_scientific_acceptance', 'canonical_candidate_sha256', 'canonical_candidate_document_sha256', 'canonical_candidate_json', 'created_at'), ('id',)),
    SemanticCandidateEntityResolutionEventsRow: ('semantic_candidate_entity_resolution_events', ('id', 'semantic_candidate_id', 'semantic_candidate_sha256', 'role', 'candidate_argument_sha256', 'entity_name_usage_id', 'entity_id', 'entity_revision', 'mapping_status', 'decision', 'reviewer', 'rationale', 'review_policy_name', 'review_policy_version', 'review_policy_sha256', 'reviewed_at'), ('id',)),
    SemanticCandidateEvidenceLinksRow: ('semantic_candidate_evidence_links', ('semantic_candidate_id', 'source_statement_claim_id', 'evidence_id', 'evidence_order', 'created_at'), ('semantic_candidate_id', 'evidence_id')),
    SemanticCandidateReviewEventsRow: ('semantic_candidate_review_events', ('id', 'semantic_candidate_id', 'semantic_candidate_sha256', 'decision', 'reviewer', 'review_text', 'review_text_sha256', 'rationale', 'review_metadata_json', 'review_policy_name', 'review_policy_version', 'review_policy_sha256', 'replacement_candidate_id', 'replacement_candidate_sha256', 'reviewed_at'), ('id',)),
    SemanticProviderCandidateOriginsRow: ('semantic_provider_candidate_origins', ('run_id', 'proposal_index', 'semantic_candidate_id', 'proposal_sha256', 'created_at'), ('run_id', 'proposal_index')),
}

def _comment_only(text: str) -> bool:
    return all(not line.partition("--")[0].strip() for line in text.splitlines())

def split_sql_statements(script: str) -> list[str]:
    statements=[]; buffer=""
    for line in script.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            statement=buffer.strip(); buffer=""
            if statement and not _comment_only(statement):
                statements.append(statement)
    if buffer.strip() and not _comment_only(buffer):
        raise SchemaIdentityError("Incomplete frozen SQL statement")
    return statements

def _bootstrap_connection(path: Path) -> sqlite3.Connection:
    conn=sqlite3.connect(str(path),timeout=5.0,autocommit=True)
    if conn.in_transaction:
        conn.close(); raise SchemaIdentityError("Transaction active before PRAGMAs")
    conn.execute("PRAGMA foreign_keys=ON")
    if conn.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        conn.close(); raise SchemaIdentityError("foreign_keys could not be enabled")
    if conn.execute("PRAGMA journal_mode=DELETE").fetchone()[0].lower() != "delete":
        conn.close(); raise SchemaIdentityError("journal_mode is not DELETE")
    conn.execute("PRAGMA synchronous=FULL")
    if conn.execute("PRAGMA synchronous").fetchone()[0] != 2:
        conn.close(); raise SchemaIdentityError("synchronous is not FULL")
    if conn.in_transaction:
        conn.close(); raise SchemaIdentityError("PRAGMA bootstrap opened transaction")
    conn.autocommit=False
    if not conn.in_transaction:
        conn.close(); raise SchemaIdentityError("PEP249 transaction not active")
    return conn

def _finish(conn: sqlite3.Connection, *, commit: bool) -> None:
    try:
        conn.commit() if commit else conn.rollback()
    finally:
        conn.autocommit=True
        conn.close()

def _schema_sets(conn: sqlite3.Connection) -> tuple[set[str], set[str]]:
    rows=conn.execute(
        "SELECT type,name FROM sqlite_schema "
        "WHERE type IN ('table','index') AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return (
        {name for typ,name in rows if typ=="table"},
        {name for typ,name in rows if typ=="index"},
    )

def validate_schema(conn: sqlite3.Connection) -> None:
    metadata=conn.execute(
        "SELECT schema_name,schema_version,design_sha256 "
        "FROM sf_schema_metadata WHERE schema_name='scientific_foundation'"
    ).fetchone()
    if metadata != ("scientific_foundation",SCHEMA_VERSION,RUNTIME_SCHEMA_DESIGN_SHA256):
        raise SchemaIdentityError(f"Schema metadata mismatch: {metadata!r}")
    if conn.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
        raise SchemaIdentityError("PRAGMA user_version mismatch")
    tables,indexes=_schema_sets(conn)
    if tables != set(EXPECTED_TABLES): raise SchemaIdentityError("Table set mismatch")
    if indexes != set(EXPECTED_INDEXES): raise SchemaIdentityError("Index set mismatch")
    fk=conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk: raise PersistenceIntegrityError(f"foreign_key_check failed: {fk[:20]!r}")
    integrity=[row[0] for row in conn.execute("PRAGMA integrity_check").fetchall()]
    if integrity != ["ok"]: raise PersistenceIntegrityError(f"integrity_check failed: {integrity[:20]!r}")

def initialize_database(
    config: PersistenceConfig,
    *,
    repo_root: Path | None = None,
) -> str:
    config=config.validated(repo_root); path=config.database_path
    if path.exists():
        conn=_bootstrap_connection(path)
        try:
            tables,_=_schema_sets(conn)
            if not tables: raise SchemaIdentityError("Existing empty DB is not adopted")
            validate_schema(conn); return "ALREADY_INITIALIZED_EXACT"
        finally:
            _finish(conn,commit=False)
    path.parent.mkdir(parents=True,exist_ok=True)
    conn=_bootstrap_connection(path)
    try:
        for statement in split_sql_statements(COMPLETE_DDL): conn.execute(statement)
        for statement in split_sql_statements(INDEX_ADDENDUM): conn.execute(statement)
        conn.execute(
            "INSERT INTO sf_schema_metadata(schema_name,schema_version,design_sha256,created_at) VALUES (?,?,?,?)",
            ("scientific_foundation",SCHEMA_VERSION,RUNTIME_SCHEMA_DESIGN_SHA256,datetime.now(UTC).isoformat(timespec="seconds")),
        )
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        validate_schema(conn)
        _finish(conn,commit=True)
    except Exception:
        with suppress(sqlite3.Error):
            _finish(conn, commit=False)
        raise
    verify=_bootstrap_connection(path)
    try: validate_schema(verify)
    finally: _finish(verify,commit=False)
    return "INITIALIZED_NEW"

def backup_database(config: PersistenceConfig, *, repo_root: Path, destination: Path) -> None:
    config=config.validated(repo_root)
    if destination.exists(): raise SchemaIdentityError("Backup destination exists")
    source=sqlite3.connect(str(config.database_path),autocommit=True)
    target=sqlite3.connect(str(destination),autocommit=True)
    try: source.backup(target)
    finally: target.close(); source.close()

def _row_values(row: Any) -> tuple[tuple[str,...], tuple[Any,...]]:
    names=tuple(field.name for field in fields(row))
    return names,tuple(getattr(row,name) for name in names)

def _insert_immutable(conn: sqlite3.Connection, row: object) -> bool:
    spec=_TABLE_SPECS.get(type(row))
    if spec is None: raise TypeError(f"Unsupported row type: {type(row)!r}")
    table,expected_columns,key_fields=spec
    columns,values=_row_values(row)
    if columns != expected_columns: raise PersistenceIntegrityError(f"Row contract mismatch for {table}")
    quoted=", ".join(f'"{name}"' for name in columns); placeholders=", ".join("?" for _ in columns)
    try:
        conn.execute(f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})',values)
        return True
    except sqlite3.IntegrityError as exc:
        if not key_fields: raise PersistenceIntegrityError(f"Integrity error in {table}") from exc
        key_values=tuple(getattr(row,key) for key in key_fields)
        where=" AND ".join(f'"{key}"=?' for key in key_fields)
        existing=conn.execute(f'SELECT {quoted} FROM "{table}" WHERE {where}',key_values).fetchone()
        if existing is not None and tuple(existing)==values: return False
        if existing is not None: raise DuplicateIdentityConflict(f"Immutable identity conflict in {table}: {key_values!r}") from exc
        raise PersistenceIntegrityError(f"Integrity error in {table}") from exc

def _fetch[RowT](conn: sqlite3.Connection, row_type: type[RowT], key_values: tuple[object, ...]) -> RowT | None:
    table,columns,key_fields=_TABLE_SPECS[row_type]
    if len(key_fields)!=len(key_values): raise ValueError("Incorrect key arity")
    quoted=", ".join(f'"{name}"' for name in columns); where=" AND ".join(f'"{key}"=?' for key in key_fields)
    row=conn.execute(f'SELECT {quoted} FROM "{table}" WHERE {where}',key_values).fetchone()
    return None if row is None else row_type(*row)

def _validate_assertion_revision_row(
    row: ScientificAssertionRevisionsRow,
) -> None:
    if row.schema_version != "scientific-assertion-v1.1":
        raise PersistenceIntegrityError(
            "ScientificAssertionRevision schema_version must be scientific-assertion-v1.1"
        )

    try:
        participants = json.loads(row.participants_json)
        value = json.loads(row.value_json)
        qualifiers = json.loads(row.qualifiers_json)
    except json.JSONDecodeError as exc:
        raise PersistenceIntegrityError(
            "ScientificAssertionRevision JSON columns must contain valid JSON"
        ) from exc

    if not isinstance(participants, list):
        raise PersistenceIntegrityError(
            "participants_json must decode to a list"
        )
    if not isinstance(value, dict):
        raise PersistenceIntegrityError(
            "value_json must decode to an object"
        )
    if not isinstance(qualifiers, dict):
        raise PersistenceIntegrityError(
            "qualifiers_json must decode to an object"
        )

    try:
        payload = canonical_assertion_payload(
            assertion_kind=row.assertion_kind,
            predicate=row.predicate,
            participants=participants,
            value=value,
            qualifiers=qualifiers,
        )
    except (TypeError, ValueError) as exc:
        raise PersistenceIntegrityError(
            "ScientificAssertionRevision semantic payload is not canonicalizable"
        ) from exc

    if canonical_json_text(payload["participants"]) != row.participants_json:
        raise PersistenceIntegrityError(
            "participants_json is not in canonical V1.1 form"
        )
    if canonical_json_text(payload["value"]) != row.value_json:
        raise PersistenceIntegrityError(
            "value_json is not in canonical V1.1 form"
        )
    if canonical_json_text(payload["qualifiers"]) != row.qualifiers_json:
        raise PersistenceIntegrityError(
            "qualifiers_json is not in canonical V1.1 form"
        )
    if canonical_sha256(payload) != row.canonical_payload_sha256:
        raise PersistenceIntegrityError(
            "ScientificAssertionRevision canonical_payload_sha256 mismatch"
        )


def _validate_assertion_claim_link_row(row: AssertionClaimLinksRow) -> None:
    fields_and_values = (
        ("stance", row.stance, _STANCE_VALUES),
        ("support_mode", row.support_mode, _SUPPORT_MODE_VALUES),
        ("scope_alignment", row.scope_alignment, _SCOPE_ALIGNMENT_VALUES),
        ("semantic_alignment", row.semantic_alignment, _SEMANTIC_ALIGNMENT_VALUES),
    )
    for field_name, value, allowed in fields_and_values:
        if value not in allowed:
            raise PersistenceIntegrityError(
                f"Unsupported assertion-claim {field_name}: {value!r}"
            )

    if row.stance != "supports":
        return

    if row.scope_alignment == "source_narrower":
        raise ScopeAlignmentError(
            "Support link rejected: source scope is narrower than assertion scope"
        )
    if row.scope_alignment in {"incompatible", "unresolved"}:
        raise ScopeAlignmentError(
            "Support link rejected: source scope is not sufficiently aligned"
        )
    if row.semantic_alignment in {
        "contradictory",
        "insufficient_to_link",
        "unresolved",
    }:
        raise PersistenceIntegrityError(
            "Support link rejected: semantic alignment cannot support the assertion"
        )


class SQLiteProvenanceRepository:
    def __init__(self,conn:sqlite3.Connection,artifact_store:RawArtifactStore)->None:
        self._conn=conn; self._artifact_store=artifact_store
    def add_knowledge_source(self, row: KnowledgeSourcesRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_acquisition_job(self, row: AcquisitionJobsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_retrieval(self, row: RetrievalsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_raw_artifact(self, row: RawArtifactsRow) -> bool:
        self._artifact_store.verify(row.artifact_store_key)
        return _insert_immutable(self._conn, row)

    def add_representation(self, row: RepresentationsRow) -> bool:
        if row.artifact_store_key is not None:
            self._artifact_store.verify(row.artifact_store_key)
        return _insert_immutable(self._conn, row)

    def add_derivation(self, row: DerivationsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_segments(self, rows: tuple[SegmentsRow, ...] | list[SegmentsRow]) -> int:
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def add_source_evidence(self, rows: tuple[SourceEvidenceRow, ...] | list[SourceEvidenceRow]) -> int:
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def add_source_claims(self, rows: tuple[SourceClaimsRow, ...] | list[SourceClaimsRow]) -> int:
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def add_claim_evidence_links(self, rows: tuple[ClaimEvidenceLinksRow, ...] | list[ClaimEvidenceLinksRow]) -> int:
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def record_claim_review_event(self, row: ClaimReviewEventsRow) -> bool:
        if row.decision not in _CLAIM_REVIEW_DECISIONS:
            raise PersistenceIntegrityError(
                f"Invalid claim review decision: {row.decision!r}"
            )
        if row.decision == "correct" and (
            row.corrected_text is None or not row.corrected_text.strip()
        ):
            raise PersistenceIntegrityError(
                "Claim review decision 'correct' requires non-empty corrected_text"
            )
        if (row.corrected_text is None) != (row.corrected_text_sha256 is None):
            raise PersistenceIntegrityError(
                "corrected_text and corrected_text_sha256 must be both null or both present"
            )
        if row.corrected_text is not None:
            actual = hashlib.sha256(row.corrected_text.encode("utf-8")).hexdigest()
            if actual != row.corrected_text_sha256:
                raise PersistenceIntegrityError(
                    "corrected_text_sha256 does not match corrected_text"
                )
        return _insert_immutable(self._conn, row)

    def add_claim_review_events(
        self, rows: tuple[ClaimReviewEventsRow, ...] | list[ClaimReviewEventsRow]
    ) -> int:
        return sum(self.record_claim_review_event(row) for row in rows)

    def get_claim_review_events(
        self, claim_id: str
    ) -> tuple[ClaimReviewEventsRow, ...]:
        table, columns, _ = _TABLE_SPECS[ClaimReviewEventsRow]
        quoted = ", ".join(f'"{name}"' for name in columns)
        rows = self._conn.execute(
            f'SELECT {quoted} FROM "{table}" WHERE claim_id=? '
            "ORDER BY reviewed_at, id",
            (claim_id,),
        ).fetchall()
        return tuple(ClaimReviewEventsRow(*item) for item in rows)

    def record_segment_review_event(self, row: SegmentReviewEventsRow) -> bool:
        if row.decision not in _SEGMENT_REVIEW_DECISIONS:
            raise PersistenceIntegrityError(
                f"Invalid segment review decision: {row.decision!r}"
            )
        if row.decision == "correct" and (
            row.corrected_text is None or not row.corrected_text.strip()
        ):
            raise PersistenceIntegrityError(
                "Segment review decision 'correct' requires non-empty corrected_text"
            )
        if (row.corrected_text is None) != (row.corrected_text_sha256 is None):
            raise PersistenceIntegrityError(
                "corrected_text and corrected_text_sha256 must be both null or both present"
            )
        if row.corrected_text is not None:
            actual = hashlib.sha256(row.corrected_text.encode("utf-8")).hexdigest()
            if actual != row.corrected_text_sha256:
                raise PersistenceIntegrityError(
                    "corrected_text_sha256 does not match corrected_text"
                )

        inserted = _insert_immutable(self._conn, row)
        latest = self._conn.execute(
            "SELECT decision FROM segment_review_events "
            "WHERE segment_id=? ORDER BY reviewed_at DESC, id DESC LIMIT 1",
            (row.segment_id,),
        ).fetchone()
        if latest is None:
            raise PersistenceIntegrityError(
                f"Segment review event vanished after insert: {row.id!r}"
            )
        status = _SEGMENT_REVIEW_STATUS_BY_DECISION[str(latest[0])]
        updated = self._conn.execute(
            "UPDATE segments SET review_status=? WHERE id=?",
            (status, row.segment_id),
        ).rowcount
        if updated != 1:
            raise PersistenceIntegrityError(
                f"Segment review projection target missing: {row.segment_id!r}"
            )
        return inserted

    def add_segment_review_events(
        self, rows: tuple[SegmentReviewEventsRow, ...] | list[SegmentReviewEventsRow]
    ) -> int:
        return sum(self.record_segment_review_event(row) for row in rows)

    def get_segment_review_events(
        self, segment_id: str
    ) -> tuple[SegmentReviewEventsRow, ...]:
        table, columns, _ = _TABLE_SPECS[SegmentReviewEventsRow]
        quoted = ", ".join(f'"{name}"' for name in columns)
        rows = self._conn.execute(
            f'SELECT {quoted} FROM "{table}" WHERE segment_id=? '
            "ORDER BY reviewed_at, id",
            (segment_id,),
        ).fetchall()
        return tuple(SegmentReviewEventsRow(*item) for item in rows)

    def get_source_claim(self,claim_id:str)->SourceClaimsRow|None:
        return _fetch(self._conn,SourceClaimsRow,(claim_id,))

class SQLiteScientificEntityRepository:
    def __init__(self,conn:sqlite3.Connection)->None: self._conn=conn
    def add_entity(self, row: ScientificEntitiesRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_entity_revision(self, row: ScientificEntityRevisionsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_identifier(self, row: ScientificEntityIdentifiersRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_name_usage(self, row: ScientificEntityNameUsagesRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_entity_relation(self, row: ScientificEntityRelationsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_candidate_entity_resolution_event(
        self,
        row: SemanticCandidateEntityResolutionEventsRow,
    ) -> bool:
        _require_lower_sha256(row.semantic_candidate_sha256, "semantic_candidate_sha256")
        _require_lower_sha256(row.candidate_argument_sha256, "candidate_argument_sha256")
        _require_lower_sha256(row.review_policy_sha256, "review_policy_sha256")
        if row.mapping_status not in {"exact", "synonym"}:
            raise PersistenceIntegrityError(
                "Entity resolution mapping_status must be exact/synonym"
            )
        if row.decision not in {"accept", "reject"}:
            raise PersistenceIntegrityError(
                "Entity resolution decision must be accept/reject"
            )
        if not row.role.strip() or not row.reviewer.strip():
            raise PersistenceIntegrityError(
                "Entity resolution requires non-empty role and reviewer"
            )
        if (
            row.review_policy_name != "ecobiome-semantic-candidate-entity-resolution"
            or row.review_policy_version != "1"
            or row.review_policy_sha256
            != "c2e31ae42c25610e4b6c299269bf50f05476b71772d1a0aefe01ff88329e329e"
        ):
            raise PersistenceIntegrityError(
                "Entity resolution review policy identity mismatch"
            )

        candidate = _fetch(
            self._conn,
            SemanticCandidatesRow,
            (row.semantic_candidate_id,),
        )
        if candidate is None:
            raise PersistenceIntegrityError(
                "Entity resolution semantic candidate is missing"
            )
        if candidate.canonical_candidate_sha256 != row.semantic_candidate_sha256:
            raise PersistenceIntegrityError(
                "Entity resolution candidate SHA binding mismatch"
            )
        try:
            payload = json.loads(candidate.canonical_candidate_json)
        except json.JSONDecodeError as exc:
            raise PersistenceIntegrityError(
                "Persisted semantic candidate JSON is invalid"
            ) from exc
        semantic = payload.get("semantic")
        if not isinstance(semantic, dict):
            raise PersistenceIntegrityError(
                "Persisted semantic candidate semantic object is missing"
            )
        raw_arguments = semantic.get("arguments")
        if not isinstance(raw_arguments, list):
            raise PersistenceIntegrityError(
                "Persisted semantic candidate arguments are missing"
            )
        matches = [
            item
            for item in raw_arguments
            if isinstance(item, dict) and item.get("role") == row.role
        ]
        if len(matches) != 1:
            raise PersistenceIntegrityError(
                "Entity resolution role must match exactly one candidate argument"
            )
        argument = matches[0]
        if canonical_sha256(argument) != row.candidate_argument_sha256:
            raise PersistenceIntegrityError(
                "Entity resolution candidate argument SHA mismatch"
            )
        if argument.get("resolution_state") != "grounded_opaque_unresolved":
            raise PersistenceIntegrityError(
                "Entity resolution requires grounded opaque source text"
            )
        value = argument.get("value")
        if not isinstance(value, dict) or value.get("kind") != "source_text":
            raise PersistenceIntegrityError(
                "Entity resolution candidate argument is not source_text"
            )
        source_surface = value.get("source_surface")
        if not isinstance(source_surface, str) or not source_surface:
            raise PersistenceIntegrityError(
                "Entity resolution source_surface is missing"
            )

        name_usage = _fetch(
            self._conn,
            ScientificEntityNameUsagesRow,
            (row.entity_name_usage_id,),
        )
        if name_usage is None:
            raise PersistenceIntegrityError(
                "Entity resolution name usage is missing"
            )
        if name_usage.mapping_review_status != "reviewed_confirmed":
            raise PersistenceIntegrityError(
                "Entity resolution name usage is not human-reviewed"
            )
        if name_usage.entity_id != row.entity_id:
            raise PersistenceIntegrityError(
                "Entity resolution name usage entity does not match event"
            )

        claim = _fetch(
            self._conn,
            SourceClaimsRow,
            (candidate.source_statement_claim_id,),
        )
        if claim is None:
            raise PersistenceIntegrityError(
                "Entity resolution source Claim is missing"
            )
        if name_usage.source_id != claim.source_id:
            raise PersistenceIntegrityError(
                "Entity resolution name usage source does not match source Claim"
            )
        if (
            name_usage.segment_id is None
            or name_usage.segment_char_start is None
            or name_usage.segment_char_end is None
        ):
            raise PersistenceIntegrityError(
                "Entity resolution requires exact segment offsets"
            )
        start = int(name_usage.segment_char_start)
        end = int(name_usage.segment_char_end)
        evidence_spans = self._conn.execute(
            "SELECT se.segment_id,se.segment_char_start,se.segment_char_end "
            "FROM semantic_candidate_evidence_links scel "
            "JOIN source_evidence se ON se.id=scel.evidence_id "
            "WHERE scel.semantic_candidate_id=?",
            (row.semantic_candidate_id,),
        ).fetchall()
        if not any(
            str(segment_id) == name_usage.segment_id
            and int(ev_start) <= start
            and end <= int(ev_end)
            for segment_id, ev_start, ev_end in evidence_spans
        ):
            raise PersistenceIntegrityError(
                "Entity resolution name usage is outside candidate Evidence"
            )

        segment = _fetch(self._conn, SegmentsRow, (name_usage.segment_id,))
        if segment is None or segment.text_inline is None:
            raise PersistenceIntegrityError(
                "Entity resolution segment text is unavailable"
            )
        if hashlib.sha256(segment.text_inline.encode("utf-8")).hexdigest() != segment.text_sha256:
            raise PersistenceIntegrityError(
                "Entity resolution segment text SHA mismatch"
            )
        if start < 0 or end <= start or end > len(segment.text_inline):
            raise PersistenceIntegrityError(
                "Entity resolution name usage offsets are invalid"
            )
        span = segment.text_inline[start:end]
        normalized = {
            unicodedata.normalize("NFC", span),
            unicodedata.normalize("NFC", name_usage.verbatim_name),
            unicodedata.normalize("NFC", source_surface),
        }
        if len(normalized) != 1:
            raise PersistenceIntegrityError(
                "Entity resolution source surface/verbatim span mismatch"
            )

        revision = _fetch(
            self._conn,
            ScientificEntityRevisionsRow,
            (row.entity_id, row.entity_revision),
        )
        if revision is None:
            raise PersistenceIntegrityError(
                "Entity resolution entity revision is missing"
            )
        if revision.review_status != "reviewed_confirmed":
            raise PersistenceIntegrityError(
                "Entity resolution entity revision is not human-reviewed"
            )
        return _insert_immutable(self._conn, row)

    def list_candidate_entity_resolution_events(
        self,
        candidate_id: str,
        role: str | None = None,
    ) -> tuple[SemanticCandidateEntityResolutionEventsRow, ...]:
        table, columns, _ = _TABLE_SPECS[
            SemanticCandidateEntityResolutionEventsRow
        ]
        quoted = ", ".join(f'"{name}"' for name in columns)
        if role is None:
            rows = self._conn.execute(
                f'SELECT {quoted} FROM "{table}" '
                "WHERE semantic_candidate_id=? ORDER BY reviewed_at,id",
                (candidate_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                f'SELECT {quoted} FROM "{table}" '
                "WHERE semantic_candidate_id=? AND role=? ORDER BY reviewed_at,id",
                (candidate_id, role),
            ).fetchall()
        return tuple(
            SemanticCandidateEntityResolutionEventsRow(*item) for item in rows
        )

    def get_name_usage(
        self,
        name_usage_id: str,
    ) -> ScientificEntityNameUsagesRow | None:
        return _fetch(
            self._conn,
            ScientificEntityNameUsagesRow,
            (name_usage_id,),
        )

    def get_entity_revision(self,entity_id:str,revision:int)->ScientificEntityRevisionsRow|None:
        return _fetch(self._conn,ScientificEntityRevisionsRow,(entity_id,revision))

class SQLiteScientificAssertionRepository:
    def __init__(self,conn:sqlite3.Connection)->None: self._conn=conn
    def add_assertion(self, row: ScientificAssertionsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_assertion_revision(self, row: ScientificAssertionRevisionsRow) -> bool:
        _validate_assertion_revision_row(row)
        return _insert_immutable(self._conn, row)

    def add_assertion_claim_link(self, row: AssertionClaimLinksRow) -> bool:
        _validate_assertion_claim_link_row(row)
        return _insert_immutable(self._conn, row)

    def get_assertion_revision(self,assertion_id:str,revision:int)->ScientificAssertionRevisionsRow|None:
        return _fetch(self._conn,ScientificAssertionRevisionsRow,(assertion_id,revision))
    def find_by_canonical_payload_sha256(self,sha256:str)->tuple[ScientificAssertionRevisionsRow,...]:
        row_type=ScientificAssertionRevisionsRow; table,columns,_=_TABLE_SPECS[row_type]
        quoted=", ".join(f'"{name}"' for name in columns)
        rows=self._conn.execute(f'SELECT {quoted} FROM "{table}" WHERE canonical_payload_sha256=? ORDER BY assertion_id,revision',(sha256,)).fetchall()
        return tuple(row_type(*row) for row in rows)

class SQLiteScientificAssessmentRepository:
    def __init__(self,conn:sqlite3.Connection)->None: self._conn=conn
    def add_source_assessment(self, row: SourceAssessmentsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_evidence_assessment(self, row: EvidenceAssessmentsRow) -> bool:
        return _insert_immutable(self._conn, row)

    def add_source_lineage_edge(self, row: SourceLineageEdgesRow) -> bool:
        return _insert_immutable(self._conn, row)


class SQLiteKnowledgeSynthesisRepository:
    def __init__(self,conn:sqlite3.Connection)->None: self._conn=conn
    def add_knowledge_synthesis(self, row: KnowledgeSynthesesRow) -> bool:
        return _insert_immutable(self._conn, row)

    def list_for_assertion(self,assertion_id:str,revision:int)->tuple[KnowledgeSynthesesRow,...]:
        row_type=KnowledgeSynthesesRow; table,columns,_=_TABLE_SPECS[row_type]
        quoted=", ".join(f'"{name}"' for name in columns)
        rows=self._conn.execute(f'SELECT {quoted} FROM "{table}" WHERE assertion_id=? AND assertion_revision=? ORDER BY synthesis_revision',(assertion_id,revision)).fetchall()
        return tuple(row_type(*row) for row in rows)


_PROVIDER_EVENT_TYPES = frozenset({
    "provider_response_received",
    "provider_refusal",
    "transport_failed",
    "provider_failed",
    "output_validation_failed",
    "validated",
    "completed",
    "cancelled",
})
_CANDIDATE_REVIEW_DECISIONS = frozenset({"accept", "correct", "reject"})
_SHA_HEX = frozenset("0123456789abcdef")
_SECRET_KEYS = frozenset({
    "api_key",
    "apikey",
    "authorization",
    "proxy_authorization",
    "password",
    "secret",
    "access_token",
    "refresh_token",
    "bearer_token",
    "cookie",
    "set-cookie",
})
_SECRET_VALUE_PREFIXES = (
    "sk-",
    "ghp_",
    "github_pat_",
    "bearer ",
    "-----begin private key-----",
)


def _require_lower_sha256(value: str | None, label: str) -> str:
    if (
        value is None
        or len(value) != 64
        or any(character not in _SHA_HEX for character in value)
    ):
        raise PersistenceIntegrityError(f"{label} must be lowercase SHA-256")
    return value


def _json_object(text: str, label: str, *, secret_safe: bool = False) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PersistenceIntegrityError(f"{label} must be valid JSON") from exc
    if not isinstance(value, dict):
        raise PersistenceIntegrityError(f"{label} must decode to an object")
    if secret_safe:
        stack: list[object] = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, item in current.items():
                    normalized = str(key).strip().lower().replace("-", "_")
                    if (
                        normalized in _SECRET_KEYS
                        or normalized.endswith(
                            ("_api_key", "_password", "_secret", "_access_token")
                        )
                    ) and item not in (None, "", False):
                        raise PersistenceIntegrityError(
                            f"{label} contains a secret-bearing key: {key}"
                        )
                    stack.append(item)
            elif isinstance(current, list):
                stack.extend(current)
            elif isinstance(current, str):
                lowered = current.strip().lower()
                if any(lowered.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES):
                    raise PersistenceIntegrityError(
                        f"{label} contains a secret-like value"
                    )
    return value


def _current_claim_effective_sha(
    conn: sqlite3.Connection,
    claim_id: str,
) -> tuple[str, str]:
    claim = _fetch(conn, SourceClaimsRow, (claim_id,))
    if claim is None:
        raise PersistenceIntegrityError(f"Unknown source Claim: {claim_id}")
    if hashlib.sha256(claim.claim_text.encode("utf-8")).hexdigest() != claim.claim_text_sha256:
        raise PersistenceIntegrityError("Source Claim text SHA mismatch")
    table, columns, _ = _TABLE_SPECS[ClaimReviewEventsRow]
    quoted = ", ".join(f'"{name}"' for name in columns)
    events = [
        ClaimReviewEventsRow(*row)
        for row in conn.execute(
            f'SELECT {quoted} FROM "{table}" WHERE claim_id=? '
            "ORDER BY reviewed_at, id",
            (claim_id,),
        ).fetchall()
    ]
    if not events:
        raise PersistenceIntegrityError(
            "Semantic candidate source Claim requires human review history"
        )
    latest = events[-1]
    if latest.decision == "reject":
        raise PersistenceIntegrityError(
            "Semantic candidate source Claim latest review is rejected"
        )
    effective = claim.claim_text_sha256
    for event in events:
        if event.decision == "correct":
            corrected = event.corrected_text
            corrected_sha = event.corrected_text_sha256
            if corrected is None or corrected_sha is None:
                raise PersistenceIntegrityError("Malformed Claim correction history")
            actual = hashlib.sha256(corrected.encode("utf-8")).hexdigest()
            if actual != corrected_sha:
                raise PersistenceIntegrityError("Claim correction SHA mismatch")
            effective = corrected_sha
    return effective, latest.decision


class SQLiteSemanticProviderAuditRepository:
    def __init__(
        self,
        conn: sqlite3.Connection,
        artifact_store: RawArtifactStore,
    ) -> None:
        self._conn = conn
        self._artifact_store = artifact_store

    def _verify_artifact(self, key: str, expected_sha: str, label: str) -> None:
        expected = _require_lower_sha256(expected_sha, label)
        stored = self._artifact_store.verify(key)
        if stored.sha256 != expected:
            raise PersistenceIntegrityError(
                f"{label} does not match referenced CAS artifact"
            )

    def add_provider_run(self, row: SemanticProviderRunsRow) -> bool:
        if row.run_kind != "semantic_extraction":
            raise PersistenceIntegrityError("Unsupported provider run_kind")
        for label, value in (
            ("semantic_contract_sha256", row.semantic_contract_sha256),
            ("instruction_sha256", row.instruction_sha256),
            ("output_schema_sha256", row.output_schema_sha256),
            ("source_request_sha256", row.source_request_sha256),
            ("request_body_sha256", row.request_body_sha256),
            ("request_fingerprint_sha256", row.request_fingerprint_sha256),
        ):
            _require_lower_sha256(value, label)
        _json_object(
            row.safe_configuration_json,
            "safe_configuration_json",
            secret_safe=True,
        )
        self._verify_artifact(
            row.request_artifact_store_key,
            row.request_body_sha256,
            "request_body_sha256",
        )
        return _insert_immutable(self._conn, row)

    def add_provider_run_claim_inputs(
        self,
        rows: tuple[SemanticProviderRunClaimInputsRow, ...]
        | list[SemanticProviderRunClaimInputsRow],
    ) -> int:
        for row in rows:
            _require_lower_sha256(
                row.claim_effective_text_sha256,
                "claim_effective_text_sha256",
            )
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def add_provider_run_evidence_inputs(
        self,
        rows: tuple[SemanticProviderRunEvidenceInputsRow, ...]
        | list[SemanticProviderRunEvidenceInputsRow],
    ) -> int:
        for row in rows:
            _require_lower_sha256(
                row.evidence_text_sha256,
                "evidence_text_sha256",
            )
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def add_provider_run_events(
        self,
        rows: tuple[SemanticProviderRunEventsRow, ...]
        | list[SemanticProviderRunEventsRow],
    ) -> int:
        inserted = 0
        for row in rows:
            if row.event_type not in _PROVIDER_EVENT_TYPES:
                raise PersistenceIntegrityError(
                    f"Unsupported provider event_type: {row.event_type!r}"
                )
            _json_object(row.usage_json, "usage_json")
            _json_object(row.diagnostics_json, "diagnostics_json", secret_safe=True)
            if (row.response_body_sha256 is None) != (
                row.response_artifact_store_key is None
            ):
                raise PersistenceIntegrityError(
                    "response SHA/CAS key must be both null or both present"
                )
            if (row.validated_output_sha256 is None) != (
                row.validated_output_artifact_store_key is None
            ):
                raise PersistenceIntegrityError(
                    "validated-output SHA/CAS key must be both null or both present"
                )
            if row.response_body_sha256 is not None:
                self._verify_artifact(
                    str(row.response_artifact_store_key),
                    row.response_body_sha256,
                    "response_body_sha256",
                )
            if row.validated_output_sha256 is not None:
                self._verify_artifact(
                    str(row.validated_output_artifact_store_key),
                    row.validated_output_sha256,
                    "validated_output_sha256",
                )
            inserted += int(_insert_immutable(self._conn, row))
        return inserted

    def list_provider_run_events(
        self,
        run_id: str,
    ) -> tuple[SemanticProviderRunEventsRow, ...]:
        table, columns, _ = _TABLE_SPECS[SemanticProviderRunEventsRow]
        quoted = ", ".join(f'"{name}"' for name in columns)
        rows = self._conn.execute(
            f'SELECT {quoted} FROM "{table}" WHERE run_id=? '
            "ORDER BY event_index, id",
            (run_id,),
        ).fetchall()
        return tuple(SemanticProviderRunEventsRow(*row) for row in rows)

    def add_provider_candidate_origins(
        self,
        rows: tuple[SemanticProviderCandidateOriginsRow, ...]
        | list[SemanticProviderCandidateOriginsRow],
    ) -> int:
        inserted = 0
        for row in rows:
            _require_lower_sha256(row.proposal_sha256, "proposal_sha256")
            validated = self._conn.execute(
                "SELECT 1 FROM semantic_provider_run_events "
                "WHERE run_id=? AND event_type='validated' LIMIT 1",
                (row.run_id,),
            ).fetchone()
            if validated is None:
                raise PersistenceIntegrityError(
                    "Provider candidate origin requires validated provider output"
                )
            inserted += int(_insert_immutable(self._conn, row))
        return inserted


class SQLiteSemanticCandidateRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def _validate_candidate_row(
        self,
        row: SemanticCandidatesRow,
    ) -> dict[str, Any]:
        _require_lower_sha256(
            row.canonical_candidate_sha256,
            "canonical_candidate_sha256",
        )
        _require_lower_sha256(
            row.canonical_candidate_document_sha256,
            "canonical_candidate_document_sha256",
        )
        actual_document_sha = hashlib.sha256(
            row.canonical_candidate_json.encode("utf-8")
        ).hexdigest()
        if actual_document_sha != row.canonical_candidate_document_sha256:
            raise PersistenceIntegrityError(
                "Candidate document SHA does not match canonical JSON bytes"
            )
        payload = _json_object(
            row.canonical_candidate_json,
            "canonical_candidate_json",
        )
        if canonical_json_text(payload) != row.canonical_candidate_json:
            raise PersistenceIntegrityError(
                "canonical_candidate_json is not canonical JSON"
            )
        contract = payload.get("contract")
        source = payload.get("source")
        semantic = payload.get("semantic")
        if not isinstance(contract, dict) or not isinstance(source, dict) or not isinstance(semantic, dict):
            raise PersistenceIntegrityError(
                "Candidate JSON lacks contract/source/semantic objects"
            )
        expected_scalars = {
            "schema_version": payload.get("schema_version"),
            "semantic_contract_name": contract.get("name"),
            "semantic_contract_version": contract.get("version"),
            "semantic_contract_sha256": contract.get("canonical_sha256"),
            "relation_type_basis_version": contract.get("relation_type_basis_version"),
            "relation_type_registry_sha256": contract.get("relation_type_registry_sha256"),
            "grounding_policy_sha256": contract.get("grounding_policy_sha256"),
            "claim_scoped_provenance_policy_sha256": contract.get(
                "claim_scoped_provenance_policy_sha256"
            ),
            "source_statement_claim_id": source.get("source_statement_claim_id"),
            "source_claim_effective_text_sha256": source.get(
                "source_claim_effective_text_sha256"
            ),
            "semantic_type": semantic.get("semantic_type"),
            "relation": semantic.get("relation"),
            "epistemic_class": semantic.get("epistemic_class"),
            "promotion_readiness": payload.get("promotion_readiness"),
            "canonical_candidate_sha256": payload.get(
                "canonical_candidate_sha256"
            ),
        }
        for field_name, expected in expected_scalars.items():
            if getattr(row, field_name) != expected:
                raise PersistenceIntegrityError(
                    f"Candidate scalar/JSON mismatch: {field_name}"
                )
        if payload.get("automatic_scientific_acceptance") is not False:
            raise PersistenceIntegrityError(
                "Candidate JSON must deny automatic scientific acceptance"
            )
        if row.automatic_scientific_acceptance != 0:
            raise PersistenceIntegrityError(
                "Persisted candidate must deny automatic scientific acceptance"
            )
        for field_name in (
            "semantic_contract_sha256",
            "relation_type_registry_sha256",
            "grounding_policy_sha256",
            "claim_scoped_provenance_policy_sha256",
            "source_claim_effective_text_sha256",
        ):
            _require_lower_sha256(getattr(row, field_name), field_name)
        current_sha, _ = _current_claim_effective_sha(
            self._conn,
            row.source_statement_claim_id,
        )
        if current_sha != row.source_claim_effective_text_sha256:
            raise PersistenceIntegrityError(
                "Semantic candidate is stale against current source Claim"
            )
        return payload

    def get_candidate(
        self,
        candidate_id: str,
    ) -> SemanticCandidatesRow | None:
        return _fetch(self._conn, SemanticCandidatesRow, (candidate_id,))

    def get_candidate_evidence_links(
        self,
        candidate_id: str,
    ) -> tuple[SemanticCandidateEvidenceLinksRow, ...]:
        table, columns, _ = _TABLE_SPECS[SemanticCandidateEvidenceLinksRow]
        quoted = ", ".join(f'"{name}"' for name in columns)
        rows = self._conn.execute(
            f'SELECT {quoted} FROM "{table}" WHERE semantic_candidate_id=? '
            "ORDER BY evidence_order, evidence_id",
            (candidate_id,),
        ).fetchall()
        return tuple(SemanticCandidateEvidenceLinksRow(*row) for row in rows)

    def find_by_canonical_candidate_sha256(
        self,
        sha256: str,
    ) -> SemanticCandidatesRow | None:
        _require_lower_sha256(sha256, "canonical candidate lookup SHA")
        table, columns, _ = _TABLE_SPECS[SemanticCandidatesRow]
        quoted = ", ".join(f'"{name}"' for name in columns)
        row = self._conn.execute(
            f'SELECT {quoted} FROM "{table}" '
            "WHERE canonical_candidate_sha256=?",
            (sha256,),
        ).fetchone()
        return None if row is None else SemanticCandidatesRow(*row)

    def _validate_evidence_links(
        self,
        row: SemanticCandidatesRow,
        payload: dict[str, Any],
        evidence_links: tuple[SemanticCandidateEvidenceLinksRow, ...]
        | list[SemanticCandidateEvidenceLinksRow],
    ) -> tuple[SemanticCandidateEvidenceLinksRow, ...]:
        source = payload["source"]
        expected_ids = source.get("evidence_ids")
        if (
            not isinstance(expected_ids, list)
            or not expected_ids
            or expected_ids != sorted(set(expected_ids))
        ):
            raise PersistenceIntegrityError(
                "Candidate Evidence IDs must be sorted and unique"
            )
        ordered = tuple(sorted(evidence_links, key=lambda item: item.evidence_order))
        if [link.evidence_order for link in ordered] != list(range(len(ordered))):
            raise PersistenceIntegrityError(
                "Candidate Evidence ordering must be contiguous from zero"
            )
        if [link.evidence_id for link in ordered] != expected_ids:
            raise PersistenceIntegrityError(
                "Candidate Evidence links do not exactly match candidate JSON"
            )
        for link in ordered:
            if link.semantic_candidate_id != row.id:
                raise PersistenceIntegrityError(
                    "Candidate Evidence link candidate ID mismatch"
                )
            if link.source_statement_claim_id != row.source_statement_claim_id:
                raise PersistenceIntegrityError(
                    "Candidate Evidence link source Claim mismatch"
                )
            ownership = self._conn.execute(
                "SELECT 1 FROM claim_evidence_links "
                "WHERE claim_id=? AND evidence_id=?",
                (link.source_statement_claim_id, link.evidence_id),
            ).fetchone()
            if ownership is None:
                raise PersistenceIntegrityError(
                    "Candidate Evidence is not owned by source Claim"
                )
        return ordered

    def add_candidate(
        self,
        row: SemanticCandidatesRow,
        evidence_links: tuple[SemanticCandidateEvidenceLinksRow, ...]
        | list[SemanticCandidateEvidenceLinksRow],
    ) -> tuple[SemanticCandidatesRow, bool]:
        payload = self._validate_candidate_row(row)
        ordered = self._validate_evidence_links(row, payload, evidence_links)
        existing = self.find_by_canonical_candidate_sha256(
            row.canonical_candidate_sha256
        )
        if existing is not None:
            existing_links = self.get_candidate_evidence_links(existing.id)
            normalized_requested = tuple(
                (
                    item.source_statement_claim_id,
                    item.evidence_id,
                    item.evidence_order,
                )
                for item in ordered
            )
            normalized_existing = tuple(
                (
                    item.source_statement_claim_id,
                    item.evidence_id,
                    item.evidence_order,
                )
                for item in existing_links
            )
            comparable_fields = (
                "schema_version",
                "semantic_contract_name",
                "semantic_contract_version",
                "semantic_contract_sha256",
                "relation_type_basis_version",
                "relation_type_registry_sha256",
                "grounding_policy_sha256",
                "claim_scoped_provenance_policy_sha256",
                "source_statement_claim_id",
                "source_claim_effective_text_sha256",
                "semantic_type",
                "relation",
                "epistemic_class",
                "promotion_readiness",
                "automatic_scientific_acceptance",
                "canonical_candidate_sha256",
                "canonical_candidate_document_sha256",
                "canonical_candidate_json",
            )
            if (
                any(
                    getattr(existing, field) != getattr(row, field)
                    for field in comparable_fields
                )
                or normalized_existing != normalized_requested
            ):
                raise DuplicateIdentityConflict(
                    "Canonical semantic candidate identity conflicts with "
                    "persisted row/link identity"
                )
            return existing, False

        savepoint = f"candidate_{hashlib.sha256(row.id.encode()).hexdigest()[:16]}"
        self._conn.execute(f"SAVEPOINT {savepoint}")
        try:
            _insert_immutable(self._conn, row)
            for link in ordered:
                _insert_immutable(self._conn, link)
            self._conn.execute(f"RELEASE SAVEPOINT {savepoint}")
        except Exception:
            self._conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            self._conn.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise
        return row, True

    def add_candidate_evidence_links(
        self,
        rows: tuple[SemanticCandidateEvidenceLinksRow, ...]
        | list[SemanticCandidateEvidenceLinksRow],
    ) -> int:
        return sum(_insert_immutable(self._conn, row) for row in rows)

    def _correction_reaches(
        self,
        start_candidate_id: str,
        target_candidate_id: str,
    ) -> bool:
        stack = [start_candidate_id]
        seen: set[str] = set()
        while stack:
            current = stack.pop()
            if current == target_candidate_id:
                return True
            if current in seen:
                continue
            seen.add(current)
            rows = self._conn.execute(
                "SELECT replacement_candidate_id "
                "FROM semantic_candidate_review_events "
                "WHERE semantic_candidate_id=? AND decision='correct' "
                "AND replacement_candidate_id IS NOT NULL",
                (current,),
            ).fetchall()
            stack.extend(str(row[0]) for row in rows)
        return False

    def add_review_event(
        self,
        row: SemanticCandidateReviewEventsRow,
    ) -> bool:
        if row.decision not in _CANDIDATE_REVIEW_DECISIONS:
            raise PersistenceIntegrityError(
                f"Invalid semantic candidate review decision: {row.decision!r}"
            )
        if not row.reviewer.strip() or not row.review_text.strip():
            raise PersistenceIntegrityError(
                "Candidate review requires reviewer and review_text"
            )
        if hashlib.sha256(row.review_text.encode("utf-8")).hexdigest() != (
            row.review_text_sha256
        ):
            raise PersistenceIntegrityError("Candidate review text SHA mismatch")
        _require_lower_sha256(
            row.semantic_candidate_sha256,
            "semantic_candidate_sha256",
        )
        _require_lower_sha256(row.review_policy_sha256, "review_policy_sha256")
        if (
            row.review_policy_name != "ecobiome-semantic-candidate-human-review"
            or row.review_policy_version != "1"
            or row.review_policy_sha256
            != "cb68231ccb26d398ce3c42c9cae33c8470325390b8e3c524f9d9a1b5a1bc8f61"
        ):
            raise PersistenceIntegrityError(
                "Candidate review policy identity is not the frozen V1 contract"
            )
        _json_object(row.review_metadata_json, "review_metadata_json", secret_safe=True)

        candidate = self.get_candidate(row.semantic_candidate_id)
        if candidate is None:
            raise PersistenceIntegrityError("Reviewed semantic candidate is missing")
        if candidate.canonical_candidate_sha256 != row.semantic_candidate_sha256:
            raise PersistenceIntegrityError("Candidate review SHA binding mismatch")

        if row.decision == "correct":
            if row.replacement_candidate_id is None or row.replacement_candidate_sha256 is None:
                raise PersistenceIntegrityError(
                    "Candidate correction requires replacement candidate"
                )
            if row.replacement_candidate_id == row.semantic_candidate_id:
                raise PersistenceIntegrityError(
                    "Candidate correction cannot self-replace"
                )
            replacement = self.get_candidate(row.replacement_candidate_id)
            if replacement is None:
                raise PersistenceIntegrityError("Replacement candidate is missing")
            if replacement.canonical_candidate_sha256 != row.replacement_candidate_sha256:
                raise PersistenceIntegrityError("Replacement candidate SHA mismatch")
            if replacement.source_statement_claim_id != candidate.source_statement_claim_id:
                raise PersistenceIntegrityError(
                    "Candidate correction replacement must retain source Claim"
                )
            if self._correction_reaches(
                replacement.id,
                candidate.id,
            ):
                raise PersistenceIntegrityError(
                    "Candidate correction lineage cycle is forbidden"
                )
        elif (
            row.replacement_candidate_id is not None
            or row.replacement_candidate_sha256 is not None
        ):
            raise PersistenceIntegrityError(
                "accept/reject candidate reviews cannot carry replacement"
            )
        return _insert_immutable(self._conn, row)

    def list_review_events(
        self,
        candidate_id: str,
    ) -> tuple[SemanticCandidateReviewEventsRow, ...]:
        table, columns, _ = _TABLE_SPECS[SemanticCandidateReviewEventsRow]
        quoted = ", ".join(f'"{name}"' for name in columns)
        rows = self._conn.execute(
            f'SELECT {quoted} FROM "{table}" WHERE semantic_candidate_id=? '
            "ORDER BY reviewed_at, id",
            (candidate_id,),
        ).fetchall()
        return tuple(SemanticCandidateReviewEventsRow(*row) for row in rows)

class SQLiteScientificFoundationUnitOfWork:
    def __init__(self,config:PersistenceConfig,*,repo_root:Path,artifact_store:RawArtifactStore)->None:
        self._config=config.validated(repo_root); self._artifact_store=artifact_store; self._conn:sqlite3.Connection|None=None
    @property
    def artifact_store(self)->RawArtifactStore: return self._artifact_store
    def __enter__(self) -> Self:
        if self._conn is not None: raise RuntimeError("UnitOfWork already active")
        self._conn=_bootstrap_connection(self._config.database_path); validate_schema(self._conn)
        self.provenance=SQLiteProvenanceRepository(self._conn,self._artifact_store)
        self.entities=SQLiteScientificEntityRepository(self._conn)
        self.assertions=SQLiteScientificAssertionRepository(self._conn)
        self.assessments=SQLiteScientificAssessmentRepository(self._conn)
        self.syntheses=SQLiteKnowledgeSynthesisRepository(self._conn)
        self.provider_audit=SQLiteSemanticProviderAuditRepository(
            self._conn, self._artifact_store
        )
        self.semantic_candidates=SQLiteSemanticCandidateRepository(
            self._conn
        )
        return self
    def __exit__(self,exc_type:object,exc:object,tb:object)->None:
        if self._conn is None: return
        self._conn.rollback(); self._conn.autocommit=True; self._conn.close(); self._conn=None
    def commit(self)->None:
        if self._conn is None: raise RuntimeError("UnitOfWork not active")
        self._conn.commit()
    def rollback(self)->None:
        if self._conn is None: raise RuntimeError("UnitOfWork not active")
        self._conn.rollback()
    def verify_artifact_reference(self,key:str)->None: self._artifact_store.verify(key)
