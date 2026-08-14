"""Tests for Collector v1 -> v2 migration, backup, and rollback."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

from ecobiome.knowledge_acquisition.collector_schema import SCHEMA_VERSION
from ecobiome.knowledge_acquisition.migration_v2 import (
    initialize_or_migrate,
    migration_plan_v1,
)

V1_DDL = """
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    locator TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    language TEXT NOT NULL,
    description TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    review_status TEXT NOT NULL,
    UNIQUE(source_type, locator)
);
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    sha256 TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    original_path TEXT NOT NULL,
    character_count INTEGER NOT NULL CHECK(character_count >= 0),
    mime_type TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(source_id, sha256)
);
CREATE TABLE passages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    passage_index INTEGER NOT NULL CHECK(passage_index >= 1),
    text TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    review_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(document_id, passage_index)
);
CREATE TABLE claims (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    passage_id TEXT REFERENCES passages(id),
    passage_index INTEGER,
    claim_text TEXT NOT NULL,
    kind TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    review_status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    passage_id TEXT NOT NULL REFERENCES passages(id),
    evidence_text TEXT NOT NULL,
    start_character INTEGER,
    end_character INTEGER,
    start_seconds REAL,
    end_seconds REAL,
    created_at TEXT NOT NULL
);
CREATE TABLE collection_jobs (
    id TEXT PRIMARY KEY,
    source_locator TEXT NOT NULL,
    source_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    source_id TEXT REFERENCES sources(id),
    document_id TEXT REFERENCES documents(id),
    error TEXT
);
CREATE TABLE review_decisions (
    id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    corrected_text TEXT,
    reviewer TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _create_v1_fixture(
    tmp_path: Path,
) -> tuple[Path, Path, dict[str, str]]:
    database = tmp_path / "collector.sqlite3"
    documents = tmp_path / "collector.documents"
    documents.mkdir()

    source_id = str(uuid4())
    document_id = str(uuid4())
    passage_id = str(uuid4())
    claim_id = str(uuid4())
    evidence_id = str(uuid4())
    job_id = str(uuid4())
    passage_review_id = str(uuid4())
    claim_review_id = str(uuid4())

    passage = "Water temperature remained stable at 24 C."
    raw = (passage + "\n").encode("utf-8")
    document_sha = _sha256(raw)
    raw_path = documents / f"{document_sha}.txt"
    raw_path.write_bytes(raw)

    evidence_text = "24 C"
    start = passage.index(evidence_text)
    end = start + len(evidence_text)
    created = "2026-08-11T10:00:00+00:00"

    with sqlite3.connect(database) as connection:
        connection.executescript(V1_DDL)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, ?)",
            (created,),
        )
        connection.execute(
            """
            INSERT INTO sources
            VALUES (?, 'transcript', 'local:v1-fixture',
                    'Fixture', 'EcoBiome', 'en',
                    'Migration fixture', ?, 'pending')
            """,
            (source_id, created),
        )
        connection.execute(
            """
            INSERT INTO documents
            VALUES (?, ?, ?, ?, 'fixture.txt', ?, 'text/plain', ?)
            """,
            (
                document_id,
                source_id,
                document_sha,
                str(raw_path),
                len(passage) + 1,
                created,
            ),
        )
        connection.execute(
            """
            INSERT INTO passages
            VALUES (?, ?, 1, ?, ?, 'accepted', ?)
            """,
            (
                passage_id,
                document_id,
                passage,
                _sha256(passage.encode("utf-8")),
                created,
            ),
        )
        connection.execute(
            """
            INSERT INTO claims
            VALUES (?, ?, ?, ?, 1, ?, 'observation',
                    0.87, 'corrected', ?)
            """,
            (
                claim_id,
                source_id,
                document_id,
                passage_id,
                "Water temperature was 24 C.",
                created,
            ),
        )
        connection.execute(
            """
            INSERT INTO evidence
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?)
            """,
            (
                evidence_id,
                claim_id,
                passage_id,
                evidence_text,
                start,
                end,
                created,
            ),
        )
        connection.execute(
            """
            INSERT INTO collection_jobs
            VALUES (?, 'local:v1-fixture', 'transcript', 'succeeded',
                    ?, ?, ?, ?, NULL)
            """,
            (
                job_id,
                created,
                created,
                source_id,
                document_id,
            ),
        )
        connection.execute(
            """
            INSERT INTO review_decisions
            VALUES (?, 'passage', ?, 'accept', NULL,
                    'reviewer', 'Accepted fixture.', ?)
            """,
            (passage_review_id, passage_id, created),
        )
        connection.execute(
            """
            INSERT INTO review_decisions
            VALUES (?, 'claim', ?, 'correct', ?,
                    'reviewer', 'Clarified wording.', ?)
            """,
            (
                claim_review_id,
                claim_id,
                "Water temperature was approximately 24 C.",
                created,
            ),
        )

    ids = {
        "source": source_id,
        "document": document_id,
        "passage": passage_id,
        "claim": claim_id,
        "evidence": evidence_id,
        "job": job_id,
        "passage_review": passage_review_id,
        "claim_review": claim_review_id,
        "raw_sha": document_sha,
    }
    return database, documents, ids


