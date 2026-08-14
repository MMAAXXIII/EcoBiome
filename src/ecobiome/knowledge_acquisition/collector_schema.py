"""Collector schema v2 definitions and invariant validators."""

from __future__ import annotations

import hashlib
import sqlite3
from collections import defaultdict

SCHEMA_VERSION = 2

VALID_REVIEW_STATUSES = frozenset(
    {"pending", "accepted", "corrected", "rejected"}
)
VALID_JOB_STATUSES = frozenset(
    {"queued", "running", "succeeded", "partial", "failed", "cancelled"}
)

_V2_STATEMENTS = (
    """
    CREATE TABLE schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE sources (
        id TEXT PRIMARY KEY,
        source_type TEXT NOT NULL,
        canonical_locator TEXT NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        language TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(source_type, canonical_locator)
    )
    """,
    """
    CREATE TABLE acquisition_jobs (
        id TEXT PRIMARY KEY,
        source_id TEXT REFERENCES sources(id),
        job_kind TEXT NOT NULL,
        requested_locator TEXT NOT NULL,
        adapter_name TEXT,
        adapter_version TEXT,
        status TEXT NOT NULL CHECK(
            status IN (
                'queued',
                'running',
                'succeeded',
                'partial',
                'failed',
                'cancelled'
            )
        ),
        started_at TEXT,
        completed_at TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE job_diagnostics (
        id TEXT PRIMARY KEY,
        acquisition_job_id TEXT NOT NULL
            REFERENCES acquisition_jobs(id) ON DELETE CASCADE,
        severity TEXT NOT NULL CHECK(
            severity IN ('info', 'warning', 'error')
        ),
        code TEXT NOT NULL,
        message TEXT,
        details_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE raw_artifacts (
        id TEXT PRIMARY KEY,
        sha256 TEXT NOT NULL UNIQUE,
        size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
        media_type TEXT NOT NULL,
        storage_relpath TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE retrievals (
        id TEXT PRIMARY KEY,
        acquisition_job_id TEXT NOT NULL
            REFERENCES acquisition_jobs(id),
        source_id TEXT NOT NULL REFERENCES sources(id),
        raw_artifact_id TEXT NOT NULL REFERENCES raw_artifacts(id),
        original_locator TEXT NOT NULL,
        canonical_locator TEXT NOT NULL,
        protocol TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        http_status INTEGER,
        etag TEXT,
        last_modified TEXT,
        request_metadata_json TEXT NOT NULL DEFAULT '{}',
        response_metadata_json TEXT NOT NULL DEFAULT '{}',
        adapter_name TEXT NOT NULL,
        adapter_version TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE representations (
        id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL REFERENCES sources(id),
        representation_kind TEXT NOT NULL,
        media_type TEXT NOT NULL,
        language TEXT,
        content_sha256 TEXT NOT NULL,
        content_size_bytes INTEGER NOT NULL CHECK(content_size_bytes >= 0),
        storage_relpath TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(
            source_id,
            representation_kind,
            content_sha256
        )
    )
    """,
    """
    CREATE TABLE representation_derivations (
        id TEXT PRIMARY KEY,
        child_representation_id TEXT NOT NULL
            REFERENCES representations(id) ON DELETE CASCADE,
        parent_raw_artifact_id TEXT REFERENCES raw_artifacts(id),
        parent_representation_id TEXT REFERENCES representations(id),
        method TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        tool_version TEXT NOT NULL,
        parameters_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        CHECK(
            (
                parent_raw_artifact_id IS NOT NULL
                AND parent_representation_id IS NULL
            )
            OR
            (
                parent_raw_artifact_id IS NULL
                AND parent_representation_id IS NOT NULL
            )
        ),
        CHECK(
            parent_representation_id IS NULL
            OR parent_representation_id <> child_representation_id
        )
    )
    """,
    """
    CREATE TABLE segments (
        id TEXT PRIMARY KEY,
        representation_id TEXT NOT NULL
            REFERENCES representations(id) ON DELETE CASCADE,
        segment_index INTEGER NOT NULL CHECK(segment_index >= 1),
        text TEXT,
        text_sha256 TEXT,
        start_char INTEGER,
        end_char INTEGER,
        start_seconds REAL,
        end_seconds REAL,
        page_number INTEGER,
        frame_start INTEGER,
        frame_end INTEGER,
        review_status TEXT NOT NULL DEFAULT 'pending'
            CHECK(
                review_status IN (
                    'pending',
                    'accepted',
                    'corrected',
                    'rejected'
                )
            ),
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(representation_id, segment_index),
        CHECK(
            (start_char IS NULL AND end_char IS NULL)
            OR (
                start_char IS NOT NULL
                AND end_char IS NOT NULL
                AND start_char >= 0
                AND end_char >= start_char
            )
        ),
        CHECK(
            (start_seconds IS NULL AND end_seconds IS NULL)
            OR (
                start_seconds IS NOT NULL
                AND end_seconds IS NOT NULL
                AND start_seconds >= 0
                AND end_seconds >= start_seconds
            )
        ),
        CHECK(page_number IS NULL OR page_number >= 1),
        CHECK(
            (frame_start IS NULL AND frame_end IS NULL)
            OR (
                frame_start IS NOT NULL
                AND frame_end IS NOT NULL
                AND frame_start >= 0
                AND frame_end >= frame_start
            )
        ),
        CHECK(
            (text IS NULL AND text_sha256 IS NULL)
            OR (text IS NOT NULL AND text_sha256 IS NOT NULL)
        )
    )
    """,
    """
    CREATE TABLE claims (
        id TEXT PRIMARY KEY,
        claim_kind TEXT NOT NULL,
        text TEXT NOT NULL,
        review_status TEXT NOT NULL DEFAULT 'pending'
            CHECK(
                review_status IN (
                    'pending',
                    'accepted',
                    'corrected',
                    'rejected'
                )
            ),
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE evidence (
        id TEXT PRIMARY KEY,
        claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
        segment_id TEXT NOT NULL REFERENCES segments(id),
        evidence_text TEXT NOT NULL,
        evidence_sha256 TEXT NOT NULL,
        segment_char_start INTEGER,
        segment_char_end INTEGER,
        start_seconds REAL,
        end_seconds REAL,
        page_number INTEGER,
        frame_start INTEGER,
        frame_end INTEGER,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        CHECK(
            (segment_char_start IS NULL AND segment_char_end IS NULL)
            OR (
                segment_char_start IS NOT NULL
                AND segment_char_end IS NOT NULL
                AND segment_char_start >= 0
                AND segment_char_end >= segment_char_start
            )
        ),
        CHECK(
            (start_seconds IS NULL AND end_seconds IS NULL)
            OR (
                start_seconds IS NOT NULL
                AND end_seconds IS NOT NULL
                AND start_seconds >= 0
                AND end_seconds >= start_seconds
            )
        ),
        CHECK(page_number IS NULL OR page_number >= 1),
        CHECK(
            (frame_start IS NULL AND frame_end IS NULL)
            OR (
                frame_start IS NOT NULL
                AND frame_end IS NOT NULL
                AND frame_start >= 0
                AND frame_end >= frame_start
            )
        )
    )
    """,
    """
    CREATE TABLE review_decisions (
        id TEXT PRIMARY KEY,
        segment_id TEXT REFERENCES segments(id),
        claim_id TEXT REFERENCES claims(id),
        decision TEXT NOT NULL CHECK(
            decision IN ('accept', 'correct', 'reject')
        ),
        reviewer TEXT NOT NULL,
        rationale TEXT NOT NULL,
        corrected_text TEXT,
        created_at TEXT NOT NULL,
        CHECK(
            (segment_id IS NOT NULL AND claim_id IS NULL)
            OR (segment_id IS NULL AND claim_id IS NOT NULL)
        ),
        CHECK(
            decision <> 'correct'
            OR corrected_text IS NOT NULL
        )
    )
    """,
    "CREATE INDEX idx_jobs_source ON acquisition_jobs(source_id)",
    "CREATE INDEX idx_jobs_status ON acquisition_jobs(status)",
    """
    CREATE INDEX idx_job_diagnostics_job
        ON job_diagnostics(acquisition_job_id)
    """,
    """
    CREATE INDEX idx_retrievals_source_time
        ON retrievals(source_id, retrieved_at)
    """,
    "CREATE INDEX idx_retrievals_artifact ON retrievals(raw_artifact_id)",
    """
    CREATE INDEX idx_retrievals_locator
        ON retrievals(canonical_locator, retrieved_at)
    """,
    "CREATE INDEX idx_representations_source ON representations(source_id)",
    """
    CREATE INDEX idx_derivations_child
        ON representation_derivations(child_representation_id)
    """,
    """
    CREATE INDEX idx_derivations_parent_raw
        ON representation_derivations(parent_raw_artifact_id)
    """,
    """
    CREATE INDEX idx_derivations_parent_representation
        ON representation_derivations(parent_representation_id)
    """,
    """
    CREATE INDEX idx_segments_representation
        ON segments(representation_id, segment_index)
    """,
    "CREATE INDEX idx_segments_review ON segments(review_status)",
    "CREATE INDEX idx_claims_review ON claims(review_status)",
    "CREATE INDEX idx_evidence_claim ON evidence(claim_id)",
    "CREATE INDEX idx_evidence_segment ON evidence(segment_id)",
    "CREATE INDEX idx_review_segment ON review_decisions(segment_id)",
    "CREATE INDEX idx_review_claim ON review_decisions(claim_id)",
)


