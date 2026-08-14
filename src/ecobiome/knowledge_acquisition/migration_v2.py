"""Forward-only Collector schema v1 -> v2 migration with verified backup."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from ecobiome.knowledge_acquisition.collector_schema import (
    SCHEMA_VERSION,
    create_schema_v2,
    validate_schema_v2,
)

LEGACY_TABLES = (
    "schema_migrations",
    "sources",
    "documents",
    "passages",
    "claims",
    "evidence",
    "collection_jobs",
    "review_decisions",
)


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Describe one schema initialization/migration result."""

    schema_version: int
    migrated: bool
    backup_directory: Path | None


def _utc_now_text() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _cas_relpath(sha256: str) -> str:
    return f"raw/{sha256[:2]}/{sha256}"


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=30.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


def _schema_version(connection: sqlite3.Connection) -> int:
    exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'schema_migrations'
        """
    ).fetchone()
    if exists is None:
        return 0
    row = connection.execute(
        "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
    ).fetchone()
    return int(row["version"])


def _directory_manifest(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)).replace("\\", "/"): _sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _backup_sqlite(source: Path, destination: Path) -> None:
    source_connection = sqlite3.connect(source, timeout=30.0)
    destination_connection = sqlite3.connect(destination)
    try:
        source_connection.backup(destination_connection)
        destination_connection.commit()
    finally:
        destination_connection.close()
        source_connection.close()


def _create_verified_backup(
    *,
    database_path: Path,
    legacy_document_directory: Path,
    artifact_directory: Path,
    backup_root: Path,
) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_directory = backup_root / f"collector-v1-backup-{stamp}-{uuid4().hex[:8]}"
    backup_directory.mkdir(parents=True, exist_ok=False)

    database_backup = backup_directory / database_path.name
    _backup_sqlite(database_path, database_backup)

    legacy_backup = backup_directory / "legacy-documents"
    if legacy_document_directory.exists():
        shutil.copytree(legacy_document_directory, legacy_backup)

    artifact_backup = backup_directory / "artifacts-before-migration"
    if artifact_directory.exists():
        shutil.copytree(artifact_directory, artifact_backup)

    manifest = {
        "database": {
            "source": str(database_path),
            "backup": str(database_backup),
            "sha256": _sha256_file(database_backup),
        },
        "legacy_documents": _directory_manifest(legacy_backup),
        "artifacts_before_migration": _directory_manifest(artifact_backup),
    }
    manifest_path = backup_directory / "BACKUP_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with sqlite3.connect(database_backup) as connection:
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity.lower() != "ok":
        raise RuntimeError(f"Collector backup integrity check failed: {integrity}")

    return backup_directory



def _replace_with_retry(
    source: Path,
    destination: Path,
    *,
    attempts: int = 20,
    delay_seconds: float = 0.1,
) -> None:
    """Replace a file with bounded retries for transient Windows locks."""
    last_error: PermissionError | None = None
    for attempt in range(attempts):
        try:
            os.replace(source, destination)
            return
        except PermissionError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _unlink_with_retry(
    path: Path,
    *,
    attempts: int = 20,
    delay_seconds: float = 0.1,
) -> None:
    """Delete a file with bounded retries for transient Windows locks."""
    last_error: PermissionError | None = None
    for attempt in range(attempts):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _restore_sqlite_backup(
    *,
    database_backup: Path,
    database_path: Path,
) -> None:
    """Restore SQLite contents without replacing the database file.

    Windows may keep an otherwise idle SQLite file handle open in another
    process or connection.  Unlink/replace based rollback is therefore too
    fragile.  SQLite's backup API performs a page-level restore through the
    database locking protocol and does not require deleting the target file.
    """
    source = sqlite3.connect(database_backup, timeout=30.0)
    destination = sqlite3.connect(database_path, timeout=30.0)
    try:
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()

    verification = _connect(database_path)
    try:
        integrity = str(
            verification.execute("PRAGMA integrity_check").fetchone()[0]
        )
        if integrity.lower() != "ok":
            raise RuntimeError(
                "Collector rollback integrity check failed: "
                f"{integrity}"
            )
        if _schema_version(verification) != 1:
            raise RuntimeError(
                "Collector rollback did not restore schema version 1."
            )
    finally:
        verification.close()


def _restore_backup(
    *,
    database_path: Path,
    legacy_document_directory: Path,
    artifact_directory: Path,
    backup_directory: Path,
) -> None:
    database_backup = backup_directory / database_path.name
    if not database_backup.is_file():
        raise RuntimeError("Collector rollback database backup is missing.")

    _restore_sqlite_backup(
        database_backup=database_backup,
        database_path=database_path,
    )

    # Journal sidecars are never authoritative rollback sources.  Remove them
    # after all rollback connections are closed; transient Windows locks get
    # bounded retries.  The main database file itself is deliberately kept.
    for suffix in ("-wal", "-shm"):
        target = Path(str(database_path) + suffix)
        if target.exists():
            _unlink_with_retry(target)

    if legacy_document_directory.exists():
        shutil.rmtree(legacy_document_directory)
    legacy_backup = backup_directory / "legacy-documents"
    if legacy_backup.exists():
        shutil.copytree(legacy_backup, legacy_document_directory)

    if artifact_directory.exists():
        shutil.rmtree(artifact_directory)
    artifact_backup = backup_directory / "artifacts-before-migration"
    if artifact_backup.exists():
        shutil.copytree(artifact_backup, artifact_directory)


def _store_cas_copy(
    source_path: Path,
    artifact_directory: Path,
    expected_sha256: str,
) -> str:
    relpath = _cas_relpath(expected_sha256)
    destination = artifact_directory / relpath
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        if _sha256_file(destination) != expected_sha256:
            raise RuntimeError(
                f"Collector CAS checksum mismatch: {destination}"
            )
        return relpath

    temporary = destination.with_name(
        f"{destination.name}.{uuid4().hex}.tmp"
    )
    try:
        with (
            source_path.open("rb") as source_stream,
            temporary.open("xb") as destination_stream,
        ):
            shutil.copyfileobj(
                source_stream,
                destination_stream,
                length=1024 * 1024,
            )
            destination_stream.flush()
            os.fsync(destination_stream.fileno())

        if _sha256_file(temporary) != expected_sha256:
            raise RuntimeError(
                "Collector migration source bytes changed during CAS copy."
            )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    return relpath


def migration_plan_v1(
    database_path: str | Path,
) -> dict[str, int]:
    """Return a no-write migration plan for a schema-v1 Collector database."""
    path = Path(database_path).expanduser().resolve()
    connection = _connect(path)
    try:
        if _schema_version(connection) != 1:
            raise RuntimeError("Migration plan requires Collector schema v1.")
        counts = {
            table: int(
                connection.execute(
                    f"SELECT COUNT(*) AS count FROM {table}"
                ).fetchone()["count"]
            )
            for table in LEGACY_TABLES
            if table != "schema_migrations"
        }
    finally:
        connection.close()
    return counts


def _migrate_v1_rows(
    connection: sqlite3.Connection,
    *,
    artifact_directory: Path,
) -> None:
    for table in LEGACY_TABLES:
        connection.execute(
            f"ALTER TABLE {table} RENAME TO legacy_{table}"
        )

    create_schema_v2(connection)

    old_versions = connection.execute(
        """
        SELECT version, applied_at
        FROM legacy_schema_migrations
        ORDER BY version
        """
    ).fetchall()
    for row in old_versions:
        connection.execute(
            """
            INSERT INTO schema_migrations(
                version, applied_at, description
            )
            VALUES (?, ?, ?)
            """,
            (
                int(row["version"]),
                str(row["applied_at"]),
                "Collector schema v1 (migrated history)",
            ),
        )

    source_rows = connection.execute(
        "SELECT * FROM legacy_sources ORDER BY id"
    ).fetchall()
    for row in source_rows:
        source_metadata = {
            "legacy_description": str(row["description"]),
            "legacy_review_status": str(row["review_status"]),
        }
        connection.execute(
            """
            INSERT INTO sources(
                id,
                source_type,
                canonical_locator,
                title,
                author,
                language,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["id"]),
                str(row["source_type"]),
                str(row["locator"]),
                str(row["title"]),
                str(row["author"]),
                str(row["language"]),
                json.dumps(source_metadata, sort_keys=True),
                str(row["imported_at"]),
            ),
        )

    legacy_jobs = connection.execute(
        "SELECT * FROM legacy_collection_jobs ORDER BY started_at, id"
    ).fetchall()
    for row in legacy_jobs:
        raw_status = str(row["status"])
        status = (
            raw_status
            if raw_status in {"running", "succeeded", "failed"}
            else "failed"
        )
        connection.execute(
            """
            INSERT INTO acquisition_jobs(
                id,
                source_id,
                job_kind,
                requested_locator,
                adapter_name,
                adapter_version,
                status,
                started_at,
                completed_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["id"]),
                row["source_id"],
                "legacy_transcript_import",
                str(row["source_locator"]),
                "ecobiome-collector-v1",
                "1",
                status,
                str(row["started_at"]),
                row["completed_at"],
                str(row["started_at"]),
            ),
        )
        if row["error"]:
            connection.execute(
                """
                INSERT INTO job_diagnostics(
                    id,
                    acquisition_job_id,
                    severity,
                    code,
                    message,
                    details_json,
                    created_at
                )
                VALUES (?, ?, 'error', 'legacy_error', ?, '{}', ?)
                """,
                (
                    str(uuid4()),
                    str(row["id"]),
                    str(row["error"]),
                    str(row["completed_at"] or row["started_at"]),
                ),
            )

    documents = connection.execute(
        """
        SELECT
            d.*,
            s.locator AS source_locator,
            s.language AS source_language
        FROM legacy_documents AS d
        JOIN legacy_sources AS s ON s.id = d.source_id
        ORDER BY d.id
        """
    ).fetchall()

    raw_ids: dict[str, str] = {}
    for row in documents:
        source_path = Path(str(row["storage_path"]))
        if not source_path.is_file():
            raise RuntimeError(
                f"Collector v1 raw document is missing: {source_path}"
            )

        document_sha = str(row["sha256"])
        if _sha256_file(source_path) != document_sha:
            raise RuntimeError(
                f"Collector v1 raw checksum mismatch: {source_path}"
            )
        relpath = _store_cas_copy(
            source_path,
            artifact_directory,
            document_sha,
        )

        raw_id = raw_ids.get(document_sha)
        if raw_id is None:
            existing = connection.execute(
                "SELECT id FROM raw_artifacts WHERE sha256 = ?",
                (document_sha,),
            ).fetchone()
            raw_id = str(existing["id"]) if existing else str(uuid4())
            raw_ids[document_sha] = raw_id
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO raw_artifacts(
                        id,
                        sha256,
                        size_bytes,
                        media_type,
                        storage_relpath,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        raw_id,
                        document_sha,
                        source_path.stat().st_size,
                        str(row["mime_type"]),
                        relpath,
                        str(row["imported_at"]),
                    ),
                )

        job_row = connection.execute(
            """
            SELECT id
            FROM legacy_collection_jobs
            WHERE document_id = ?
            ORDER BY started_at, id
            LIMIT 1
            """,
            (str(row["id"]),),
        ).fetchone()
        if job_row is None:
            job_id = str(uuid4())
            connection.execute(
                """
                INSERT INTO acquisition_jobs(
                    id,
                    source_id,
                    job_kind,
                    requested_locator,
                    adapter_name,
                    adapter_version,
                    status,
                    started_at,
                    completed_at,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'succeeded', ?, ?, ?)
                """,
                (
                    job_id,
                    str(row["source_id"]),
                    "legacy_transcript_import",
                    str(row["source_locator"]),
                    "ecobiome-v1-migration",
                    "1",
                    str(row["imported_at"]),
                    str(row["imported_at"]),
                    str(row["imported_at"]),
                ),
            )
        else:
            job_id = str(job_row["id"])

        connection.execute(
            """
            INSERT INTO retrievals(
                id,
                acquisition_job_id,
                source_id,
                raw_artifact_id,
                original_locator,
                canonical_locator,
                protocol,
                retrieved_at,
                http_status,
                etag,
                last_modified,
                request_metadata_json,
                response_metadata_json,
                adapter_name,
                adapter_version
            )
            VALUES (?, ?, ?, ?, ?, ?, 'legacy_import', ?, NULL, NULL,
                    NULL, '{}', '{}', 'ecobiome-collector-v1', '1')
            """,
            (
                str(uuid4()),
                job_id,
                str(row["source_id"]),
                raw_id,
                str(row["original_path"]),
                str(row["source_locator"]),
                str(row["imported_at"]),
            ),
        )

        representation_metadata = {
            "legacy_document_id": str(row["id"]),
            "legacy_original_path": str(row["original_path"]),
            "legacy_character_count": int(row["character_count"]),
        }
        connection.execute(
            """
            INSERT INTO representations(
                id,
                source_id,
                representation_kind,
                media_type,
                language,
                content_sha256,
                content_size_bytes,
                storage_relpath,
                metadata_json,
                created_at
            )
            VALUES (?, ?, 'transcript', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["id"]),
                str(row["source_id"]),
                str(row["mime_type"]),
                str(row["source_language"]),
                document_sha,
                source_path.stat().st_size,
                relpath,
                json.dumps(representation_metadata, sort_keys=True),
                str(row["imported_at"]),
            ),
        )
        connection.execute(
            """
            INSERT INTO representation_derivations(
                id,
                child_representation_id,
                parent_raw_artifact_id,
                parent_representation_id,
                method,
                tool_name,
                tool_version,
                parameters_json,
                created_at
            )
            VALUES (?, ?, ?, NULL, 'legacy_import_identity',
                    'ecobiome-v1-migration', '1', '{}', ?)
            """,
            (
                str(uuid4()),
                str(row["id"]),
                raw_id,
                str(row["imported_at"]),
            ),
        )

    passages = connection.execute(
        """
        SELECT *
        FROM legacy_passages
        ORDER BY document_id, passage_index
        """
    ).fetchall()
    for row in passages:
        connection.execute(
            """
            INSERT INTO segments(
                id,
                representation_id,
                segment_index,
                text,
                text_sha256,
                start_char,
                end_char,
                start_seconds,
                end_seconds,
                page_number,
                frame_start,
                frame_end,
                review_status,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL,
                    NULL, NULL, ?, '{"migrated_from":"passages"}', ?)
            """,
            (
                str(row["id"]),
                str(row["document_id"]),
                int(row["passage_index"]),
                str(row["text"]),
                str(row["sha256"]),
                str(row["review_status"]),
                str(row["created_at"]),
            ),
        )

    claims = connection.execute(
        "SELECT * FROM legacy_claims ORDER BY id"
    ).fetchall()
    for row in claims:
        claim_metadata: dict[str, object] = {
            "legacy_source_id": str(row["source_id"]),
            "legacy_document_id": str(row["document_id"]),
            "legacy_passage_id": (
                None if row["passage_id"] is None else str(row["passage_id"])
            ),
            "legacy_passage_index": row["passage_index"],
            "legacy_confidence": float(row["confidence"]),
        }
        connection.execute(
            """
            INSERT INTO claims(
                id,
                claim_kind,
                text,
                review_status,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["id"]),
                str(row["kind"]),
                str(row["claim_text"]),
                str(row["review_status"]),
                json.dumps(claim_metadata, sort_keys=True),
                str(row["created_at"]),
            ),
        )

    evidence_rows = connection.execute(
        """
        SELECT e.*, p.text AS passage_text
        FROM legacy_evidence AS e
        JOIN legacy_passages AS p ON p.id = e.passage_id
        ORDER BY e.id
        """
    ).fetchall()
    for row in evidence_rows:
        start = row["start_character"]
        end = row["end_character"]
        passage_text = str(row["passage_text"])
        evidence_text = str(row["evidence_text"])
        if (start is None) != (end is None):
            raise RuntimeError(
                f"Legacy evidence {row['id']} has a partial char anchor."
            )
        if start is not None:
            start_int = int(start)
            end_int = int(end)
            if end_int > len(passage_text):
                raise RuntimeError(
                    f"Legacy evidence {row['id']} exceeds passage bounds."
                )
            if passage_text[start_int:end_int] != evidence_text:
                raise RuntimeError(
                    f"Legacy evidence {row['id']} anchor text mismatch."
                )

        connection.execute(
            """
            INSERT INTO evidence(
                id,
                claim_id,
                segment_id,
                evidence_text,
                evidence_sha256,
                segment_char_start,
                segment_char_end,
                start_seconds,
                end_seconds,
                page_number,
                frame_start,
                frame_end,
                metadata_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL,
                    '{"migrated_from":"evidence_v1"}', ?)
            """,
            (
                str(row["id"]),
                str(row["claim_id"]),
                str(row["passage_id"]),
                evidence_text,
                _sha256_bytes(evidence_text.encode("utf-8")),
                start,
                end,
                row["start_seconds"],
                row["end_seconds"],
                str(row["created_at"]),
            ),
        )

    reviews = connection.execute(
        """
        SELECT *
        FROM legacy_review_decisions
        ORDER BY created_at, id
        """
    ).fetchall()
    for row in reviews:
        target_type = str(row["target_type"])
        segment_id = str(row["target_id"]) if target_type == "passage" else None
        claim_id = str(row["target_id"]) if target_type == "claim" else None
        if target_type not in {"passage", "claim"}:
            raise RuntimeError(
                f"Unknown legacy review target: {target_type}"
            )
        if str(row["decision"]) == "correct" and not str(
            row["corrected_text"] or ""
        ).strip():
            raise RuntimeError(
                f"Legacy correction {row['id']} has no corrected_text."
            )
        connection.execute(
            """
            INSERT INTO review_decisions(
                id,
                segment_id,
                claim_id,
                decision,
                reviewer,
                rationale,
                corrected_text,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["id"]),
                segment_id,
                claim_id,
                str(row["decision"]),
                str(row["reviewer"]),
                str(row["rationale"]),
                row["corrected_text"],
                str(row["created_at"]),
            ),
        )

    for table in (
        "legacy_evidence",
        "legacy_review_decisions",
        "legacy_claims",
        "legacy_passages",
        "legacy_collection_jobs",
        "legacy_documents",
        "legacy_sources",
        "legacy_schema_migrations",
    ):
        connection.execute(f"DROP TABLE {table}")

    connection.execute(
        """
        INSERT INTO schema_migrations(
            version, applied_at, description
        )
        VALUES (?, ?, ?)
        """,
        (
            SCHEMA_VERSION,
            _utc_now_text(),
            "Collector acquisition architecture v2",
        ),
    )
    validate_schema_v2(connection)