def _schema_version(database: Path) -> int:
    with sqlite3.connect(database) as connection:
        return int(
            connection.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()[0]
        )


def test_migration_plan_is_read_only_and_migration_preserves_ids(
    tmp_path: Path,
) -> None:
    database, documents, ids = _create_v1_fixture(tmp_path)
    before_raw = next(documents.iterdir()).read_bytes()

    plan = migration_plan_v1(database)

    assert plan["sources"] == 1
    assert plan["documents"] == 1
    assert plan["passages"] == 1
    assert _schema_version(database) == 1
    assert next(documents.iterdir()).read_bytes() == before_raw

    artifacts = tmp_path / "collector.artifacts"
    backups = tmp_path / "collector.backups"
    result = initialize_or_migrate(
        database_path=database,
        legacy_document_directory=documents,
        artifact_directory=artifacts,
        backup_root=backups,
    )

    assert result.migrated is True
    assert result.schema_version == SCHEMA_VERSION
    assert result.backup_directory is not None
    assert (result.backup_directory / "BACKUP_MANIFEST.json").is_file()
    assert _schema_version(database) == 2

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT id FROM sources"
        ).fetchone()[0] == ids["source"]
        assert connection.execute(
            "SELECT id FROM representations"
        ).fetchone()[0] == ids["document"]
        assert connection.execute(
            "SELECT id FROM segments"
        ).fetchone()[0] == ids["passage"]
        assert connection.execute(
            "SELECT id FROM claims"
        ).fetchone()[0] == ids["claim"]
        assert connection.execute(
            "SELECT id FROM evidence"
        ).fetchone()[0] == ids["evidence"]
        assert connection.execute(
            "SELECT id FROM acquisition_jobs"
        ).fetchone()[0] == ids["job"]

        corrected = connection.execute(
            """
            SELECT corrected_text
            FROM review_decisions
            WHERE claim_id = ?
            """,
            (ids["claim"],),
        ).fetchone()[0]
        assert corrected == "Water temperature was approximately 24 C."

        raw_row = connection.execute(
            "SELECT sha256, storage_relpath FROM raw_artifacts"
        ).fetchone()

    assert raw_row[0] == ids["raw_sha"]
    cas_path = artifacts / raw_row[1]
    assert cas_path.read_bytes() == before_raw

    second = initialize_or_migrate(
        database_path=database,
        legacy_document_directory=documents,
        artifact_directory=artifacts,
        backup_root=backups,
    )
    assert second.migrated is False
    assert second.schema_version == 2


def test_failed_migration_restores_v1_database_and_artifacts(
    tmp_path: Path,
) -> None:
    database, documents, _ids = _create_v1_fixture(tmp_path)
    artifacts = tmp_path / "collector.artifacts"
    artifacts.mkdir()
    preexisting = artifacts / "keep.txt"
    preexisting.write_text("preexisting", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Injected Collector migration"):
        initialize_or_migrate(
            database_path=database,
            legacy_document_directory=documents,
            artifact_directory=artifacts,
            backup_root=tmp_path / "backups",
            failure_injection="after_sql",
        )

    assert _schema_version(database) == 1
    assert preexisting.read_text(encoding="utf-8") == "preexisting"
    assert len(list(documents.glob("*.txt"))) == 1

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM review_decisions"
        ).fetchone()[0] == 2


def test_failed_migration_restores_with_live_idle_reader_connection(
    tmp_path: Path,
) -> None:
    """Rollback must not depend on unlinking the SQLite database file."""
    database, documents, _ids = _create_v1_fixture(tmp_path)
    artifacts = tmp_path / "collector.artifacts"
    artifacts.mkdir()
    preexisting = artifacts / "keep.txt"
    preexisting.write_text("preexisting", encoding="utf-8")

    live_reader = sqlite3.connect(database)
    try:
        assert live_reader.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0] == 1

        with pytest.raises(RuntimeError, match="Injected Collector migration"):
            initialize_or_migrate(
                database_path=database,
                legacy_document_directory=documents,
                artifact_directory=artifacts,
                backup_root=tmp_path / "backups",
                failure_injection="after_sql",
            )
    finally:
        live_reader.close()

    assert _schema_version(database) == 1
    assert preexisting.read_text(encoding="utf-8") == "preexisting"
    assert len(list(documents.glob("*.txt"))) == 1

    connection = sqlite3.connect(database)
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM review_decisions"
        ).fetchone()[0] == 2
    finally:
        connection.close()