def create_schema_v2(connection: sqlite3.Connection) -> None:
    """Create schema v2 without using executescript implicit commits."""
    for statement in _V2_STATEMENTS:
        connection.execute(statement)


def _table_exists(
    connection: sqlite3.Connection,
    table: str,
) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_schema WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _uses_v4_provenance(connection: sqlite3.Connection) -> bool:
    return _table_exists(connection, "sf_schema_metadata")


def validate_derivation_graph(connection: sqlite3.Connection) -> None:
    """Reject representation-to-representation derivation cycles."""
    representation_ids = {
        str(row[0])
        for row in connection.execute("SELECT id FROM representations")
    }
    parents: dict[str, set[str]] = defaultdict(set)
    if _uses_v4_provenance(connection):
        derivation_rows = connection.execute(
            """
            SELECT child_representation_id, parent_representation_id
            FROM derivations
            WHERE parent_representation_id IS NOT NULL
            """
        )
    else:
        derivation_rows = connection.execute(
            """
            SELECT child_representation_id, parent_representation_id
            FROM representation_derivations
            WHERE parent_representation_id IS NOT NULL
            """
        )

    for child, parent in derivation_rows:
        parents[str(child)].add(str(parent))

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise RuntimeError(
                f"Representation derivation cycle detected at {node}."
            )
        if node in visited:
            return
        visiting.add(node)
        for parent in parents.get(node, set()):
            if parent not in representation_ids:
                raise RuntimeError(
                    f"Unknown parent representation in derivation: {parent}."
                )
            visit(parent)
        visiting.remove(node)
        visited.add(node)

    for representation_id in representation_ids:
        visit(representation_id)


