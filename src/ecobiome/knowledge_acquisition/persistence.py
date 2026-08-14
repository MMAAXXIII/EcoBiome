"""Durable scientific acquisition storage for EcoBiome Collector v2."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionDiagnostic,
    AcquisitionResult,
    SegmentDraft,
)
from ecobiome.knowledge_acquisition.claim_candidates import (
    ClaimSegment,
    build_source_statement_candidates,
)
from ecobiome.knowledge_acquisition.collector_schema import (
    SCHEMA_VERSION,
    validate_evidence_anchors,
)
from ecobiome.knowledge_acquisition.migration_v2 import (
    MigrationResult,
    initialize_or_migrate,
)
from ecobiome.knowledge_acquisition.processing import split_into_passages
from ecobiome.knowledge_acquisition.semantic_claims import AtomicClaimBatch
from ecobiome.knowledge_acquisition.transcript import ImportedTranscript
from ecobiome.knowledge_persistence.collector_compat import (
    AcquisitionReceipt as _AcquisitionReceiptCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    ClaimProposalReceipt as _ClaimProposalReceiptCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    CollectorStore as _CollectorStoreCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    ImportReceipt as _ImportReceiptCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    PersistedAtomicClaimReceipt as _PersistedAtomicClaimReceiptCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    PersistedClaimReceipt as _PersistedClaimReceiptCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    PersistedPayloadReceipt as _PersistedPayloadReceiptCompatibilityFacade,
)
from ecobiome.knowledge_persistence.collector_compat import (
    PersistedRepresentationReceipt as _PersistedRepresentationReceiptCompatibilityFacade,
)

VALID_REVIEW_TARGETS = frozenset({"passage", "claim"})
VALID_REVIEW_DECISIONS = frozenset({"accept", "correct", "reject"})


def _utc_now_text() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _text(value: object | None) -> str:
    return "" if value is None else str(value)


def _cas_relpath(sha256: str) -> str:
    return f"raw/{sha256[:2]}/{sha256}"


@dataclass(frozen=True, slots=True)
class LegacyImportReceipt:
    """Identify one durable transcript-ingestion result.

    The historical document/passage names remain API-compatible while v2
    persists them as Representation/Segment records.
    """

    job_id: UUID
    source_id: UUID
    document_id: UUID
    document_sha256: str
    stored_document_path: Path
    passage_ids: tuple[UUID, ...]
    passage_review_statuses: tuple[str, ...]
    duplicate_document: bool


@dataclass(frozen=True, slots=True)
class LegacyPersistedPayloadReceipt:
    """Identify one persisted exact raw payload."""

    logical_key: str
    raw_artifact_id: UUID
    sha256: str
    stored_path: Path


@dataclass(frozen=True, slots=True)
class LegacyPersistedRepresentationReceipt:
    """Identify one persisted derived representation and its review segments."""

    logical_key: str
    representation_id: UUID
    sha256: str
    stored_path: Path
    segment_ids: tuple[UUID, ...]
    segment_review_statuses: tuple[str, ...]
    duplicate: bool


@dataclass(frozen=True, slots=True)
class LegacyAcquisitionReceipt:
    """Identify one source-agnostic acquisition persistence result."""

    job_id: UUID
    source_id: UUID
    payloads: tuple[PersistedPayloadReceipt, ...]
    representations: tuple[PersistedRepresentationReceipt, ...]


@dataclass(frozen=True, slots=True)
class LegacyPersistedClaimReceipt:
    """Identify one persisted candidate claim and its exact Evidence rows."""

    claim_id: UUID
    evidence_ids: tuple[UUID, ...]
    duplicate: bool


@dataclass(frozen=True, slots=True)
class LegacyClaimProposalReceipt:
    """Identify one deterministic source-statement proposal run."""

    representation_id: UUID
    claims: tuple[PersistedClaimReceipt, ...]


@dataclass(frozen=True, slots=True)
class LegacyPersistedAtomicClaimReceipt:
    """Identify one guarded atomic-source-proposition persistence result."""

    source_claim_id: UUID
    claim_id: UUID
    evidence_ids: tuple[UUID, ...]
    duplicate: bool


class LegacyCollectorStore:
    """Persist Collector provenance, artifacts, representations, and reviews."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.document_directory = self.database_path.with_name(
            f"{self.database_path.stem}.documents"
        )
        self.artifact_directory = self.database_path.with_name(
            f"{self.database_path.stem}.artifacts"
        )
        self.backup_directory = self.database_path.with_name(
            f"{self.database_path.stem}.backups"
        )
        self._last_migration_result: MigrationResult | None = None

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.database_path,
            timeout=30.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")

        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create v2 or safely migrate an existing Collector v1 database."""
        self._last_migration_result = initialize_or_migrate(
            database_path=self.database_path,
            legacy_document_directory=self.document_directory,
            artifact_directory=self.artifact_directory,
            backup_root=self.backup_directory,
        )

    @property
    def last_migration_result(self) -> MigrationResult | None:
        """Return the latest initialization/migration result for diagnostics."""
        return self._last_migration_result

    def schema_version(self) -> int:
        """Return the installed Collector schema version."""
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT MAX(version) AS version FROM schema_migrations"
            ).fetchone()
            return int(row["version"])

    def begin_acquisition_job(
        self,
        *,
        requested_locator: str,
        job_kind: str,
        adapter_name: str,
        adapter_version: str,
    ) -> UUID:
        """Create one running acquisition job before adapter retrieval."""
        self.initialize()
        job_id = uuid4()
        now = _utc_now_text()
        with self._connection() as connection:
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
                VALUES (?, NULL, ?, ?, ?, ?, 'running', ?, NULL, ?)
                """,
                (
                    str(job_id),
                    job_kind,
                    requested_locator,
                    adapter_name,
                    adapter_version,
                    now,
                    now,
                ),
            )
        return job_id

    def finish_acquisition_job(
        self,
        job_id: UUID,
        *,
        status: str,
        source_id: UUID | None = None,
        diagnostics: Sequence[AcquisitionDiagnostic] = (),
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Finish one acquisition job and append structured diagnostics."""
        if status not in {
            "succeeded",
            "partial",
            "failed",
            "cancelled",
        }:
            raise ValueError(f"Unsupported acquisition job status: {status}")

        completed = _utc_now_text()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id
                FROM acquisition_jobs
                WHERE id = ?
                """,
                (str(job_id),),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown acquisition job: {job_id}")

            connection.execute(
                """
                UPDATE acquisition_jobs
                SET status = ?, completed_at = ?, source_id = ?
                WHERE id = ?
                """,
                (
                    status,
                    completed,
                    str(source_id) if source_id is not None else None,
                    str(job_id),
                ),
            )

            diagnostic_rows = list(diagnostics)
            if error_code is not None:
                diagnostic_rows.append(
                    AcquisitionDiagnostic(
                        severity="error",
                        code=error_code,
                        message=error_message or "",
                    )
                )

            for diagnostic in diagnostic_rows:
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
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid4()),
                        str(job_id),
                        diagnostic.severity,
                        diagnostic.code,
                        diagnostic.message,
                        json.dumps(
                            diagnostic.details,
                            sort_keys=True,
                        ),
                        completed,
                    ),
                )

    def _begin_job(
        self,
        *,
        source_locator: str,
        source_type: str,
    ) -> UUID:
        return self.begin_acquisition_job(
            requested_locator=source_locator,
            job_kind=f"{source_type}_transcript_import",
            adapter_name="manual-transcript-import",
            adapter_version="2",
        )

    def _finish_job(
        self,
        job_id: UUID,
        *,
        status: str,
        source_id: UUID | None = None,
        error: str | None = None,
    ) -> None:
        self.finish_acquisition_job(
            job_id,
            status=status,
            source_id=source_id,
            error_code="import_failed" if error is not None else None,
            error_message=error,
        )

    def _store_raw_artifact(
        self,
        source_path: Path,
        expected_sha256: str,
    ) -> tuple[Path, str]:
        relpath = _cas_relpath(expected_sha256)
        destination = self.artifact_directory / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            actual = _sha256_file(destination)
            if actual != expected_sha256:
                raise RuntimeError(
                    "Immutable Collector artifact checksum mismatch: "
                    f"{destination}"
                )
            return destination, relpath

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

            actual = _sha256_file(temporary)
            if actual != expected_sha256:
                raise RuntimeError(
                    "Raw artifact changed while it was being persisted."
                )
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()

        return destination, relpath

    def _store_representation_content(
        self,
        source_path: Path,
        expected_sha256: str,
    ) -> tuple[Path, str]:
        relpath = f"derived/{expected_sha256[:2]}/{expected_sha256}"
        destination = self.artifact_directory / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists():
            actual = _sha256_file(destination)
            if actual != expected_sha256:
                raise RuntimeError(
                    "Immutable representation checksum mismatch: "
                    f"{destination}"
                )
            return destination, relpath

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

            actual = _sha256_file(temporary)
            if actual != expected_sha256:
                raise RuntimeError(
                    "Representation changed while it was being persisted."
                )
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()

        return destination, relpath

    def persist_acquisition_result(
        self,
        *,
        job_id: UUID,
        result: AcquisitionResult,
        adapter_name: str,
        adapter_version: str,
        maximum_passage_characters: int,
    ) -> AcquisitionReceipt:
        """Persist validated source-agnostic adapter output into schema v2."""
        if maximum_passage_characters <= 0:
            raise ValueError(
                "maximum_passage_characters must be greater than zero"
            )

        self.initialize()
        source = result.canonical_source

        payload_state: dict[
            str,
            tuple[UUID, str, Path, str],
        ] = {}
        for payload in result.payloads:
            raw_sha256 = _sha256_file(payload.staged_path)
            stored_path, relpath = self._store_raw_artifact(
                payload.staged_path,
                raw_sha256,
            )
            payload_state[payload.logical_key] = (
                uuid4(),
                raw_sha256,
                stored_path,
                relpath,
            )

        representation_state: dict[
            str,
            tuple[str, Path, str],
        ] = {}
        for representation in result.representations:
            content_sha256 = _sha256_file(representation.staged_path)
            stored_path, relpath = self._store_representation_content(
                representation.staged_path,
                content_sha256,
            )
            representation_state[representation.logical_key] = (
                content_sha256,
                stored_path,
                relpath,
            )

        payload_receipts: list[PersistedPayloadReceipt] = []
        representation_receipts: list[PersistedRepresentationReceipt] = []

        with self._connection() as connection:
            job_row = connection.execute(
                """
                SELECT status, adapter_name, adapter_version
                FROM acquisition_jobs
                WHERE id = ?
                """,
                (str(job_id),),
            ).fetchone()
            if job_row is None:
                raise KeyError(f"Unknown acquisition job: {job_id}")
            if str(job_row["status"]) != "running":
                raise RuntimeError(
                    "Acquisition result can only persist into a running job."
                )
            if (
                str(job_row["adapter_name"]) != adapter_name
                or str(job_row["adapter_version"]) != adapter_version
            ):
                raise RuntimeError(
                    "Acquisition job adapter identity changed before persist."
                )

            source_row = connection.execute(
                """
                SELECT id
                FROM sources
                WHERE source_type = ? AND canonical_locator = ?
                """,
                (
                    source.source_type,
                    source.canonical_locator,
                ),
            ).fetchone()

            if source_row is None:
                source_id = uuid4()
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
                        str(source_id),
                        source.source_type,
                        source.canonical_locator,
                        source.title,
                        source.author,
                        source.language,
                        json.dumps(source.metadata, sort_keys=True),
                        _utc_now_text(),
                    ),
                )
            else:
                source_id = UUID(str(source_row["id"]))

            resolved_payload_ids: dict[str, UUID] = {}
            for payload in result.payloads:
                (
                    proposed_raw_id,
                    raw_sha256,
                    stored_path,
                    storage_relpath,
                ) = payload_state[payload.logical_key]

                raw_row = connection.execute(
                    """
                    SELECT id, storage_relpath
                    FROM raw_artifacts
                    WHERE sha256 = ?
                    """,
                    (raw_sha256,),
                ).fetchone()
                if raw_row is None:
                    raw_artifact_id = proposed_raw_id
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
                            str(raw_artifact_id),
                            raw_sha256,
                            payload.staged_path.stat().st_size,
                            payload.media_type,
                            storage_relpath,
                            _utc_now_text(),
                        ),
                    )
                else:
                    raw_artifact_id = UUID(str(raw_row["id"]))
                    if str(raw_row["storage_relpath"]) != storage_relpath:
                        raise RuntimeError(
                            "Raw artifact points to an unexpected CAS path."
                        )

                resolved_payload_ids[payload.logical_key] = raw_artifact_id
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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL,
                            ?, ?, ?, ?)
                    """,
                    (
                        str(uuid4()),
                        str(job_id),
                        str(source_id),
                        str(raw_artifact_id),
                        payload.original_locator,
                        payload.canonical_locator,
                        payload.protocol,
                        _utc_now_text(),
                        json.dumps(
                            payload.request_metadata,
                            sort_keys=True,
                        ),
                        json.dumps(
                            payload.response_metadata,
                            sort_keys=True,
                        ),
                        adapter_name,
                        adapter_version,
                    ),
                )
                payload_receipts.append(
                    PersistedPayloadReceipt(
                        logical_key=payload.logical_key,
                        raw_artifact_id=raw_artifact_id,
                        sha256=raw_sha256,
                        stored_path=stored_path,
                    )
                )

            for representation in result.representations:
                (
                    content_sha256,
                    stored_path,
                    storage_relpath,
                ) = representation_state[representation.logical_key]
                representation_row = connection.execute(
                    """
                    SELECT id, storage_relpath
                    FROM representations
                    WHERE
                        source_id = ?
                        AND representation_kind = ?
                        AND content_sha256 = ?
                    """,
                    (
                        str(source_id),
                        representation.representation_kind,
                        content_sha256,
                    ),
                ).fetchone()

                duplicate = representation_row is not None
                if representation_row is None:
                    representation_id = uuid4()
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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(representation_id),
                            str(source_id),
                            representation.representation_kind,
                            representation.media_type,
                            representation.language,
                            content_sha256,
                            representation.staged_path.stat().st_size,
                            storage_relpath,
                            json.dumps(
                                representation.metadata,
                                sort_keys=True,
                            ),
                            _utc_now_text(),
                        ),
                    )
                else:
                    representation_id = UUID(
                        str(representation_row["id"])
                    )
                    if str(
                        representation_row["storage_relpath"]
                    ) != storage_relpath:
                        raise RuntimeError(
                            "Duplicate representation points to an "
                            "unexpected derived-content path."
                        )

                parent_raw_id = resolved_payload_ids[
                    representation.parent_payload_key
                ]
                derivation_parameters = json.dumps(
                    representation.derivation_parameters,
                    sort_keys=True,
                )
                derivation_row = connection.execute(
                    """
                    SELECT id
                    FROM representation_derivations
                    WHERE
                        child_representation_id = ?
                        AND parent_raw_artifact_id = ?
                        AND parent_representation_id IS NULL
                        AND method = ?
                        AND tool_name = ?
                        AND tool_version = ?
                        AND parameters_json = ?
                    """,
                    (
                        str(representation_id),
                        str(parent_raw_id),
                        representation.derivation_method,
                        representation.tool_name,
                        representation.tool_version,
                        derivation_parameters,
                    ),
                ).fetchone()
                if derivation_row is None:
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
                        VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid4()),
                            str(representation_id),
                            str(parent_raw_id),
                            representation.derivation_method,
                            representation.tool_name,
                            representation.tool_version,
                            derivation_parameters,
                            _utc_now_text(),
                        ),
                    )

                explicit_segments = representation.segments
                if explicit_segments:
                    segments = explicit_segments
                else:
                    passages = (
                        split_into_passages(
                            representation.text,
                            maximum_characters=maximum_passage_characters,
                        )
                        if representation.text is not None
                        else ()
                    )
                    segments = tuple(
                        SegmentDraft(
                            text=passage,
                            metadata={"origin": "acquire"},
                        )
                        for passage in passages
                    )

                stored_rows = connection.execute(
                    """
                    SELECT
                        id,
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
                        metadata_json
                    FROM segments
                    WHERE representation_id = ?
                    ORDER BY segment_index
                    """,
                    (str(representation_id),),
                ).fetchall()

                if stored_rows:
                    if len(stored_rows) != len(segments):
                        raise RuntimeError(
                            "Deterministic segment count changed for an "
                            "already persisted representation."
                        )
                    segment_ids: list[UUID] = []
                    review_statuses: list[str] = []
                    for row, segment in zip(
                        stored_rows,
                        segments,
                        strict=True,
                    ):
                        expected_index = len(segment_ids) + 1
                        expected_hash = _sha256_bytes(
                            segment.text.encode("utf-8")
                        )
                        expected_metadata = json.dumps(
                            segment.metadata,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        stored_metadata = json.dumps(
                            json.loads(str(row["metadata_json"])),
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                        if (
                            int(row["segment_index"]) != expected_index
                            or str(row["text"]) != segment.text
                            or str(row["text_sha256"]) != expected_hash
                            or row["start_char"] != segment.start_char
                            or row["end_char"] != segment.end_char
                            or row["start_seconds"] != segment.start_seconds
                            or row["end_seconds"] != segment.end_seconds
                            or row["page_number"] != segment.page_number
                            or row["frame_start"] != segment.frame_start
                            or row["frame_end"] != segment.frame_end
                            or stored_metadata != expected_metadata
                        ):
                            raise RuntimeError(
                                "Deterministic segment content/anchors changed "
                                "for an already persisted representation."
                            )
                        segment_ids.append(UUID(str(row["id"])))
                        review_statuses.append(str(row["review_status"]))
                else:
                    segment_ids = []
                    review_statuses = []
                    for index, segment in enumerate(segments, start=1):
                        segment_id = uuid4()
                        segment_ids.append(segment_id)
                        review_statuses.append("pending")
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
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                    'pending', ?, ?)
                            """,
                            (
                                str(segment_id),
                                str(representation_id),
                                index,
                                segment.text,
                                _sha256_bytes(segment.text.encode("utf-8")),
                                segment.start_char,
                                segment.end_char,
                                segment.start_seconds,
                                segment.end_seconds,
                                segment.page_number,
                                segment.frame_start,
                                segment.frame_end,
                                json.dumps(
                                    segment.metadata,
                                    sort_keys=True,
                                ),
                                _utc_now_text(),
                            ),
                        )

                representation_receipts.append(
                    PersistedRepresentationReceipt(
                        logical_key=representation.logical_key,
                        representation_id=representation_id,
                        sha256=content_sha256,
                        stored_path=stored_path,
                        segment_ids=tuple(segment_ids),
                        segment_review_statuses=tuple(review_statuses),
                        duplicate=duplicate,
                    )
                )

        return AcquisitionReceipt(
            job_id=job_id,
            source_id=source_id,
            payloads=tuple(payload_receipts),
            representations=tuple(representation_receipts),
        )

    def persist_transcript(
        self,
        imported: ImportedTranscript,
        *,
        transcript_path: str | Path,
        passages: tuple[str, ...],
    ) -> ImportReceipt:
        """Persist one transcript into the v2 provenance model."""
        self.initialize()

        path = Path(transcript_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)

        raw = path.read_bytes()
        document_sha256 = _sha256_bytes(raw)
        source_type = _enum_value(imported.source.source_type)
        source_locator = _text(imported.source.locator)

        job_id = self._begin_job(
            source_locator=source_locator,
            source_type=source_type,
        )

        source_id: UUID | None = None
        document_id: UUID | None = None

        try:
            stored_path, storage_relpath = self._store_raw_artifact(
                path,
                document_sha256,
            )

            with self._connection() as connection:
                source_row = connection.execute(
                    """
                    SELECT id
                    FROM sources
                    WHERE source_type = ? AND canonical_locator = ?
                    """,
                    (source_type, source_locator),
                ).fetchone()

                if source_row is None:
                    source_id = imported.source.id
                    source_metadata = {
                        "description": _text(imported.source.description),
                        "review_status": _enum_value(
                            getattr(
                                imported.source,
                                "review_status",
                                "imported",
                            )
                        ),
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
                            str(source_id),
                            source_type,
                            source_locator,
                            _text(imported.source.title),
                            _text(imported.source.author),
                            _text(imported.source.language),
                            json.dumps(source_metadata, sort_keys=True),
                            imported.source.imported_at.isoformat(),
                        ),
                    )
                else:
                    source_id = UUID(str(source_row["id"]))

                raw_row = connection.execute(
                    """
                    SELECT id, storage_relpath
                    FROM raw_artifacts
                    WHERE sha256 = ?
                    """,
                    (document_sha256,),
                ).fetchone()

                if raw_row is None:
                    raw_artifact_id = uuid4()
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
                            str(raw_artifact_id),
                            document_sha256,
                            len(raw),
                            "text/plain; charset=utf-8",
                            storage_relpath,
                            _utc_now_text(),
                        ),
                    )
                else:
                    raw_artifact_id = UUID(str(raw_row["id"]))
                    if str(raw_row["storage_relpath"]) != storage_relpath:
                        raise RuntimeError(
                            "Raw artifact points to an unexpected CAS path."
                        )

                representation_row = connection.execute(
                    """
                    SELECT id, storage_relpath
                    FROM representations
                    WHERE
                        source_id = ?
                        AND representation_kind = 'transcript'
                        AND content_sha256 = ?
                    """,
                    (str(source_id), document_sha256),
                ).fetchone()

                duplicate_document = representation_row is not None

                if representation_row is None:
                    document_id = uuid4()
                    representation_metadata = {
                        "original_path": str(path),
                        "character_count": len(imported.text),
                        "compatibility_name": "document",
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
                            str(document_id),
                            str(source_id),
                            "text/plain; charset=utf-8",
                            _text(imported.source.language),
                            document_sha256,
                            len(raw),
                            storage_relpath,
                            json.dumps(
                                representation_metadata,
                                sort_keys=True,
                            ),
                            _utc_now_text(),
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
                        VALUES (?, ?, ?, NULL, 'identity',
                                'manual-transcript-import', '2', '{}', ?)
                        """,
                        (
                            str(uuid4()),
                            str(document_id),
                            str(raw_artifact_id),
                            _utc_now_text(),
                        ),
                    )

                    passage_ids: list[UUID] = []
                    passage_review_statuses: list[str] = []
                    for index, passage in enumerate(passages, start=1):
                        passage_id = uuid4()
                        passage_ids.append(passage_id)
                        passage_review_statuses.append("pending")
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
                            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL,
                                    NULL, NULL, NULL, 'pending',
                                    '{"compatibility_name":"passage"}', ?)
                            """,
                            (
                                str(passage_id),
                                str(document_id),
                                index,
                                passage,
                                _sha256_bytes(passage.encode("utf-8")),
                                _utc_now_text(),
                            ),
                        )
                else:
                    document_id = UUID(str(representation_row["id"]))
                    if str(representation_row["storage_relpath"]) != storage_relpath:
                        raise RuntimeError(
                            "Duplicate transcript representation points to an "
                            "unexpected CAS path."
                        )

                    stored_rows = connection.execute(
                        """
                        SELECT
                            id,
                            segment_index,
                            text,
                            text_sha256,
                            review_status
                        FROM segments
                        WHERE representation_id = ?
                        ORDER BY segment_index
                        """,
                        (str(document_id),),
                    ).fetchall()

                    if len(stored_rows) != len(passages):
                        raise RuntimeError(
                            "Deterministic passage count changed for an "
                            "already persisted transcript."
                        )

                    passage_ids = []
                    passage_review_statuses = []
                    for row, passage in zip(
                        stored_rows,
                        passages,
                        strict=True,
                    ):
                        expected_index = len(passage_ids) + 1
                        expected_hash = _sha256_bytes(
                            passage.encode("utf-8")
                        )
                        if (
                            int(row["segment_index"]) != expected_index
                            or str(row["text"]) != passage
                            or str(row["text_sha256"]) != expected_hash
                        ):
                            raise RuntimeError(
                                "Deterministic passage content changed for an "
                                "already persisted transcript."
                            )
                        passage_ids.append(UUID(str(row["id"])))
                        passage_review_statuses.append(
                            str(row["review_status"])
                        )

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
                    VALUES (?, ?, ?, ?, ?, ?, 'file', ?, NULL, NULL, NULL,
                            '{}', '{}', 'manual-transcript-import', '2')
                    """,
                    (
                        str(uuid4()),
                        str(job_id),
                        str(source_id),
                        str(raw_artifact_id),
                        str(path),
                        source_locator,
                        _utc_now_text(),
                    ),
                )

            assert source_id is not None
            assert document_id is not None

            self._finish_job(
                job_id,
                status="succeeded",
                source_id=source_id,
            )

            return ImportReceipt(
                job_id=job_id,
                source_id=source_id,
                document_id=document_id,
                document_sha256=document_sha256,
                stored_document_path=stored_path,
                passage_ids=tuple(passage_ids),
                passage_review_statuses=tuple(passage_review_statuses),
                duplicate_document=duplicate_document,
            )
        except Exception as exc:
            self._finish_job(
                job_id,
                status="failed",
                source_id=source_id,
                error=f"{type(exc).__name__}: {exc}",
            )
            raise

    def propose_source_statement_claims(
        self,
        *,
        representation_id: UUID | str,
        limit: int = 50,
        maximum_claim_characters: int = 350,
        maximum_window_seconds: float = 15.0,
    ) -> ClaimProposalReceipt:
        """Create pending source-statement Claims with exact segment Evidence."""
        self.initialize()
        representation_text = str(representation_id)

        with self._connection() as connection:
            representation = connection.execute(
                """
                SELECT id
                FROM representations
                WHERE id = ?
                """,
                (representation_text,),
            ).fetchone()
            if representation is None:
                raise KeyError(
                    f"Unknown representation: {representation_id}"
                )

            rows = connection.execute(
                """
                SELECT
                    s.id,
                    s.segment_index,
                    s.text,
                    s.review_status,
                    s.start_seconds,
                    s.end_seconds,
                    s.page_number,
                    s.frame_start,
                    s.frame_end,
                    (
                        SELECT rd.corrected_text
                        FROM review_decisions AS rd
                        WHERE rd.segment_id = s.id
                          AND rd.decision = 'correct'
                        ORDER BY rd.created_at DESC, rd.id DESC
                        LIMIT 1
                    ) AS corrected_text
                FROM segments AS s
                WHERE s.representation_id = ?
                ORDER BY s.segment_index
                """,
                (representation_text,),
            ).fetchall()

            segments = tuple(
                ClaimSegment(
                    id=str(row["id"]),
                    segment_index=int(row["segment_index"]),
                    text=_text(row["text"]),
                    effective_text=(
                        _text(row["corrected_text"])
                        if row["corrected_text"] is not None
                        else _text(row["text"])
                    ),
                    review_status=str(row["review_status"]),
                    start_seconds=row["start_seconds"],
                    end_seconds=row["end_seconds"],
                    page_number=row["page_number"],
                    frame_start=row["frame_start"],
                    frame_end=row["frame_end"],
                    correction_applied=row["corrected_text"] is not None,
                )
                for row in rows
                if _text(row["text"])
            )

            candidates = build_source_statement_candidates(
                segments,
                representation_id=representation_text,
                limit=limit,
                maximum_claim_characters=maximum_claim_characters,
                maximum_window_seconds=maximum_window_seconds,
            )

            receipts: list[PersistedClaimReceipt] = []
            now = _utc_now_text()
            for candidate in candidates:
                metadata_json = json.dumps(
                    candidate.metadata,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                existing = connection.execute(
                    """
                    SELECT id
                    FROM claims
                    WHERE claim_kind = ?
                      AND text = ?
                      AND metadata_json = ?
                    """,
                    (
                        candidate.claim_kind,
                        candidate.text,
                        metadata_json,
                    ),
                ).fetchone()

                if existing is not None:
                    claim_id = UUID(str(existing["id"]))
                    evidence_rows = connection.execute(
                        """
                        SELECT id
                        FROM evidence
                        WHERE claim_id = ?
                        ORDER BY created_at, id
                        """,
                        (str(claim_id),),
                    ).fetchall()
                    if len(evidence_rows) != len(candidate.evidence):
                        raise RuntimeError(
                            "Existing candidate Claim has inconsistent Evidence."
                        )
                    receipts.append(
                        PersistedClaimReceipt(
                            claim_id=claim_id,
                            evidence_ids=tuple(
                                UUID(str(row["id"]))
                                for row in evidence_rows
                            ),
                            duplicate=True,
                        )
                    )
                    continue

                claim_id = uuid4()
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
                    VALUES (?, ?, ?, 'pending', ?, ?)
                    """,
                    (
                        str(claim_id),
                        candidate.claim_kind,
                        candidate.text,
                        metadata_json,
                        now,
                    ),
                )

                evidence_ids: list[UUID] = []
                for item in candidate.evidence:
                    evidence_id = uuid4()
                    evidence_ids.append(evidence_id)
                    evidence_metadata = json.dumps(
                        {
                            "role": "verbatim_source_segment",
                            "extractor": "source-statement-window-v1",
                        },
                        sort_keys=True,
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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(evidence_id),
                            str(claim_id),
                            item.segment_id,
                            item.evidence_text,
                            _sha256_bytes(
                                item.evidence_text.encode("utf-8")
                            ),
                            item.segment_char_start,
                            item.segment_char_end,
                            item.start_seconds,
                            item.end_seconds,
                            item.page_number,
                            item.frame_start,
                            item.frame_end,
                            evidence_metadata,
                            now,
                        ),
                    )

                validate_evidence_anchors(connection)
                receipts.append(
                    PersistedClaimReceipt(
                        claim_id=claim_id,
                        evidence_ids=tuple(evidence_ids),
                        duplicate=False,
                    )
                )

        return ClaimProposalReceipt(
            representation_id=UUID(representation_text),
            claims=tuple(receipts),
        )

    @staticmethod
    def _effective_claim_text(
        connection: sqlite3.Connection,
        *,
        claim_id: str,
        original_text: str,
    ) -> str:
        correction = connection.execute(
            """
            SELECT corrected_text
            FROM review_decisions
            WHERE claim_id = ?
              AND corrected_text IS NOT NULL
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (claim_id,),
        ).fetchone()
        if correction is None:
            return original_text
        return _text(correction["corrected_text"])

    def persist_atomic_claim_batch(
        self,
        batch: AtomicClaimBatch,
    ) -> tuple[PersistedAtomicClaimReceipt, ...]:
        """Persist validated semantic proposals using existing Evidence only."""
        self.initialize()
        receipts: list[PersistedAtomicClaimReceipt] = []

        with self._connection() as connection:
            for proposal in batch.proposals:
                if proposal.qualifiers.get("benchmark_only") is True:
                    raise ValueError(
                        "Benchmark-only semantic proposals cannot be "
                        "persisted."
                    )

                parent = connection.execute(
                    """
                    SELECT
                        id,
                        claim_kind,
                        text,
                        review_status
                    FROM claims
                    WHERE id = ?
                    """,
                    (proposal.source_claim_id,),
                ).fetchone()
                if parent is None:
                    raise KeyError(
                        f"Unknown source Claim: {proposal.source_claim_id}"
                    )
                if str(parent["claim_kind"]) != "source_statement":
                    raise ValueError(
                        "Atomic propositions may only derive from "
                        "source_statement Claims."
                    )
                parent_review_status = str(parent["review_status"])
                if parent_review_status == "rejected":
                    raise ValueError(
                        "Rejected source_statement Claims cannot produce "
                        "atomic propositions."
                    )

                effective_text = self._effective_claim_text(
                    connection,
                    claim_id=proposal.source_claim_id,
                    original_text=str(parent["text"]),
                )
                effective_hash = _sha256_bytes(
                    effective_text.encode("utf-8")
                )
                if (
                    effective_hash
                    != proposal.source_claim_effective_text_sha256
                ):
                    raise ValueError(
                        "Semantic proposal is stale: source Claim effective "
                        "text SHA-256 no longer matches."
                    )

                selected_rows: list[sqlite3.Row] = []
                for parent_evidence_id in proposal.evidence_ids:
                    row = connection.execute(
                        """
                        SELECT
                            e.id,
                            e.segment_id,
                            e.evidence_text,
                            e.evidence_sha256,
                            e.segment_char_start,
                            e.segment_char_end,
                            e.start_seconds,
                            e.end_seconds,
                            e.page_number,
                            e.frame_start,
                            e.frame_end,
                            s.review_status AS segment_review_status
                        FROM evidence AS e
                        JOIN segments AS s ON s.id = e.segment_id
                        WHERE e.id = ?
                          AND e.claim_id = ?
                        """,
                        (
                            parent_evidence_id,
                            proposal.source_claim_id,
                        ),
                    ).fetchone()
                    if row is None:
                        raise ValueError(
                            "Semantic proposal references Evidence that does "
                            "not belong to its source Claim."
                        )
                    if str(row["segment_review_status"]) == "rejected":
                        raise ValueError(
                            "Semantic proposal references Evidence from a "
                            "rejected Segment."
                        )
                    if (
                        _sha256_bytes(
                            str(row["evidence_text"]).encode("utf-8")
                        )
                        != str(row["evidence_sha256"])
                    ):
                        raise RuntimeError(
                            "Persisted parent Evidence SHA-256 is inconsistent."
                        )
                    selected_rows.append(row)

                fingerprint_payload = {
                    "claim_kind": "atomic_source_proposition",
                    "text": proposal.text,
                    "semantic_type": proposal.semantic_type,
                    "source_claim_id": proposal.source_claim_id,
                    "source_claim_effective_text_sha256": effective_hash,
                    "evidence_ids": list(proposal.evidence_ids),
                    "extractor": {
                        "name": batch.extractor.name,
                        "version": batch.extractor.version,
                    },
                    "qualifiers": proposal.qualifiers,
                }
                fingerprint = _sha256_bytes(
                    json.dumps(
                        fingerprint_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                metadata: dict[str, object] = {
                    "epistemic_status": (
                        "candidate_atomic_source_proposition"
                    ),
                    "extractor": "semantic-claim-contract-v1",
                    "semantic_extractor_name": batch.extractor.name,
                    "semantic_extractor_version": batch.extractor.version,
                    "semantic_type": proposal.semantic_type,
                    "source_claim_id": proposal.source_claim_id,
                    "source_claim_review_status": parent_review_status,
                    "source_claim_effective_text_sha256": effective_hash,
                    "selected_parent_evidence_ids": list(
                        proposal.evidence_ids
                    ),
                    "qualifiers": proposal.qualifiers,
                    "candidate_fingerprint": fingerprint,
                    "automatic_scientific_acceptance": False,
                }
                metadata_json = json.dumps(
                    metadata,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )

                existing = connection.execute(
                    """
                    SELECT id
                    FROM claims
                    WHERE claim_kind = 'atomic_source_proposition'
                      AND metadata_json = ?
                    """,
                    (metadata_json,),
                ).fetchone()
                if existing is not None:
                    claim_id = UUID(str(existing["id"]))
                    evidence_rows = connection.execute(
                        """
                        SELECT id
                        FROM evidence
                        WHERE claim_id = ?
                        ORDER BY created_at, id
                        """,
                        (str(claim_id),),
                    ).fetchall()
                    if len(evidence_rows) != len(selected_rows):
                        raise RuntimeError(
                            "Existing atomic Claim has inconsistent Evidence."
                        )
                    receipts.append(
                        PersistedAtomicClaimReceipt(
                            source_claim_id=UUID(
                                proposal.source_claim_id
                            ),
                            claim_id=claim_id,
                            evidence_ids=tuple(
                                UUID(str(row["id"]))
                                for row in evidence_rows
                            ),
                            duplicate=True,
                        )
                    )
                    continue

                now = _utc_now_text()
                claim_id = uuid4()
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
                    VALUES (
                        ?,
                        'atomic_source_proposition',
                        ?,
                        'pending',
                        ?,
                        ?
                    )
                    """,
                    (
                        str(claim_id),
                        proposal.text,
                        metadata_json,
                        now,
                    ),
                )

                evidence_ids: list[UUID] = []
                for parent_evidence in selected_rows:
                    new_evidence_id = uuid4()
                    evidence_ids.append(new_evidence_id)
                    evidence_metadata = json.dumps(
                        {
                            "role": "verbatim_parent_evidence",
                            "extractor": "semantic-claim-contract-v1",
                            "parent_evidence_id": str(
                                parent_evidence["id"]
                            ),
                            "source_claim_id": proposal.source_claim_id,
                        },
                        sort_keys=True,
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
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(new_evidence_id),
                            str(claim_id),
                            str(parent_evidence["segment_id"]),
                            str(parent_evidence["evidence_text"]),
                            str(parent_evidence["evidence_sha256"]),
                            parent_evidence["segment_char_start"],
                            parent_evidence["segment_char_end"],
                            parent_evidence["start_seconds"],
                            parent_evidence["end_seconds"],
                            parent_evidence["page_number"],
                            parent_evidence["frame_start"],
                            parent_evidence["frame_end"],
                            evidence_metadata,
                            now,
                        ),
                    )

                validate_evidence_anchors(connection)
                receipts.append(
                    PersistedAtomicClaimReceipt(
                        source_claim_id=UUID(
                            proposal.source_claim_id
                        ),
                        claim_id=claim_id,
                        evidence_ids=tuple(evidence_ids),
                        duplicate=False,
                    )
                )

        return tuple(receipts)

    def get_claim_with_evidence(
        self,
        claim_id: UUID | str,
    ) -> dict[str, Any]:
        """Return one Claim plus exact Evidence and source provenance."""
        self.initialize()
        with self._connection() as connection:
            claim = connection.execute(
                """
                SELECT
                    id,
                    claim_kind,
                    text,
                    review_status,
                    metadata_json,
                    created_at
                FROM claims
                WHERE id = ?
                """,
                (str(claim_id),),
            ).fetchone()
            if claim is None:
                raise KeyError(f"Unknown claim: {claim_id}")

            evidence_rows = connection.execute(
                """
                SELECT
                    e.id,
                    e.segment_id,
                    e.evidence_text,
                    e.evidence_sha256,
                    e.segment_char_start,
                    e.segment_char_end,
                    e.start_seconds,
                    e.end_seconds,
                    e.page_number,
                    e.frame_start,
                    e.frame_end,
                    e.metadata_json,
                    s.segment_index,
                    s.review_status AS segment_review_status,
                    r.id AS representation_id,
                    r.representation_kind,
                    r.language AS representation_language,
                    src.id AS source_id,
                    src.source_type,
                    src.canonical_locator,
                    src.title AS source_title,
                    src.author AS source_author
                FROM evidence AS e
                JOIN segments AS s ON s.id = e.segment_id
                JOIN representations AS r ON r.id = s.representation_id
                JOIN sources AS src ON src.id = r.source_id
                WHERE e.claim_id = ?
                ORDER BY s.segment_index, e.created_at, e.id
                """,
                (str(claim_id),),
            ).fetchall()
            review_rows = connection.execute(
                """
                SELECT
                    id,
                    decision,
                    reviewer,
                    rationale,
                    corrected_text,
                    created_at
                FROM review_decisions
                WHERE claim_id = ?
                ORDER BY created_at, id
                """,
                (str(claim_id),),
            ).fetchall()

        payload = dict(claim)
        payload["metadata"] = json.loads(str(payload.pop("metadata_json")))
        evidence: list[dict[str, Any]] = []
        for row in evidence_rows:
            item = dict(row)
            item["metadata"] = json.loads(
                str(item.pop("metadata_json"))
            )
            evidence.append(item)
        payload["evidence"] = evidence
        payload["review_history"] = [
            dict(row) for row in review_rows
        ]
        corrected_text = next(
            (
                str(row["corrected_text"])
                for row in reversed(review_rows)
                if row["corrected_text"] is not None
            ),
            None,
        )
        payload["effective_text"] = (
            corrected_text
            if corrected_text is not None
            else str(payload["text"])
        )
        payload["text_was_corrected"] = corrected_text is not None
        return payload

    def summary(self) -> dict[str, int]:
        """Return non-sensitive canonical and compatibility record counts."""
        self.initialize()
        canonical_tables = (
            "sources",
            "raw_artifacts",
            "retrievals",
            "representations",
            "representation_derivations",
            "segments",
            "claims",
            "evidence",
            "acquisition_jobs",
            "job_diagnostics",
            "review_decisions",
        )

        with self._connection() as connection:
            result = {
                table: int(
                    connection.execute(
                        f"SELECT COUNT(*) AS count FROM {table}"
                    ).fetchone()["count"]
                )
                for table in canonical_tables
            }
            result["pending_segments"] = int(
                connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM segments
                    WHERE review_status = 'pending'
                    """
                ).fetchone()["count"]
            )
            result["pending_claims"] = int(
                connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM claims
                    WHERE review_status = 'pending'
                    """
                ).fetchone()["count"]
            )
            result["failed_jobs"] = int(
                connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM acquisition_jobs
                    WHERE status = 'failed'
                    """
                ).fetchone()["count"]
            )
            result["documents"] = int(
                connection.execute(
                    """
                    SELECT COUNT(DISTINCT representation_id) AS count
                    FROM segments
                    """
                ).fetchone()["count"]
            )

        result["passages"] = result["segments"]
        result["collection_jobs"] = result["acquisition_jobs"]
        result["pending_passages"] = result["pending_segments"]
        result["schema_version"] = SCHEMA_VERSION
        return result

    def list_pending_reviews(
        self,
        *,
        limit: int = 50,
    ) -> tuple[dict[str, Any], ...]:
        """Return pending segments/claims using historical CLI target names."""
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        self.initialize()
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    'passage' AS target_type,
                    s.id AS target_id,
                    s.representation_id AS document_id,
                    s.segment_index AS passage_index,
                    s.text AS text,
                    s.review_status AS review_status,
                    s.created_at AS created_at
                FROM segments AS s
                WHERE s.review_status = 'pending'

                UNION ALL

                SELECT
                    'claim' AS target_type,
                    c.id AS target_id,
                    NULL AS document_id,
                    NULL AS passage_index,
                    c.text AS text,
                    c.review_status AS review_status,
                    c.created_at AS created_at
                FROM claims AS c
                WHERE c.review_status = 'pending'

                ORDER BY created_at, target_type, passage_index
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return tuple(dict(row) for row in rows)

    def record_review_decision(
        self,
        *,
        target_type: str,
        target_id: UUID | str,
        decision: str,
        reviewer: str = "",
        rationale: str = "",
        corrected_text: str | None = None,
    ) -> UUID:
        """Append one review decision while preserving original source text."""
        normalized_target = target_type.strip().lower()
        normalized_decision = decision.strip().lower()

        if normalized_target not in VALID_REVIEW_TARGETS:
            raise ValueError("target_type must be 'passage' or 'claim'")
        if normalized_decision not in VALID_REVIEW_DECISIONS:
            raise ValueError("decision must be accept, correct, or reject")
        if (
            normalized_decision == "correct"
            and not (corrected_text or "").strip()
        ):
            raise ValueError("A correction requires corrected_text.")

        table = "segments" if normalized_target == "passage" else "claims"
        review_status = {
            "accept": "accepted",
            "correct": "corrected",
            "reject": "rejected",
        }[normalized_decision]
        decision_id = uuid4()

        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                f"SELECT id FROM {table} WHERE id = ?",
                (str(target_id),),
            ).fetchone()
            if row is None:
                raise KeyError(
                    f"Unknown {normalized_target}: {target_id}"
                )

            segment_id = (
                str(target_id)
                if normalized_target == "passage"
                else None
            )
            claim_id = (
                str(target_id)
                if normalized_target == "claim"
                else None
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
                    str(decision_id),
                    segment_id,
                    claim_id,
                    normalized_decision,
                    reviewer.strip(),
                    rationale.strip(),
                    corrected_text,
                    _utc_now_text(),
                ),
            )
            connection.execute(
                f"UPDATE {table} SET review_status = ? WHERE id = ?",
                (review_status, str(target_id)),
            )

        return decision_id

    def get_passage(self, passage_id: UUID | str) -> dict[str, Any]:
        """Return one original segment using historical passage field names."""
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    representation_id AS document_id,
                    segment_index AS passage_index,
                    text,
                    text_sha256 AS sha256,
                    review_status,
                    created_at
                FROM segments
                WHERE id = ?
                """,
                (str(passage_id),),
            ).fetchone()

        if row is None:
            raise KeyError(f"Unknown passage: {passage_id}")
        return dict(row)


ImportReceipt = _ImportReceiptCompatibilityFacade
PersistedPayloadReceipt = _PersistedPayloadReceiptCompatibilityFacade
PersistedRepresentationReceipt = _PersistedRepresentationReceiptCompatibilityFacade
AcquisitionReceipt = _AcquisitionReceiptCompatibilityFacade
PersistedClaimReceipt = _PersistedClaimReceiptCompatibilityFacade
ClaimProposalReceipt = _ClaimProposalReceiptCompatibilityFacade
PersistedAtomicClaimReceipt = _PersistedAtomicClaimReceiptCompatibilityFacade
CollectorStore = _CollectorStoreCompatibilityFacade
