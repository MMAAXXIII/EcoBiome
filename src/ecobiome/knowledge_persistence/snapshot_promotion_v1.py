"""Candidate engine for immutable Scientific Foundation snapshot promotion.

This module is intentionally inert unless called by a later, separately
authorized gate. RATE-3C only freezes and tests this implementation.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import uuid
import xml.etree.ElementTree as ET
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ENGINE_NAME = "ecobiome-first-derived-snapshot-promotion-engine"
ENGINE_VERSION = "rate-3c-candidate-v1"

_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class SnapshotPromotionError(RuntimeError):
    """Fail-closed promotion error."""


@dataclass(frozen=True)
class PromotionAuthorization:
    """Explicit authorization supplied by a later human-reviewed gate."""

    authorization_payload_sha256: str
    snapshot_creation_authorized: bool
    derived_representation_cas_write_authorized: bool
    scientific_input_repo_head: str
    promotion_contract_repo_head: str
    promotion_engine_repo_head: str
    promotion_engine_code_identity_sha256: str


@dataclass(frozen=True)
class PromotionResult:
    """Immutable result identity returned after a successful publication."""

    database_sha256: str
    database_size_bytes: int
    manifest_sha256: str
    logical_snapshot_path: str


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_jats_text_v1(raw: bytes) -> tuple[str, list[str]]:
    root = ET.fromstring(raw)
    paragraphs: list[str] = []
    for elem in root.iter():
        if xml_local_name(elem.tag) != "p":
            continue
        text = normalize_space("".join(elem.itertext()))
        if len(text) < 30:
            continue
        paragraphs.append(text)
    if not paragraphs:
        raise SnapshotPromotionError("No JATS paragraphs extracted")
    return "\n\n".join(paragraphs), paragraphs


def locate_anchor_paragraph_v1(
    paragraphs: list[str],
    anchor_candidates: list[str],
) -> tuple[int, str]:
    candidates: list[tuple[int, int, str]] = []
    for anchor_rank, anchor in enumerate(anchor_candidates):
        folded = normalize_space(anchor).casefold()
        for paragraph_index, paragraph in enumerate(paragraphs):
            if paragraph.casefold().find(folded) >= 0:
                candidates.append((anchor_rank, paragraph_index, paragraph))
    if not candidates:
        raise SnapshotPromotionError("No configured evidence anchor found")
    candidates.sort(key=lambda item: (item[0], item[1]))
    _, paragraph_index, paragraph = candidates[0]
    return paragraph_index, paragraph


def _safe_identifier(value: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(value):
        raise SnapshotPromotionError(f"Unsafe SQL identifier: {value!r}")
    return value


def _engine_file_sha256() -> str:
    return sha256_file(Path(__file__).resolve())


def verify_authorization(
    authorization: PromotionAuthorization,
    expected_code_sha256: str,
) -> None:
    if not authorization.snapshot_creation_authorized:
        raise SnapshotPromotionError("Snapshot creation is not authorized")
    if (
        authorization.promotion_engine_code_identity_sha256
        != expected_code_sha256
    ):
        raise SnapshotPromotionError("Authorized engine code SHA mismatch")
    if _engine_file_sha256() != expected_code_sha256:
        raise SnapshotPromotionError("Executing engine file SHA mismatch")


def _resolve_protected_field(
    binding: Mapping[str, Any],
    cas: Any,
) -> str:
    resolver = binding.get("resolver")
    if resolver != "rate2h_jats_segment_text_v1":
        raise SnapshotPromotionError(
            f"Unsupported protected-field resolver: {resolver!r}"
        )
    raw_key = str(binding["raw_artifact_key"])
    raw = cas.get(raw_key)
    if sha256_bytes(raw) != binding["expected_raw_sha256"]:
        raise SnapshotPromotionError("Protected-field raw CAS SHA mismatch")

    representation, paragraphs = normalized_jats_text_v1(raw)
    if sha256_bytes(representation.encode("utf-8")) != binding[
        "expected_representation_sha256"
    ]:
        raise SnapshotPromotionError("Derived representation SHA mismatch")

    paragraph_index, paragraph = locate_anchor_paragraph_v1(
        paragraphs,
        list(binding["anchor_candidates"]),
    )
    if paragraph_index != binding["expected_paragraph_index"]:
        raise SnapshotPromotionError("Protected paragraph index drift")
    if sha256_bytes(paragraph.encode("utf-8")) != binding[
        "expected_segment_text_sha256"
    ]:
        raise SnapshotPromotionError("Protected segment SHA mismatch")
    return paragraph


def resolve_manifest_row(
    entry: Mapping[str, Any],
    cas: Any,
) -> dict[str, Any]:
    payload = deepcopy(dict(entry["row_payload_redacted"]))
    protected = entry.get("protected_fields", {})
    if not isinstance(protected, Mapping):
        raise SnapshotPromotionError("protected_fields must be a mapping")
    for field_name, binding in protected.items():
        payload[str(field_name)] = _resolve_protected_field(binding, cas)
    observed = canonical_sha256(payload)
    expected = str(entry["canonical_row_payload_sha256"])
    if observed != expected:
        raise SnapshotPromotionError(
            f"Resolved row identity drift for {entry['row_id']}: "
            f"{observed} != {expected}"
        )
    return payload


def validate_manifest_document(
    manifest: Mapping[str, Any],
) -> None:
    if manifest.get("schema_version") != (
        "ecobiome-first-derived-snapshot-replay-manifest-v1"
    ):
        raise SnapshotPromotionError("Unsupported replay manifest schema")
    rows = manifest.get("rows")
    if not isinstance(rows, list) or not rows:
        raise SnapshotPromotionError("Replay manifest contains no rows")

    seen_ids: set[tuple[str, str]] = set()
    for entry in rows:
        if not isinstance(entry, Mapping):
            raise SnapshotPromotionError("Replay manifest row is not a mapping")
        table = _safe_identifier(str(entry["table"]))
        row_id = str(entry["row_id"])
        key = (table, row_id)
        if key in seen_ids:
            raise SnapshotPromotionError(f"Duplicate replay row: {key}")
        seen_ids.add(key)
        if len(str(entry["canonical_row_payload_sha256"])) != 64:
            raise SnapshotPromotionError("Invalid canonical row SHA length")
        where = entry.get("identity_where")
        if not isinstance(where, Mapping) or not where:
            raise SnapshotPromotionError("Missing row identity predicate")
        for column in where:
            _safe_identifier(str(column))

    expected = manifest.get("expected_table_delta")
    if not isinstance(expected, Mapping):
        raise SnapshotPromotionError("Missing expected table delta")
    if expected.get("knowledge_syntheses") != 0:
        raise SnapshotPromotionError("KnowledgeSynthesis delta must remain zero")
    if expected.get("source_lineage_edges") != 0:
        raise SnapshotPromotionError("Source-lineage delta must remain zero")


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    safe = _safe_identifier(table)
    return [
        str(row[1])
        for row in conn.execute(f"PRAGMA table_info({safe})").fetchall()
    ]


def validate_manifest_against_schema(
    conn: sqlite3.Connection,
    manifest: Mapping[str, Any],
) -> None:
    validate_manifest_document(manifest)
    for entry in manifest["rows"]:
        table = str(entry["table"])
        redacted = dict(entry["row_payload_redacted"])
        columns = _table_columns(conn, table)
        if set(redacted) != set(columns):
            raise SnapshotPromotionError(
                f"Manifest/schema column mismatch for {table}: "
                f"manifest={sorted(redacted)} schema={sorted(columns)}"
            )


def _select_identity_row(
    conn: sqlite3.Connection,
    table: str,
    where: Mapping[str, Any],
) -> sqlite3.Row | None:
    safe_table = _safe_identifier(table)
    columns = [_safe_identifier(str(column)) for column in where]
    predicate = " AND ".join(f"{column}=?" for column in columns)
    values = [where[column] for column in where]
    return conn.execute(
        f"SELECT * FROM {safe_table} WHERE {predicate}",
        values,
    ).fetchone()


def _insert_row(
    conn: sqlite3.Connection,
    table: str,
    row: Mapping[str, Any],
) -> None:
    safe_table = _safe_identifier(table)
    columns = [_safe_identifier(str(column)) for column in row]
    placeholders = ",".join("?" for _ in columns)
    column_sql = ",".join(columns)
    values = [row[column] for column in row]
    conn.execute(
        f"INSERT INTO {safe_table} ({column_sql}) VALUES ({placeholders})",
        values,
    )


def replay_manifest_rows(
    conn: sqlite3.Connection,
    manifest: Mapping[str, Any],
    cas: Any,
) -> None:
    validate_manifest_against_schema(conn, manifest)
    order = list(manifest["replay_dependency_order"])
    by_table: dict[str, list[Mapping[str, Any]]] = {}
    for entry in manifest["rows"]:
        by_table.setdefault(str(entry["table"]), []).append(entry)

    unknown = set(by_table).difference(order)
    if unknown:
        raise SnapshotPromotionError(
            f"Replay dependency order omits tables: {sorted(unknown)}"
        )

    for table in order:
        for entry in by_table.get(table, []):
            if _select_identity_row(
                conn,
                table,
                dict(entry["identity_where"]),
            ) is not None:
                raise SnapshotPromotionError(
                    f"Replay row unexpectedly preexists: {entry['row_id']}"
                )
            resolved = resolve_manifest_row(entry, cas)
            _insert_row(conn, table, resolved)


def verify_manifest_rows(
    conn: sqlite3.Connection,
    manifest: Mapping[str, Any],
    cas: Any,
) -> None:
    conn.row_factory = sqlite3.Row
    for entry in manifest["rows"]:
        row = _select_identity_row(
            conn,
            str(entry["table"]),
            dict(entry["identity_where"]),
        )
        if row is None:
            raise SnapshotPromotionError(
                f"Promoted row is missing: {entry['row_id']}"
            )
        observed_payload = dict(row)
        observed_sha = canonical_sha256(observed_payload)
        if observed_sha != entry["canonical_row_payload_sha256"]:
            raise SnapshotPromotionError(
                f"Post-replay row SHA drift for {entry['row_id']}: "
                f"{observed_sha} != {entry['canonical_row_payload_sha256']}"
            )
        # Resolve once more to prove protected-source reconstruction is stable.
        resolve_manifest_row(entry, cas)


def _derive_artifact_bytes(
    requirement: Mapping[str, Any],
    cas: Any,
) -> bytes:
    if requirement.get("derivation") != "normalized_jats_text_v1":
        raise SnapshotPromotionError("Unsupported derived-artifact transform")
    raw = cas.get(str(requirement["source_raw_artifact_key"]))
    if sha256_bytes(raw) != requirement["source_raw_sha256"]:
        raise SnapshotPromotionError("Derived-artifact raw source SHA drift")
    representation, _ = normalized_jats_text_v1(raw)
    data = representation.encode("utf-8")
    if sha256_bytes(data) != requirement["content_sha256"]:
        raise SnapshotPromotionError("Derived-artifact content SHA drift")
    return data


def ensure_derived_artifacts(
    manifest: Mapping[str, Any],
    cas: Any,
    *,
    allow_write: bool,
) -> None:
    for requirement in manifest.get("derived_cas_artifacts", []):
        key = str(requirement["artifact_key"])
        expected_sha = str(requirement["content_sha256"])
        try:
            verified = cas.verify(key)
            data = cas.get(key)
        except FileNotFoundError:
            if not allow_write:
                raise SnapshotPromotionError(
                    f"Derived CAS artifact missing and write unauthorized: {key}"
                )
            data = _derive_artifact_bytes(requirement, cas)
            stored = cas.put(data)
            verified = cas.verify(key)
            if stored.key != key:
                raise SnapshotPromotionError("Derived CAS returned wrong key")
        if (
            verified.key != key
            or verified.sha256 != expected_sha
            or sha256_bytes(data) != expected_sha
        ):
            raise SnapshotPromotionError("Derived CAS verification failed")


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory_windows(path: Path) -> None:
    kernel32: Any = ctypes.windll.kernel32
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    handle = create_file(
        str(path),
        0x80000000,  # GENERIC_READ
        0x00000007,  # FILE_SHARE_READ | WRITE | DELETE
        None,
        3,  # OPEN_EXISTING
        0x02000000,  # FILE_FLAG_BACKUP_SEMANTICS
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle in (None, invalid):
        raise SnapshotPromotionError(
            f"CreateFileW failed for directory fsync: {path}"
        )
    try:
        if not kernel32.FlushFileBuffers(handle):
            raise SnapshotPromotionError(
                f"FlushFileBuffers failed for directory: {path}"
            )
    finally:
        kernel32.CloseHandle(handle)


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        _fsync_directory_windows(path)
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _verify_sqlite_file(
    path: Path,
    *,
    expected_schema_version: int,
    expected_schema_design_sha256: str,
) -> dict[str, Any]:
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        quick = [row[0] for row in conn.execute("PRAGMA quick_check")]
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
        metadata = conn.execute(
            """
            SELECT schema_version,design_sha256
            FROM sf_schema_metadata
            WHERE schema_name='scientific_foundation'
            """
        ).fetchone()
        if quick != ["ok"] or fk:
            raise SnapshotPromotionError("Published SQLite integrity failure")
        if user_version != expected_schema_version:
            raise SnapshotPromotionError("Published schema version drift")
        if metadata != (
            expected_schema_version,
            expected_schema_design_sha256,
        ):
            raise SnapshotPromotionError("Published schema design drift")
        return {
            "quick_check": quick,
            "foreign_key_violation_count": len(fk),
            "user_version": user_version,
        }
    finally:
        conn.close()


def _build_snapshot_manifest_payload(
    *,
    replay_manifest: Mapping[str, Any],
    authorization: PromotionAuthorization,
    database_sha256: str,
    database_size_bytes: int,
    table_counts: Mapping[str, int],
    regression_gate_summary: Mapping[str, Any],
    created_at: str,
    schema_design_sha256: str,
) -> dict[str, Any]:
    reviewed = replay_manifest["reviewed_input_identities"]
    return {
        "schema_version": (
            "ecobiome-scientific-foundation-snapshot-manifest-v1-reviewed"
        ),
        "snapshot": {
            "database_sha256": database_sha256,
            "database_size_bytes": database_size_bytes,
            "schema_version": 6,
            "schema_design_sha256": schema_design_sha256,
            "immutable": True,
            "created_at": created_at,
            "purpose": (
                "First immutable derived Scientific Foundation snapshot "
                "containing reviewed ammonia-to-nitrite evidence state."
            ),
        },
        "lineage": {
            "parent_kind": "legacy_root",
            "parent_database_sha256": replay_manifest[
                "parent_database_sha256"
            ],
            "parent_manifest_sha256": None,
            "promotion_plan_sha256": replay_manifest[
                "promotion_plan_sha256"
            ],
            "source_repo_head": authorization.scientific_input_repo_head,
        },
        "reviewed_inputs": reviewed,
        "runtime_and_persistence_identity": {
            "sqlite_version": sqlite3.sqlite_version,
            "python_version": sys.version,
            "persistence_schema_design_sha256": schema_design_sha256,
            "promotion_engine_identity": {
                "name": ENGINE_NAME,
                "version_or_gate": ENGINE_VERSION,
                "source_repo_head": authorization.promotion_engine_repo_head,
                "code_identity_sha256": (
                    authorization.promotion_engine_code_identity_sha256
                ),
            },
        },
        "validation": {
            "quick_check": ["ok"],
            "foreign_key_violation_count": 0,
            "regression_gate_summary": dict(regression_gate_summary),
            "table_counts": dict(table_counts),
            "replay_manifest_payload_sha256": replay_manifest[
                "replay_manifest_payload_sha256"
            ],
        },
        "boundaries": {
            "real_v6_mutated": False,
            "knowledge_synthesis_created": False,
            "numeric_rate_model_authorized": False,
            "active_pointer_updated": False,
        },
    }


def _publish_atomic_complete_pair(
    *,
    temporary_directory: Path,
    final_directory: Path,
    database_sha256: str,
    manifest_sha256: str,
) -> None:
    db = temporary_directory / "scientific-foundation.sqlite3"
    manifest = temporary_directory / "snapshot-manifest.json"
    if sha256_file(db) != database_sha256:
        raise SnapshotPromotionError("Temporary publication DB SHA drift")
    if sha256_file(manifest) != manifest_sha256:
        raise SnapshotPromotionError("Temporary publication manifest SHA drift")

    _fsync_file(db)
    _fsync_file(manifest)
    _fsync_directory(temporary_directory)

    if final_directory.exists():
        final_db = final_directory / "scientific-foundation.sqlite3"
        final_manifest = final_directory / "snapshot-manifest.json"
        if not final_db.is_file() or not final_manifest.is_file():
            raise SnapshotPromotionError(
                "Partial pre-existing final snapshot directory is fatal"
            )
        if (
            sha256_file(final_db) != database_sha256
            or sha256_file(final_manifest) != manifest_sha256
        ):
            raise SnapshotPromotionError(
                "Inconsistent pre-existing final snapshot directory is fatal"
            )
        shutil.rmtree(temporary_directory)
        return

    os.replace(temporary_directory, final_directory)
    _fsync_directory(final_directory.parent)


def promote_first_derived_snapshot(
    *,
    parent_database: Path,
    snapshot_root: Path,
    replay_manifest: Mapping[str, Any],
    cas: Any,
    authorization: PromotionAuthorization,
    expected_engine_code_sha256: str,
    regression_runner: Callable[[], Mapping[str, Any]],
    created_at: str,
) -> PromotionResult:
    """Execute the reviewed promotion after a later explicit authorization."""

    verify_authorization(authorization, expected_engine_code_sha256)
    validate_manifest_document(replay_manifest)

    expected_parent_sha = str(replay_manifest["parent_database_sha256"])
    if sha256_file(parent_database) != expected_parent_sha:
        raise SnapshotPromotionError("Frozen parent database SHA drift")

    ensure_derived_artifacts(
        replay_manifest,
        cas,
        allow_write=authorization.derived_representation_cas_write_authorized,
    )

    snapshot_root.mkdir(parents=True, exist_ok=True)
    temporary_directory = snapshot_root / (
        ".tmp-promotion-" + uuid.uuid4().hex
    )
    temporary_directory.mkdir(parents=False, exist_ok=False)
    staging_db = temporary_directory / "scientific-foundation.sqlite3"

    try:
        shutil.copyfile(parent_database, staging_db)
        if sha256_file(staging_db) != expected_parent_sha:
            raise SnapshotPromotionError("Staging copy differs from parent")

        conn = sqlite3.connect(staging_db)
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA synchronous=FULL")
            conn.row_factory = sqlite3.Row
            validate_manifest_against_schema(conn, replay_manifest)

            before_counts = {
                str(table): conn.execute(
                    f"SELECT COUNT(*) FROM {_safe_identifier(str(table))}"
                ).fetchone()[0]
                for table in replay_manifest["expected_table_delta"]
            }

            conn.execute("BEGIN IMMEDIATE")
            try:
                replay_manifest_rows(conn, replay_manifest, cas)
                verify_manifest_rows(conn, replay_manifest, cas)

                fk = conn.execute("PRAGMA foreign_key_check").fetchall()
                quick = [
                    row[0] for row in conn.execute("PRAGMA quick_check")
                ]
                if fk or quick != ["ok"]:
                    raise SnapshotPromotionError(
                        "Post-replay SQLite integrity failure"
                    )

                final_counts = {
                    str(table): conn.execute(
                        f"SELECT COUNT(*) FROM {_safe_identifier(str(table))}"
                    ).fetchone()[0]
                    for table in replay_manifest["expected_table_delta"]
                }
                for table, delta in replay_manifest[
                    "expected_table_delta"
                ].items():
                    if final_counts[table] != before_counts[table] + delta:
                        raise SnapshotPromotionError(
                            f"Exact table delta mismatch for {table}"
                        )
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        finally:
            conn.close()

        regression_summary = dict(regression_runner())

        database_sha = sha256_file(staging_db)
        database_size = staging_db.stat().st_size

        verification = _verify_sqlite_file(
            staging_db,
            expected_schema_version=6,
            expected_schema_design_sha256=str(
                replay_manifest["schema_design_sha256"]
            ),
        )

        check_conn = sqlite3.connect(
            staging_db.resolve().as_uri() + "?mode=ro",
            uri=True,
        )
        try:
            table_counts = {
                str(table): check_conn.execute(
                    f"SELECT COUNT(*) FROM {_safe_identifier(str(table))}"
                ).fetchone()[0]
                for table in replay_manifest["expected_table_delta"]
            }
        finally:
            check_conn.close()

        manifest_payload = _build_snapshot_manifest_payload(
            replay_manifest=replay_manifest,
            authorization=authorization,
            database_sha256=database_sha,
            database_size_bytes=database_size,
            table_counts=table_counts,
            regression_gate_summary={
                **regression_summary,
                "sqlite_verification": verification,
            },
            created_at=created_at,
            schema_design_sha256=str(
                replay_manifest["schema_design_sha256"]
            ),
        )
        manifest_document = {
            "manifest_payload_sha256": canonical_sha256(manifest_payload),
            "manifest_payload": manifest_payload,
        }
        manifest_path = temporary_directory / "snapshot-manifest.json"
        manifest_path.write_text(
            json.dumps(
                manifest_document,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest_sha = sha256_file(manifest_path)

        final_directory = snapshot_root / database_sha
        _publish_atomic_complete_pair(
            temporary_directory=temporary_directory,
            final_directory=final_directory,
            database_sha256=database_sha,
            manifest_sha256=manifest_sha,
        )

        final_db = final_directory / "scientific-foundation.sqlite3"
        final_manifest = final_directory / "snapshot-manifest.json"
        if (
            sha256_file(final_db) != database_sha
            or sha256_file(final_manifest) != manifest_sha
        ):
            raise SnapshotPromotionError("Final publication verification failed")

        if sha256_file(parent_database) != expected_parent_sha:
            raise SnapshotPromotionError("Frozen parent changed during promotion")

        return PromotionResult(
            database_sha256=database_sha,
            database_size_bytes=database_size,
            manifest_sha256=manifest_sha,
            logical_snapshot_path=str(final_directory),
        )
    except BaseException:
        if temporary_directory.exists():
            shutil.rmtree(temporary_directory)
        raise
