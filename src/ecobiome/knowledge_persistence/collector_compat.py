"""CollectorStore compatibility facade over Schema V4.

This compatibility facade preserves the current CollectorStore public method surface while
using exactly one Schema V4 SQLite database plus the validated SHA-256 CAS.
It does not migrate or adopt legacy CollectorStore databases.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from ecobiome.knowledge_acquisition.migration_v2 import MigrationResult

from .artifact_store import FilesystemContentAddressedArtifactStore
from .config import PersistenceConfig
from .sqlite_store import initialize_database

_COMPAT_SCHEMA_VERSION = 2
_VALID_REVIEW_TARGETS = {"passage", "claim"}
_VALID_REVIEW_DECISIONS = {"accept", "correct", "reject"}
_REVIEW_STATUS = {
    "accept": "accepted",
    "correct": "corrected",
    "reject": "rejected",
}


def _utc_now_text() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_sha(value: object) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _text(value: object | None) -> str:
    return "" if value is None else str(value)


def _enum_value(value: object) -> str:
    candidate = getattr(value, "value", value)
    return str(candidate)


def _decimal_text(value: object | None) -> str | None:
    if value is None:
        return None
    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError("Time anchor must be finite")
    normalized = format(decimal.normalize(), "f")
    return "0" if normalized in {"-0", ""} else normalized


def _float_or_none(value: object | None) -> float | None:
    if value is None:
        return None
    return float(str(value))


@dataclass(frozen=True, slots=True)
class ImportReceipt:
    job_id: UUID
    source_id: UUID
    document_id: UUID
    document_sha256: str
    stored_document_path: Path
    passage_ids: tuple[UUID, ...]
    passage_review_statuses: tuple[str, ...]
    duplicate_document: bool


@dataclass(frozen=True, slots=True)
class PersistedPayloadReceipt:
    logical_key: str
    raw_artifact_id: UUID
    sha256: str
    stored_path: Path


@dataclass(frozen=True, slots=True)
class PersistedRepresentationReceipt:
    logical_key: str
    representation_id: UUID
    sha256: str
    stored_path: Path
    segment_ids: tuple[UUID, ...]
    segment_review_statuses: tuple[str, ...]
    duplicate: bool


@dataclass(frozen=True, slots=True)
class AcquisitionReceipt:
    job_id: UUID
    source_id: UUID
    payloads: tuple[PersistedPayloadReceipt, ...]
    representations: tuple[PersistedRepresentationReceipt, ...]


@dataclass(frozen=True, slots=True)
class PersistedClaimReceipt:
    claim_id: UUID
    evidence_ids: tuple[UUID, ...]
    duplicate: bool


@dataclass(frozen=True, slots=True)
class ClaimProposalReceipt:
    representation_id: UUID
    claims: tuple[PersistedClaimReceipt, ...]


@dataclass(frozen=True, slots=True)
class PersistedAtomicClaimReceipt:
    source_claim_id: UUID
    claim_id: UUID
    evidence_ids: tuple[UUID, ...]
    duplicate: bool


class CollectorStoreCompatibilityFacade:
    """Current CollectorStore behavior projected onto Schema V4."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.artifact_directory = self.database_path.with_name(
            f"{self.database_path.stem}.cas"
        )
        # Historical attributes retained for callers that inspect them.
        self.document_directory = self.artifact_directory
        self.backup_directory = self.database_path.with_name(
            f"{self.database_path.stem}.backups"
        )
        self._last_migration_result: MigrationResult | None = None

    def _repo_root(self) -> Path | None:
        explicit = os.environ.get("ECOBIOME_REPO_ROOT", "").strip()
        if explicit:
            root = Path(explicit).expanduser().resolve()
            if (root / "pyproject.toml").is_file():
                return root
            raise RuntimeError("ECOBIOME_REPO_ROOT is not an EcoBiome repository")

        candidate = Path.cwd().resolve()
        for parent in (candidate, *candidate.parents):
            if (parent / "pyproject.toml").is_file() and (parent / ".git").exists():
                return parent
        return None

    def _config(self) -> PersistenceConfig:
        return PersistenceConfig(
            database_path=self.database_path,
            artifact_store_root=self.artifact_directory,
        )

    def _artifact_store(self) -> FilesystemContentAddressedArtifactStore:
        return FilesystemContentAddressedArtifactStore(self.artifact_directory)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.initialize()
        connection = sqlite3.connect(str(self.database_path), timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=FULL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _cas_path(self, key: str) -> Path:
        if not key.startswith("sha256:"):
            raise RuntimeError("Unsupported CAS key")
        digest = key[7:]
        return (
            self.artifact_directory
            / "sha256"
            / digest[:2]
            / digest[2:4]
            / f"{digest}.blob"
        )

    def initialize(self) -> None:
        initialize_database(self._config(), repo_root=self._repo_root())
        self._last_migration_result = MigrationResult(
            schema_version=_COMPAT_SCHEMA_VERSION,
            migrated=False,
            backup_directory=None,
        )

    @property
    def last_migration_result(self) -> MigrationResult | None:
        # Schema V4 intentionally refuses legacy database migration/adoption.
        return self._last_migration_result

    def schema_version(self) -> int:
        # Compatibility API version remains the CollectorStore v2 surface.
        self.initialize()
        return _COMPAT_SCHEMA_VERSION

    def _source_identity(self, source_type: str, locator: str) -> str:
        return _canonical_sha(
            {"source_type": source_type, "canonical_locator": locator}
        )

    def _find_source(
        self,
        connection: sqlite3.Connection,
        *,
        source_type: str,
        canonical_locator: str,
    ) -> sqlite3.Row | None:
        identity = self._source_identity(source_type, canonical_locator)
        rows = connection.execute(
            """
            SELECT *
            FROM knowledge_sources
            WHERE logical_identity_sha256=?
            ORDER BY created_at, id
            """,
            (identity,),
        ).fetchall()
        if len(rows) > 1:
            raise RuntimeError("Logical source identity collision in Schema V4")
        return rows[0] if rows else None

    def _insert_source(
        self,
        connection: sqlite3.Connection,
        *,
        source_id: UUID,
        source_type: str,
        canonical_locator: str,
        title: str,
        author: str,
        language: str,
        description: str,
        imported_at: str,
        metadata: object,
        created_at: str,
    ) -> UUID:
        connection.execute(
            """
            INSERT INTO knowledge_sources(
                id, source_type, canonical_locator, title, author, language,
                description, imported_at, source_metadata_json,
                logical_identity_sha256, created_at
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(source_id),
                source_type,
                canonical_locator,
                title,
                author or None,
                language,
                description,
                imported_at,
                _canonical_json(metadata),
                self._source_identity(source_type, canonical_locator),
                created_at,
            ),
        )
        return source_id

    def begin_acquisition_job(
        self,
        *,
        requested_locator: str,
        job_kind: str,
        adapter_name: str,
        adapter_version: str,
    ) -> UUID:
        self.initialize()
        job_id = uuid4()
        now = _utc_now_text()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO acquisition_jobs(
                    id, source_id, adapter_name, adapter_version,
                    requested_locator, requested_language,
                    preferred_languages_json, maximum_input_bytes,
                    outcome, request_json, diagnostics_json,
                    started_at, completed_at, created_at
                )
                VALUES (?,NULL,?,?,?,NULL,'[]',NULL,'running',?,'[]',?,NULL,?)
                """,
                (
                    str(job_id),
                    adapter_name,
                    adapter_version,
                    requested_locator,
                    _canonical_json({"job_kind": job_kind}),
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
        diagnostics: Sequence[Any] = (),
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        if status not in {"succeeded", "partial", "failed", "cancelled"}:
            raise ValueError(f"Unsupported acquisition job status: {status}")
        completed = _utc_now_text()
        with self._connection() as connection:
            row = connection.execute(
                "SELECT diagnostics_json FROM acquisition_jobs WHERE id=?",
                (str(job_id),),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown acquisition job: {job_id}")
            existing = json.loads(str(row["diagnostics_json"] or "[]"))
            if not isinstance(existing, list):
                raise TypeError("Malformed acquisition diagnostics_json")
            for diagnostic in diagnostics:
                existing.append(
                    {
                        "severity": _text(getattr(diagnostic, "severity", "")),
                        "code": _text(getattr(diagnostic, "code", "")),
                        "message": _text(getattr(diagnostic, "message", "")),
                        "details": getattr(diagnostic, "details", {}) or {},
                        "created_at": completed,
                    }
                )
            if error_code is not None:
                existing.append(
                    {
                        "severity": "error",
                        "code": error_code,
                        "message": error_message or "",
                        "details": {},
                        "created_at": completed,
                    }
                )
            connection.execute(
                """
                UPDATE acquisition_jobs
                SET outcome=?, completed_at=?, source_id=?, diagnostics_json=?
                WHERE id=?
                """,
                (
                    status,
                    completed,
                    str(source_id) if source_id is not None else None,
                    _canonical_json(existing),
                    str(job_id),
                ),
            )

    def _put_path(self, source_path: Path) -> tuple[str, str, int, Path]:
        raw = source_path.read_bytes()
        stored = self._artifact_store().put(raw)
        verified = self._artifact_store().verify(stored.key)
        if stored != verified:
            raise RuntimeError("CAS verification mismatch")
        return stored.key, stored.sha256, stored.size_bytes, self._cas_path(stored.key)

    def _next_retrieval_index(
        self,
        connection: sqlite3.Connection,
        job_id: UUID | str,
    ) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(retrieval_index),-1)+1 FROM retrievals "
            "WHERE acquisition_job_id=?",
            (str(job_id),),
        ).fetchone()
        return int(row[0])

    def persist_acquisition_result(
        self,
        *,
        job_id: UUID,
        result: Any,
        adapter_name: str,
        adapter_version: str,
        maximum_passage_characters: int,
    ) -> AcquisitionReceipt:
        if maximum_passage_characters <= 0:
            raise ValueError(
                "maximum_passage_characters must be greater than zero"
            )
        self.initialize()
        source = result.canonical_source

        payload_state: dict[str, tuple[str, str, int, Path]] = {}
        for payload in result.payloads:
            payload_state[payload.logical_key] = self._put_path(
                Path(payload.staged_path)
            )
        representation_state: dict[str, tuple[str, str, int, Path]] = {}
        for representation in result.representations:
            representation_state[representation.logical_key] = self._put_path(
                Path(representation.staged_path)
            )

        payload_receipts: list[PersistedPayloadReceipt] = []
        representation_receipts: list[PersistedRepresentationReceipt] = []

        with self._connection() as connection:
            job = connection.execute(
                """
                SELECT outcome, adapter_name, adapter_version
                FROM acquisition_jobs WHERE id=?
                """,
                (str(job_id),),
            ).fetchone()
            if job is None:
                raise KeyError(f"Unknown acquisition job: {job_id}")
            if str(job["outcome"]) != "running":
                raise RuntimeError(
                    "Acquisition result can only persist into a running job."
                )
            if (
                str(job["adapter_name"]) != adapter_name
                or str(job["adapter_version"]) != adapter_version
            ):
                raise RuntimeError(
                    "Acquisition job adapter identity changed before persist."
                )

            source_row = self._find_source(
                connection,
                source_type=str(source.source_type),
                canonical_locator=str(source.canonical_locator),
            )
            now = _utc_now_text()
            if source_row is None:
                source_id = self._insert_source(
                    connection,
                    source_id=uuid4(),
                    source_type=str(source.source_type),
                    canonical_locator=str(source.canonical_locator),
                    title=str(source.title),
                    author=str(source.author or ""),
                    language=str(source.language or ""),
                    description="",
                    imported_at=now,
                    metadata=source.metadata,
                    created_at=now,
                )
            else:
                source_id = UUID(str(source_row["id"]))

            raw_id_by_key: dict[str, UUID] = {}
            for payload in result.payloads:
                store_key, digest, size_bytes, stored_path = payload_state[
                    payload.logical_key
                ]
                retrieval_id = uuid4()
                retrieval_index = self._next_retrieval_index(
                    connection, job_id
                )
                created = _utc_now_text()
                connection.execute(
                    """
                    INSERT INTO retrievals(
                        id, acquisition_job_id, retrieval_index,
                        retrieval_method, requested_locator, resolved_locator,
                        retrieved_at, transport_status,
                        transport_metadata_json, created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        str(retrieval_id),
                        str(job_id),
                        retrieval_index,
                        str(payload.protocol),
                        str(payload.original_locator),
                        str(payload.canonical_locator),
                        created,
                        str(payload.protocol),
                        _canonical_json(
                            {
                                "request_metadata": payload.request_metadata,
                                "response_metadata": payload.response_metadata,
                                "adapter_name": adapter_name,
                                "adapter_version": adapter_version,
                            }
                        ),
                        created,
                    ),
                )
                raw_id = uuid4()
                connection.execute(
                    """
                    INSERT INTO raw_artifacts(
                        id, retrieval_id, payload_role, media_type,
                        size_bytes, content_sha256, artifact_store_key,
                        license_id, license_evidence_locator,
                        materialization_policy, immutable, created_at
                    )
                    VALUES (?,?,?,?,?,?,?,NULL,NULL,'materialized',1,?)
                    """,
                    (
                        str(raw_id),
                        str(retrieval_id),
                        str(payload.logical_key),
                        str(payload.media_type),
                        size_bytes,
                        digest,
                        store_key,
                        created,
                    ),
                )
                raw_id_by_key[payload.logical_key] = raw_id
                payload_receipts.append(
                    PersistedPayloadReceipt(
                        logical_key=str(payload.logical_key),
                        raw_artifact_id=raw_id,
                        sha256=digest,
                        stored_path=stored_path,
                    )
                )

            for representation in result.representations:
                store_key, digest, _, stored_path = representation_state[
                    representation.logical_key
                ]
                existing = connection.execute(
                    """
                    SELECT *
                    FROM representations
                    WHERE source_id=? AND representation_kind=?
                      AND content_sha256=?
                    ORDER BY created_at,id
                    """,
                    (
                        str(source_id),
                        str(representation.representation_kind),
                        digest,
                    ),
                ).fetchall()
                if len(existing) > 1:
                    raise RuntimeError("Representation identity collision in V4")
                duplicate = bool(existing)
                parent_raw_id = raw_id_by_key[representation.parent_payload_key]
                created = _utc_now_text()

                if not existing:
                    representation_id = uuid4()
                    connection.execute(
                        """
                        INSERT INTO representations(
                            id, source_id, origin_raw_artifact_id, logical_key,
                            representation_kind, media_type, language,
                            content_sha256, artifact_store_key,
                            materialization_status, metadata_json, created_at
                        )
                        VALUES (?,?,?,?,?,?,?,?,?,'materialized',?,?)
                        """,
                        (
                            str(representation_id),
                            str(source_id),
                            str(parent_raw_id),
                            str(representation.logical_key),
                            str(representation.representation_kind),
                            str(representation.media_type),
                            str(representation.language or ""),
                            digest,
                            store_key,
                            _canonical_json(representation.metadata),
                            created,
                        ),
                    )
                else:
                    representation_id = UUID(str(existing[0]["id"]))
                    if str(existing[0]["artifact_store_key"] or "") != store_key:
                        raise RuntimeError(
                            "Duplicate representation points to unexpected CAS key"
                        )

                parameters_json = _canonical_json(
                    representation.derivation_parameters
                )
                derivation = connection.execute(
                    """
                    SELECT id FROM derivations
                    WHERE child_representation_id=?
                      AND parent_raw_artifact_id=?
                      AND parent_representation_id IS NULL
                      AND derivation_method=?
                      AND COALESCE(tool_name,'')=?
                      AND COALESCE(tool_version,'')=?
                      AND parameters_json=?
                    """,
                    (
                        str(representation_id),
                        str(parent_raw_id),
                        str(representation.derivation_method),
                        str(representation.tool_name or ""),
                        str(representation.tool_version or ""),
                        parameters_json,
                    ),
                ).fetchone()
                if derivation is None:
                    connection.execute(
                        """
                        INSERT INTO derivations(
                            id, child_representation_id, parent_raw_artifact_id,
                            parent_representation_id, derivation_method,
                            tool_name, tool_version, parameters_json, created_at
                        )
                        VALUES (?,?,?,NULL,?,?,?,?,?)
                        """,
                        (
                            str(uuid4()),
                            str(representation_id),
                            str(parent_raw_id),
                            str(representation.derivation_method),
                            str(representation.tool_name or ""),
                            str(representation.tool_version or ""),
                            parameters_json,
                            created,
                        ),
                    )

                explicit_segments = tuple(representation.segments)
                if explicit_segments:
                    segments = explicit_segments
                elif representation.text is not None:
                    from ecobiome.knowledge_acquisition.processing import (
                        split_into_passages,
                    )
                    passages = split_into_passages(
                        representation.text,
                        maximum_characters=maximum_passage_characters,
                    )
                    # Use light compatibility objects without requiring the
                    # acquisition module at import time.
                    segments = tuple(
                        type(
                            "_Segment",
                            (),
                            {
                                "text": passage,
                                "start_char": None,
                                "end_char": None,
                                "start_seconds": None,
                                "end_seconds": None,
                                "page_number": None,
                                "frame_start": None,
                                "frame_end": None,
                                "metadata": {"origin": "acquire"},
                            },
                        )()
                        for passage in passages
                    )
                else:
                    segments = ()

                stored_rows = connection.execute(
                    """
                    SELECT *
                    FROM segments
                    WHERE representation_id=?
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
                    statuses: list[str] = []
                    for index, (row, segment) in enumerate(
                        zip(stored_rows, segments, strict=True),
                        start=1,
                    ):
                        expected_sha = _sha256_bytes(
                            str(segment.text).encode("utf-8")
                        )
                        if (
                            int(row["segment_index"]) != index
                            or str(row["text_inline"] or "") != str(segment.text)
                            or str(row["text_sha256"]) != expected_sha
                            or row["representation_char_start"]
                            != segment.start_char
                            or row["representation_char_end"]
                            != segment.end_char
                            or row["start_seconds_decimal"]
                            != _decimal_text(segment.start_seconds)
                            or row["end_seconds_decimal"]
                            != _decimal_text(segment.end_seconds)
                            or row["page_number"] != segment.page_number
                            or row["frame_start"] != segment.frame_start
                            or row["frame_end"] != segment.frame_end
                            or _canonical_json(
                                json.loads(str(row["metadata_json"] or "{}"))
                            )
                            != _canonical_json(segment.metadata)
                        ):
                            raise RuntimeError(
                                "Deterministic segment content/anchors changed "
                                "for an already persisted representation."
                            )
                        segment_ids.append(UUID(str(row["id"])))
                        statuses.append(str(row["review_status"] or "pending"))
                else:
                    segment_ids = []
                    statuses = []
                    for index, segment in enumerate(segments, start=1):
                        segment_id = uuid4()
                        segment_ids.append(segment_id)
                        statuses.append("pending")
                        connection.execute(
                            """
                            INSERT INTO segments(
                                id, representation_id, segment_index,
                                text_inline, text_sha256,
                                materialization_status,
                                representation_char_start,
                                representation_char_end,
                                start_seconds_decimal, end_seconds_decimal,
                                page_number, frame_start, frame_end,
                                review_status, metadata_json, created_at
                            )
                            VALUES (?,?,?,?,?,'inline',?,?,?,?,?,?,?,
                                    'pending',?,?)
                            """,
                            (
                                str(segment_id),
                                str(representation_id),
                                index,
                                str(segment.text),
                                _sha256_bytes(
                                    str(segment.text).encode("utf-8")
                                ),
                                segment.start_char,
                                segment.end_char,
                                _decimal_text(segment.start_seconds),
                                _decimal_text(segment.end_seconds),
                                segment.page_number,
                                segment.frame_start,
                                segment.frame_end,
                                _canonical_json(segment.metadata),
                                created,
                            ),
                        )

                representation_receipts.append(
                    PersistedRepresentationReceipt(
                        logical_key=str(representation.logical_key),
                        representation_id=representation_id,
                        sha256=digest,
                        stored_path=stored_path,
                        segment_ids=tuple(segment_ids),
                        segment_review_statuses=tuple(statuses),
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
        imported: Any,
        *,
        transcript_path: str | Path,
        passages: tuple[str, ...],
    ) -> ImportReceipt:
        self.initialize()
        path = Path(transcript_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        raw = path.read_bytes()
        document_sha256 = _sha256_bytes(raw)
        source_type = _enum_value(imported.source.source_type)
        source_locator = _text(imported.source.locator)

        job_id = self.begin_acquisition_job(
            requested_locator=source_locator,
            job_kind=f"{source_type}_transcript_import",
            adapter_name="manual-transcript-import",
            adapter_version="2",
        )
        source_id: UUID | None = None
        document_id: UUID | None = None
        try:
            stored = self._artifact_store().put(raw)
            self._artifact_store().verify(stored.key)
            stored_path = self._cas_path(stored.key)
            now = _utc_now_text()

            with self._connection() as connection:
                source_row = self._find_source(
                    connection,
                    source_type=source_type,
                    canonical_locator=source_locator,
                )
                if source_row is None:
                    source_id = self._insert_source(
                        connection,
                        source_id=UUID(str(imported.source.id)),
                        source_type=source_type,
                        canonical_locator=source_locator,
                        title=_text(imported.source.title),
                        author=_text(imported.source.author),
                        language=_text(imported.source.language),
                        description=_text(imported.source.description),
                        imported_at=imported.source.imported_at.isoformat(),
                        metadata={
                            "review_status": _enum_value(
                                getattr(imported.source, "review_status", "imported")
                            )
                        },
                        created_at=imported.source.imported_at.isoformat(),
                    )
                else:
                    source_id = UUID(str(source_row["id"]))

                retrieval_id = uuid4()
                connection.execute(
                    """
                    INSERT INTO retrievals(
                        id, acquisition_job_id, retrieval_index,
                        retrieval_method, requested_locator, resolved_locator,
                        retrieved_at, transport_status,
                        transport_metadata_json, created_at
                    )
                    VALUES (?,?,0,'file',?,?,?,'file','{}',?)
                    """,
                    (
                        str(retrieval_id),
                        str(job_id),
                        str(path),
                        source_locator,
                        now,
                        now,
                    ),
                )
                raw_artifact_id = uuid4()
                connection.execute(
                    """
                    INSERT INTO raw_artifacts(
                        id, retrieval_id, payload_role, media_type, size_bytes,
                        content_sha256, artifact_store_key, license_id,
                        license_evidence_locator, materialization_policy,
                        immutable, created_at
                    )
                    VALUES (?,?,'manual_transcript','text/plain; charset=utf-8',
                            ?,?,?,NULL,NULL,'materialized',1,?)
                    """,
                    (
                        str(raw_artifact_id),
                        str(retrieval_id),
                        len(raw),
                        document_sha256,
                        stored.key,
                        now,
                    ),
                )

                existing = connection.execute(
                    """
                    SELECT * FROM representations
                    WHERE source_id=? AND representation_kind='transcript'
                      AND content_sha256=?
                    ORDER BY created_at,id
                    """,
                    (str(source_id), document_sha256),
                ).fetchall()
                if len(existing) > 1:
                    raise RuntimeError("Transcript representation identity collision")
                duplicate_document = bool(existing)
                if not existing:
                    document_id = uuid4()
                    connection.execute(
                        """
                        INSERT INTO representations(
                            id, source_id, origin_raw_artifact_id, logical_key,
                            representation_kind, media_type, language,
                            content_sha256, artifact_store_key,
                            materialization_status, metadata_json, created_at
                        )
                        VALUES (?,?,?,?,'transcript',
                                'text/plain; charset=utf-8',?,?,?,
                                'materialized',?,?)
                        """,
                        (
                            str(document_id),
                            str(source_id),
                            str(raw_artifact_id),
                            f"manual-transcript:{source_id}:{document_sha256}",
                            _text(imported.source.language),
                            document_sha256,
                            stored.key,
                            _canonical_json(
                                {
                                    "original_path": str(path),
                                    "character_count": len(imported.text),
                                    "compatibility_name": "document",
                                }
                            ),
                            now,
                        ),
                    )
                else:
                    document_id = UUID(str(existing[0]["id"]))
                    if str(existing[0]["artifact_store_key"] or "") != stored.key:
                        raise RuntimeError(
                            "Duplicate transcript points to unexpected CAS key"
                        )

                derivation = connection.execute(
                    """
                    SELECT id FROM derivations
                    WHERE child_representation_id=?
                      AND parent_raw_artifact_id=?
                      AND parent_representation_id IS NULL
                      AND derivation_method='identity'
                    """,
                    (str(document_id), str(raw_artifact_id)),
                ).fetchone()
                if derivation is None:
                    connection.execute(
                        """
                        INSERT INTO derivations(
                            id, child_representation_id, parent_raw_artifact_id,
                            parent_representation_id, derivation_method,
                            tool_name, tool_version, parameters_json, created_at
                        )
                        VALUES (?,?,?,NULL,'identity',
                                'manual-transcript-import','2','{}',?)
                        """,
                        (
                            str(uuid4()),
                            str(document_id),
                            str(raw_artifact_id),
                            now,
                        ),
                    )

                stored_rows = connection.execute(
                    "SELECT * FROM segments WHERE representation_id=? "
                    "ORDER BY segment_index",
                    (str(document_id),),
                ).fetchall()
                if stored_rows:
                    if len(stored_rows) != len(passages):
                        raise RuntimeError(
                            "Deterministic passage count changed for an "
                            "already persisted transcript."
                        )
                    passage_ids = []
                    passage_statuses = []
                    for index, (row, passage) in enumerate(
                        zip(stored_rows, passages, strict=True),
                        start=1,
                    ):
                        if (
                            int(row["segment_index"]) != index
                            or str(row["text_inline"] or "") != passage
                            or str(row["text_sha256"])
                            != _sha256_bytes(passage.encode("utf-8"))
                        ):
                            raise RuntimeError(
                                "Deterministic passage content changed for an "
                                "already persisted transcript."
                            )
                        passage_ids.append(UUID(str(row["id"])))
                        passage_statuses.append(
                            str(row["review_status"] or "pending")
                        )
                else:
                    passage_ids = []
                    passage_statuses = []
                    for index, passage in enumerate(passages, start=1):
                        passage_id = uuid4()
                        passage_ids.append(passage_id)
                        passage_statuses.append("pending")
                        connection.execute(
                            """
                            INSERT INTO segments(
                                id, representation_id, segment_index,
                                text_inline, text_sha256,
                                materialization_status,
                                representation_char_start,
                                representation_char_end,
                                start_seconds_decimal, end_seconds_decimal,
                                page_number, frame_start, frame_end,
                                review_status, metadata_json, created_at
                            )
                            VALUES (?,?,?,?,?,'inline',NULL,NULL,NULL,NULL,
                                    NULL,NULL,NULL,'pending',?,?)
                            """,
                            (
                                str(passage_id),
                                str(document_id),
                                index,
                                passage,
                                _sha256_bytes(passage.encode("utf-8")),
                                _canonical_json(
                                    {"compatibility_name": "passage"}
                                ),
                                now,
                            ),
                        )

            assert source_id is not None
            assert document_id is not None
            self.finish_acquisition_job(
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
                passage_review_statuses=tuple(passage_statuses),
                duplicate_document=duplicate_document,
            )
        except Exception as exc:
            self.finish_acquisition_job(
                job_id,
                status="failed",
                source_id=source_id,
                error_code="import_failed",
                error_message=f"{type(exc).__name__}: {exc}",
            )
            raise

    def _claim_review_status(
        self,
        connection: sqlite3.Connection,
        claim_id: str,
        initial: str | None,
    ) -> str:
        row = connection.execute(
            """
            SELECT decision
            FROM claim_review_events
            WHERE claim_id=?
            ORDER BY reviewed_at DESC,id DESC
            LIMIT 1
            """,
            (claim_id,),
        ).fetchone()
        if row is None:
            return initial or "pending"
        return _REVIEW_STATUS[str(row["decision"])]

    def _effective_claim_text(
        self,
        connection: sqlite3.Connection,
        *,
        claim_id: str,
        original_text: str,
    ) -> str:
        row = connection.execute(
            """
            SELECT corrected_text
            FROM claim_review_events
            WHERE claim_id=? AND corrected_text IS NOT NULL
            ORDER BY reviewed_at DESC,id DESC
            LIMIT 1
            """,
            (claim_id,),
        ).fetchone()
        return original_text if row is None else str(row["corrected_text"])

    def propose_source_statement_claims(
        self,
        *,
        representation_id: UUID | str,
        limit: int = 50,
        maximum_claim_characters: int = 350,
        maximum_window_seconds: float = 15.0,
    ) -> ClaimProposalReceipt:
        self.initialize()
        representation_text = str(representation_id)
        from ecobiome.knowledge_acquisition.claim_candidates import (
            ClaimSegment,
            build_source_statement_candidates,
        )

        with self._connection() as connection:
            representation = connection.execute(
                "SELECT id,source_id FROM representations WHERE id=?",
                (representation_text,),
            ).fetchone()
            if representation is None:
                raise KeyError(f"Unknown representation: {representation_id}")

            rows = connection.execute(
                """
                SELECT
                    s.*,
                    (
                        SELECT e.corrected_text
                        FROM segment_review_events e
                        WHERE e.segment_id=s.id
                          AND e.corrected_text IS NOT NULL
                        ORDER BY e.reviewed_at DESC,e.id DESC
                        LIMIT 1
                    ) AS corrected_text
                FROM segments s
                WHERE s.representation_id=?
                ORDER BY s.segment_index
                """,
                (representation_text,),
            ).fetchall()
            segments = tuple(
                ClaimSegment(
                    id=str(row["id"]),
                    segment_index=int(row["segment_index"]),
                    text=str(row["text_inline"] or ""),
                    effective_text=(
                        str(row["corrected_text"])
                        if row["corrected_text"] is not None
                        else str(row["text_inline"] or "")
                    ),
                    review_status=str(row["review_status"] or "pending"),
                    start_seconds=_float_or_none(row["start_seconds_decimal"]),
                    end_seconds=_float_or_none(row["end_seconds_decimal"]),
                    page_number=row["page_number"],
                    frame_start=row["frame_start"],
                    frame_end=row["frame_end"],
                    correction_applied=row["corrected_text"] is not None,
                )
                for row in rows
                if str(row["text_inline"] or "")
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
                metadata_json = _canonical_json(candidate.metadata)
                existing = connection.execute(
                    """
                    SELECT id FROM source_claims
                    WHERE claim_layer='extracted'
                      AND claim_kind=?
                      AND claim_text=?
                      AND qualifiers_json=?
                    """,
                    (
                        candidate.claim_kind,
                        candidate.text,
                        metadata_json,
                    ),
                ).fetchone()
                if existing is not None:
                    claim_id = UUID(str(existing["id"]))
                    links = connection.execute(
                        """
                        SELECT evidence_id FROM claim_evidence_links
                        WHERE claim_id=?
                        ORDER BY evidence_order,evidence_id
                        """,
                        (str(claim_id),),
                    ).fetchall()
                    if len(links) != len(candidate.evidence):
                        raise RuntimeError(
                            "Existing candidate Claim has inconsistent Evidence."
                        )
                    receipts.append(
                        PersistedClaimReceipt(
                            claim_id=claim_id,
                            evidence_ids=tuple(
                                UUID(str(row["evidence_id"])) for row in links
                            ),
                            duplicate=True,
                        )
                    )
                    continue

                claim_id = uuid4()
                claim_sha = _sha256_bytes(candidate.text.encode("utf-8"))
                connection.execute(
                    """
                    INSERT INTO source_claims(
                        id, source_id, representation_id, parent_claim_id,
                        claim_layer, claim_text, claim_text_sha256, claim_kind,
                        semantic_type, qualifiers_json,
                        extraction_confidence_decimal,
                        source_claim_effective_text_sha256, notes,
                        initial_review_status, created_at
                    )
                    VALUES (?,?,?,NULL,'extracted',?,?,?,NULL,?,NULL,?,
                            '','pending',?)
                    """,
                    (
                        str(claim_id),
                        str(representation["source_id"]),
                        representation_text,
                        candidate.text,
                        claim_sha,
                        candidate.claim_kind,
                        metadata_json,
                        claim_sha,
                        now,
                    ),
                )
                evidence_ids: list[UUID] = []
                for order, item in enumerate(candidate.evidence):
                    segment = connection.execute(
                        "SELECT text_inline FROM segments WHERE id=?",
                        (item.segment_id,),
                    ).fetchone()
                    if segment is None:
                        raise RuntimeError("Candidate Evidence segment missing")
                    original = str(segment["text_inline"] or "")
                    start = int(item.segment_char_start)
                    end = int(item.segment_char_end)
                    if not 0 <= start < end <= len(original):
                        raise RuntimeError("Candidate Evidence anchor invalid")
                    source_text = original[start:end]
                    if source_text != item.evidence_text:
                        raise RuntimeError(
                            "Corrected segment text must never become source Evidence"
                        )
                    evidence_sha = _sha256_bytes(source_text.encode("utf-8"))
                    existing_evidence = connection.execute(
                        """
                        SELECT id FROM source_evidence
                        WHERE segment_id=? AND segment_char_start=?
                          AND segment_char_end=? AND evidence_text_sha256=?
                        """,
                        (
                            item.segment_id,
                            start,
                            end,
                            evidence_sha,
                        ),
                    ).fetchone()
                    if existing_evidence is None:
                        evidence_id = uuid4()
                        connection.execute(
                            """
                            INSERT INTO source_evidence(
                                id, segment_id, segment_char_start,
                                segment_char_end, evidence_text_sha256,
                                start_seconds_decimal, end_seconds_decimal,
                                page_number, frame_start, frame_end,
                                evidence_metadata_json, created_at
                            )
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                            """,
                            (
                                str(evidence_id),
                                item.segment_id,
                                start,
                                end,
                                evidence_sha,
                                _decimal_text(item.start_seconds),
                                _decimal_text(item.end_seconds),
                                item.page_number,
                                item.frame_start,
                                item.frame_end,
                                _canonical_json(
                                    {
                                        "role": "verbatim_source_segment",
                                        "extractor":
                                            "source-statement-window-v1",
                                    }
                                ),
                                now,
                            ),
                        )
                    else:
                        evidence_id = UUID(str(existing_evidence["id"]))
                    connection.execute(
                        """
                        INSERT INTO claim_evidence_links(
                            claim_id,evidence_id,evidence_order,link_role,created_at
                        )
                        VALUES (?,?,?,'supports_source_claim',?)
                        """,
                        (str(claim_id), str(evidence_id), order, now),
                    )
                    evidence_ids.append(evidence_id)
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

    def persist_atomic_claim_batch(
        self,
        batch: Any,
    ) -> tuple[PersistedAtomicClaimReceipt, ...]:
        self.initialize()
        receipts: list[PersistedAtomicClaimReceipt] = []
        with self._connection() as connection:
            for proposal in batch.proposals:
                if proposal.qualifiers.get("benchmark_only") is True:
                    raise ValueError(
                        "Benchmark-only semantic proposals cannot be persisted."
                    )
                parent = connection.execute(
                    "SELECT * FROM source_claims WHERE id=?",
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
                parent_status = self._claim_review_status(
                    connection,
                    proposal.source_claim_id,
                    parent["initial_review_status"],
                )
                if parent_status == "rejected":
                    raise ValueError(
                        "Rejected source_statement Claims cannot produce "
                        "atomic propositions."
                    )
                effective = self._effective_claim_text(
                    connection,
                    claim_id=proposal.source_claim_id,
                    original_text=str(parent["claim_text"]),
                )
                effective_hash = _sha256_bytes(effective.encode("utf-8"))
                if (
                    effective_hash
                    != proposal.source_claim_effective_text_sha256
                ):
                    raise ValueError(
                        "Semantic proposal is stale: source Claim effective "
                        "text SHA-256 no longer matches."
                    )

                selected: list[sqlite3.Row] = []
                for evidence_id in proposal.evidence_ids:
                    row = connection.execute(
                        """
                        SELECT
                            e.*, s.text_inline,
                            s.review_status AS segment_review_status
                        FROM claim_evidence_links l
                        JOIN source_evidence e ON e.id=l.evidence_id
                        JOIN segments s ON s.id=e.segment_id
                        WHERE l.claim_id=? AND l.evidence_id=?
                        """,
                        (proposal.source_claim_id, evidence_id),
                    ).fetchone()
                    if row is None:
                        raise ValueError(
                            "Semantic proposal references Evidence that does "
                            "not belong to its source Claim."
                        )
                    if str(row["segment_review_status"] or "pending") == "rejected":
                        raise ValueError(
                            "Semantic proposal references Evidence from a "
                            "rejected Segment."
                        )
                    original = str(row["text_inline"] or "")
                    evidence_text = original[
                        int(row["segment_char_start"]):
                        int(row["segment_char_end"])
                    ]
                    if (
                        _sha256_bytes(evidence_text.encode("utf-8"))
                        != str(row["evidence_text_sha256"])
                    ):
                        raise RuntimeError(
                            "Persisted parent Evidence SHA-256 is inconsistent."
                        )
                    selected.append(row)

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
                    _canonical_json(fingerprint_payload).encode("utf-8")
                )
                metadata = {
                    "epistemic_status":
                        "candidate_atomic_source_proposition",
                    "extractor": "semantic-claim-contract-v1",
                    "semantic_extractor_name": batch.extractor.name,
                    "semantic_extractor_version": batch.extractor.version,
                    "semantic_type": proposal.semantic_type,
                    "source_claim_id": proposal.source_claim_id,
                    "source_claim_review_status": parent_status,
                    "source_claim_effective_text_sha256": effective_hash,
                    "selected_parent_evidence_ids":
                        list(proposal.evidence_ids),
                    "qualifiers": proposal.qualifiers,
                    "candidate_fingerprint": fingerprint,
                    "automatic_scientific_acceptance": False,
                }
                metadata_json = _canonical_json(metadata)
                existing = connection.execute(
                    """
                    SELECT id FROM source_claims
                    WHERE claim_layer='atomic'
                      AND claim_kind='atomic_source_proposition'
                      AND qualifiers_json=?
                    """,
                    (metadata_json,),
                ).fetchone()
                if existing is not None:
                    claim_id = UUID(str(existing["id"]))
                    links = connection.execute(
                        """
                        SELECT evidence_id FROM claim_evidence_links
                        WHERE claim_id=?
                        ORDER BY evidence_order,evidence_id
                        """,
                        (str(claim_id),),
                    ).fetchall()
                    if len(links) != len(selected):
                        raise RuntimeError(
                            "Existing atomic Claim has inconsistent Evidence."
                        )
                    receipts.append(
                        PersistedAtomicClaimReceipt(
                            source_claim_id=UUID(proposal.source_claim_id),
                            claim_id=claim_id,
                            evidence_ids=tuple(
                                UUID(str(r["evidence_id"])) for r in links
                            ),
                            duplicate=True,
                        )
                    )
                    continue

                now = _utc_now_text()
                claim_id = uuid4()
                claim_sha = _sha256_bytes(proposal.text.encode("utf-8"))
                connection.execute(
                    """
                    INSERT INTO source_claims(
                        id,source_id,representation_id,parent_claim_id,
                        claim_layer,claim_text,claim_text_sha256,claim_kind,
                        semantic_type,qualifiers_json,
                        extraction_confidence_decimal,
                        source_claim_effective_text_sha256,notes,
                        initial_review_status,created_at
                    )
                    VALUES (?,?,?,?,'atomic',?,?,
                            'atomic_source_proposition',?,?,NULL,?,
                            '','pending',?)
                    """,
                    (
                        str(claim_id),
                        str(parent["source_id"]),
                        parent["representation_id"],
                        proposal.source_claim_id,
                        proposal.text,
                        claim_sha,
                        proposal.semantic_type,
                        metadata_json,
                        claim_sha,
                        now,
                    ),
                )
                evidence_ids: list[UUID] = []
                for order, row in enumerate(selected):
                    evidence_id = UUID(str(row["id"]))
                    connection.execute(
                        """
                        INSERT INTO claim_evidence_links(
                            claim_id,evidence_id,evidence_order,link_role,created_at
                        )
                        VALUES (?,?,?,'verbatim_parent_evidence',?)
                        """,
                        (str(claim_id), str(evidence_id), order, now),
                    )
                    evidence_ids.append(evidence_id)
                receipts.append(
                    PersistedAtomicClaimReceipt(
                        source_claim_id=UUID(proposal.source_claim_id),
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
        self.initialize()
        with self._connection() as connection:
            claim = connection.execute(
                "SELECT * FROM source_claims WHERE id=?",
                (str(claim_id),),
            ).fetchone()
            if claim is None:
                raise KeyError(f"Unknown claim: {claim_id}")
            links = connection.execute(
                """
                SELECT
                    l.evidence_order,
                    e.*,
                    s.segment_index,
                    s.text_inline,
                    s.review_status AS segment_review_status,
                    r.id AS representation_id,
                    r.representation_kind,
                    r.language AS representation_language,
                    src.id AS source_id,
                    src.source_type,
                    src.canonical_locator,
                    src.title AS source_title,
                    src.author AS source_author
                FROM claim_evidence_links l
                JOIN source_evidence e ON e.id=l.evidence_id
                JOIN segments s ON s.id=e.segment_id
                JOIN representations r ON r.id=s.representation_id
                JOIN knowledge_sources src ON src.id=r.source_id
                WHERE l.claim_id=?
                ORDER BY s.segment_index,l.evidence_order,e.created_at,e.id
                """,
                (str(claim_id),),
            ).fetchall()
            reviews = connection.execute(
                """
                SELECT id,decision,reviewer,notes,corrected_text,reviewed_at
                FROM claim_review_events
                WHERE claim_id=?
                ORDER BY reviewed_at,id
                """,
                (str(claim_id),),
            ).fetchall()
            review_status = self._claim_review_status(
                connection,
                str(claim_id),
                claim["initial_review_status"],
            )

        payload: dict[str, Any] = {
            "id": str(claim["id"]),
            "claim_kind": str(claim["claim_kind"] or ""),
            "text": str(claim["claim_text"]),
            "review_status": review_status,
            "metadata": json.loads(str(claim["qualifiers_json"] or "{}")),
            "created_at": str(claim["created_at"]),
        }
        evidence: list[dict[str, Any]] = []
        for row in links:
            original = str(row["text_inline"] or "")
            start = int(row["segment_char_start"])
            end = int(row["segment_char_end"])
            evidence_text = original[start:end]
            if (
                _sha256_bytes(evidence_text.encode("utf-8"))
                != str(row["evidence_text_sha256"])
            ):
                raise RuntimeError("Source Evidence SHA-256 mismatch")
            evidence.append(
                {
                    "id": str(row["id"]),
                    "segment_id": str(row["segment_id"]),
                    "evidence_text": evidence_text,
                    "evidence_sha256": str(row["evidence_text_sha256"]),
                    "segment_char_start": start,
                    "segment_char_end": end,
                    "start_seconds":
                        _float_or_none(row["start_seconds_decimal"]),
                    "end_seconds":
                        _float_or_none(row["end_seconds_decimal"]),
                    "page_number": row["page_number"],
                    "frame_start": row["frame_start"],
                    "frame_end": row["frame_end"],
                    "metadata": json.loads(
                        str(row["evidence_metadata_json"] or "{}")
                    ),
                    "segment_index": int(row["segment_index"]),
                    "segment_review_status":
                        str(row["segment_review_status"] or "pending"),
                    "representation_id": str(row["representation_id"]),
                    "representation_kind": str(row["representation_kind"]),
                    "representation_language": row["representation_language"],
                    "source_id": str(row["source_id"]),
                    "source_type": str(row["source_type"]),
                    "canonical_locator": str(row["canonical_locator"]),
                    "source_title": str(row["source_title"]),
                    "source_author": row["source_author"],
                }
            )
        payload["evidence"] = evidence
        history = [
            {
                "id": str(row["id"]),
                "decision": str(row["decision"]),
                "reviewer": _text(row["reviewer"]),
                "rationale": str(row["notes"] or ""),
                "corrected_text": row["corrected_text"],
                "created_at": str(row["reviewed_at"]),
            }
            for row in reviews
        ]
        payload["review_history"] = history
        corrected = next(
            (
                str(item["corrected_text"])
                for item in reversed(history)
                if item["corrected_text"] is not None
            ),
            None,
        )
        payload["effective_text"] = (
            corrected if corrected is not None else payload["text"]
        )
        payload["text_was_corrected"] = corrected is not None
        return payload

    def summary(self) -> dict[str, int]:
        self.initialize()
        with self._connection() as connection:
            count = lambda table: int(
                connection.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
            )
            diagnostics = 0
            for row in connection.execute(
                "SELECT diagnostics_json FROM acquisition_jobs"
            ):
                value = json.loads(str(row[0] or "[]"))
                if isinstance(value, list):
                    diagnostics += len(value)
            pending_claims = 0
            for row in connection.execute(
                "SELECT id,initial_review_status FROM source_claims"
            ):
                if self._claim_review_status(
                    connection, str(row["id"]), row["initial_review_status"]
                ) == "pending":
                    pending_claims += 1
            logical_raw_artifacts = int(
                connection.execute(
                    "SELECT COUNT(DISTINCT content_sha256) FROM raw_artifacts"
                ).fetchone()[0]
            )
            logical_derivations = len(
                {
                    (
                        str(row["child_representation_id"]),
                        str(row["parent_content_sha256"] or ""),
                        str(row["parent_representation_id"] or ""),
                        str(row["derivation_method"]),
                        str(row["tool_name"] or ""),
                        str(row["tool_version"] or ""),
                        str(row["parameters_json"]),
                    )
                    for row in connection.execute(
                        """
                        SELECT
                            d.child_representation_id,
                            ra.content_sha256 AS parent_content_sha256,
                            d.parent_representation_id,
                            d.derivation_method,
                            d.tool_name,
                            d.tool_version,
                            d.parameters_json
                        FROM derivations d
                        LEFT JOIN raw_artifacts ra
                          ON ra.id=d.parent_raw_artifact_id
                        """
                    )
                }
            )
            result = {
                "sources": count("knowledge_sources"),
                # Compatibility count collapses retrieval-scoped V4 rows by
                # immutable content, matching legacy CollectorStore status.
                "raw_artifacts": logical_raw_artifacts,
                "retrievals": count("retrievals"),
                "representations": count("representations"),
                "representation_derivations": logical_derivations,
                "segments": count("segments"),
                "claims": count("source_claims"),
                # Legacy evidence count represents Claim↔Evidence occurrences.
                "evidence": count("claim_evidence_links"),
                "acquisition_jobs": count("acquisition_jobs"),
                "job_diagnostics": diagnostics,
                "review_decisions":
                    count("claim_review_events")
                    + count("segment_review_events"),
            }
            result["pending_segments"] = int(
                connection.execute(
                    "SELECT COUNT(*) FROM segments "
                    "WHERE COALESCE(review_status,'pending')='pending'"
                ).fetchone()[0]
            )
            result["pending_claims"] = pending_claims
            result["failed_jobs"] = int(
                connection.execute(
                    "SELECT COUNT(*) FROM acquisition_jobs "
                    "WHERE outcome='failed'"
                ).fetchone()[0]
            )
            result["documents"] = int(
                connection.execute(
                    "SELECT COUNT(DISTINCT representation_id) FROM segments"
                ).fetchone()[0]
            )
        result["passages"] = result["segments"]
        result["collection_jobs"] = result["acquisition_jobs"]
        result["pending_passages"] = result["pending_segments"]
        result["schema_version"] = _COMPAT_SCHEMA_VERSION
        return result

    def list_pending_reviews(
        self,
        *,
        limit: int = 50,
    ) -> tuple[dict[str, Any], ...]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        self.initialize()
        items: list[dict[str, Any]] = []
        with self._connection() as connection:
            for row in connection.execute(
                """
                SELECT id,representation_id,segment_index,text_inline,
                       review_status,created_at
                FROM segments
                WHERE COALESCE(review_status,'pending')='pending'
                """
            ):
                items.append(
                    {
                        "target_type": "passage",
                        "target_id": str(row["id"]),
                        "document_id": str(row["representation_id"]),
                        "passage_index": int(row["segment_index"]),
                        "text": str(row["text_inline"] or ""),
                        "review_status": "pending",
                        "created_at": str(row["created_at"]),
                    }
                )
            for row in connection.execute(
                "SELECT id,claim_text,initial_review_status,created_at "
                "FROM source_claims"
            ):
                if self._claim_review_status(
                    connection,
                    str(row["id"]),
                    row["initial_review_status"],
                ) == "pending":
                    items.append(
                        {
                            "target_type": "claim",
                            "target_id": str(row["id"]),
                            "document_id": None,
                            "passage_index": None,
                            "text": str(row["claim_text"]),
                            "review_status": "pending",
                            "created_at": str(row["created_at"]),
                        }
                    )
        items.sort(
            key=lambda item: (
                item["created_at"],
                item["target_type"],
                item["passage_index"]
                if item["passage_index"] is not None else 10**18,
            )
        )
        return tuple(items[:limit])

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
        normalized_target = target_type.strip().lower()
        normalized_decision = decision.strip().lower()
        if normalized_target not in _VALID_REVIEW_TARGETS:
            raise ValueError("target_type must be 'passage' or 'claim'")
        if normalized_decision not in _VALID_REVIEW_DECISIONS:
            raise ValueError("decision must be accept, correct, or reject")
        if (
            normalized_decision == "correct"
            and not (corrected_text or "").strip()
        ):
            raise ValueError("A correction requires corrected_text.")
        decision_id = uuid4()
        now = _utc_now_text()
        corrected_sha = (
            _sha256_bytes(corrected_text.encode("utf-8"))
            if corrected_text is not None
            else None
        )

        with self._connection() as connection:
            if normalized_target == "passage":
                row = connection.execute(
                    "SELECT id FROM segments WHERE id=?",
                    (str(target_id),),
                ).fetchone()
                if row is None:
                    raise KeyError(f"Unknown passage: {target_id}")
                connection.execute(
                    """
                    INSERT INTO segment_review_events(
                        id,segment_id,decision,reviewer,rationale,
                        corrected_text,corrected_text_sha256,
                        review_metadata_json,reviewed_at
                    )
                    VALUES (?,?,?,?,?,?,?,'{}',?)
                    """,
                    (
                        str(decision_id),
                        str(target_id),
                        normalized_decision,
                        reviewer.strip() or None,
                        rationale.strip(),
                        corrected_text,
                        corrected_sha,
                        now,
                    ),
                )
                latest = connection.execute(
                    """
                    SELECT decision FROM segment_review_events
                    WHERE segment_id=?
                    ORDER BY reviewed_at DESC,id DESC LIMIT 1
                    """,
                    (str(target_id),),
                ).fetchone()
                if latest is not None:
                    connection.execute(
                        "UPDATE segments SET review_status=? WHERE id=?",
                        (
                            _REVIEW_STATUS[str(latest["decision"])],
                            str(target_id),
                        ),
                    )
            else:
                row = connection.execute(
                    "SELECT id FROM source_claims WHERE id=?",
                    (str(target_id),),
                ).fetchone()
                if row is None:
                    raise KeyError(f"Unknown claim: {target_id}")
                connection.execute(
                    """
                    INSERT INTO claim_review_events(
                        id,claim_id,decision,reviewer,notes,
                        corrected_text,corrected_text_sha256,
                        review_metadata_json,reviewed_at
                    )
                    VALUES (?,?,?,?,?,?,?,'{}',?)
                    """,
                    (
                        str(decision_id),
                        str(target_id),
                        normalized_decision,
                        reviewer.strip() or None,
                        rationale.strip(),
                        corrected_text,
                        corrected_sha,
                        now,
                    ),
                )
        return decision_id

    def get_passage(self, passage_id: UUID | str) -> dict[str, Any]:
        self.initialize()
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id,representation_id,segment_index,text_inline,
                       text_sha256,review_status,created_at
                FROM segments WHERE id=?
                """,
                (str(passage_id),),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown passage: {passage_id}")
        return {
            "id": str(row["id"]),
            "document_id": str(row["representation_id"]),
            "passage_index": int(row["segment_index"]),
            "text": str(row["text_inline"] or ""),
            "sha256": str(row["text_sha256"]),
            "review_status": str(row["review_status"] or "pending"),
            "created_at": str(row["created_at"]),
        }


# Prototype export uses the historical name.
CollectorStore = CollectorStoreCompatibilityFacade