def initialize_or_migrate(
    *,
    database_path: str | Path,
    legacy_document_directory: str | Path,
    artifact_directory: str | Path,
    backup_root: str | Path | None = None,
    failure_injection: str | None = None,
) -> MigrationResult:
    """Initialize v2 or safely migrate one existing v1 Collector database."""
    database = Path(database_path).expanduser().resolve()
    legacy_documents = Path(legacy_document_directory).expanduser().resolve()
    artifacts = Path(artifact_directory).expanduser().resolve()
    backup_base = (
        Path(backup_root).expanduser().resolve()
        if backup_root is not None
        else database.with_name(f"{database.stem}.backups")
    )

    database.parent.mkdir(parents=True, exist_ok=True)

    if not database.exists():
        connection = _connect(database)
        try:
            connection.execute("BEGIN IMMEDIATE")
            create_schema_v2(connection)
            connection.execute(
                """
                INSERT INTO schema_migrations(
                    version, applied_at, description
                )
                VALUES (?, ?, ?)
                """,
                (
                    SCHEMA_VERSION,
                    _utc_now_text(),
                    "Collector acquisition architecture v2",
                ),
            )
            validate_schema_v2(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return MigrationResult(
            schema_version=SCHEMA_VERSION,
            migrated=False,
            backup_directory=None,
        )

    inspection = _connect(database)
    try:
        current = _schema_version(inspection)
    finally:
        inspection.close()

    if current == SCHEMA_VERSION:
        connection = _connect(database)
        try:
            validate_schema_v2(connection)
        finally:
            connection.close()
        return MigrationResult(
            schema_version=SCHEMA_VERSION,
            migrated=False,
            backup_directory=None,
        )

    if current != 1:
        raise RuntimeError(
            "Collector database schema is unsupported by this build: "
            f"{current}."
        )

    backup_directory = _create_verified_backup(
        database_path=database,
        legacy_document_directory=legacy_documents,
        artifact_directory=artifacts,
        backup_root=backup_base,
    )

    connection = _connect(database)
    try:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN IMMEDIATE")
        _migrate_v1_rows(
            connection,
            artifact_directory=artifacts,
        )
        if failure_injection == "after_sql":
            raise RuntimeError("Injected Collector migration failure.")
        connection.commit()
    except Exception:
        connection.rollback()
        connection.close()
        _restore_backup(
            database_path=database,
            legacy_document_directory=legacy_documents,
            artifact_directory=artifacts,
            backup_directory=backup_directory,
        )
        raise
    else:
        connection.close()

    verification = _connect(database)
    try:
        validate_schema_v2(verification)
    except Exception:
        verification.close()
        _restore_backup(
            database_path=database,
            legacy_document_directory=legacy_documents,
            artifact_directory=artifacts,
            backup_directory=backup_directory,
        )
        raise
    else:
        verification.close()

    return MigrationResult(
        schema_version=SCHEMA_VERSION,
        migrated=True,
        backup_directory=backup_directory,
    )
