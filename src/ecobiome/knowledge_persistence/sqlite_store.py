"""SQLite Scientific Foundation adapter candidate."""
from __future__ import annotations

import hashlib
import json
import sqlite3
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

def initialize_database(config: PersistenceConfig, *, repo_root: Path) -> str:
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