def validate_evidence_anchors(connection: sqlite3.Connection) -> None:
    """Validate evidence anchors against enclosing segment boundaries."""
    v4 = _uses_v4_provenance(connection)
    if v4:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.evidence_text_sha256,
                e.segment_char_start,
                e.segment_char_end,
                e.start_seconds_decimal,
                e.end_seconds_decimal,
                e.page_number,
                e.frame_start,
                e.frame_end,
                s.text_inline,
                s.start_seconds_decimal,
                s.end_seconds_decimal,
                s.page_number,
                s.frame_start,
                s.frame_end
            FROM source_evidence AS e
            JOIN segments AS s ON s.id = e.segment_id
            """
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT
                e.id,
                e.evidence_text,
                e.segment_char_start,
                e.segment_char_end,
                e.start_seconds,
                e.end_seconds,
                e.page_number,
                e.frame_start,
                e.frame_end,
                s.text,
                s.start_seconds,
                s.end_seconds,
                s.page_number,
                s.frame_start,
                s.frame_end
            FROM evidence AS e
            JOIN segments AS s ON s.id = e.segment_id
            """
        ).fetchall()

    for row in rows:
        (
            evidence_id,
            evidence_reference,
            char_start,
            char_end,
            start_seconds,
            end_seconds,
            page_number,
            frame_start,
            frame_end,
            segment_text,
            segment_start,
            segment_end,
            segment_page,
            segment_frame_start,
            segment_frame_end,
        ) = row

        if char_start is not None:
            if segment_text is None:
                raise RuntimeError(
                    f"Evidence {evidence_id} has a char anchor without text."
                )
            start = int(char_start)
            end = int(char_end)
            text = str(segment_text)
            if end > len(text):
                raise RuntimeError(
                    f"Evidence {evidence_id} char anchor exceeds segment."
                )
            anchored_text = text[start:end]
            if v4:
                anchored_sha256 = hashlib.sha256(
                    anchored_text.encode("utf-8")
                ).hexdigest()
                if anchored_sha256 != str(evidence_reference):
                    raise RuntimeError(
                        f"Evidence {evidence_id} text does not match char anchor."
                    )
            elif anchored_text != str(evidence_reference):
                raise RuntimeError(
                    f"Evidence {evidence_id} text does not match char anchor."
                )

        if start_seconds is not None and segment_start is not None:
            if float(start_seconds) < float(segment_start):
                raise RuntimeError(
                    f"Evidence {evidence_id} starts before segment time."
                )
            if float(end_seconds) > float(segment_end):
                raise RuntimeError(
                    f"Evidence {evidence_id} ends after segment time."
                )

        if (
            page_number is not None
            and segment_page is not None
            and int(page_number) != int(segment_page)
        ):
            raise RuntimeError(
                f"Evidence {evidence_id} page differs from segment page."
            )

        if frame_start is not None and segment_frame_start is not None:
            if int(frame_start) < int(segment_frame_start):
                raise RuntimeError(
                    f"Evidence {evidence_id} starts before segment frame."
                )
            if int(frame_end) > int(segment_frame_end):
                raise RuntimeError(
                    f"Evidence {evidence_id} ends after segment frame."
                )


def validate_schema_v2(connection: sqlite3.Connection) -> None:
    """Run cross-row schema invariants not expressible as CHECK constraints."""
    foreign_key_errors = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
    if foreign_key_errors:
        raise RuntimeError(
            f"Collector foreign-key validation failed: {foreign_key_errors}"
        )
    validate_derivation_graph(connection)
    validate_evidence_anchors(connection)
