from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from ecobiome.cli.main import main as central_main
from ecobiome.knowledge_acquisition.semantic_candidate_review_v1 import (
    SemanticCandidateReviewV1Error,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    build_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence import (
    PersistenceConfig,
    initialize_database,
)
from ecobiome.knowledge_persistence.serialization import canonical_json_text

CREATED_AT = "2026-08-17T18:00:00+00:00"
TEXT = "Ammonia adversely affects medaka."


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _candidate(text: str = TEXT) -> dict[str, object]:
    registry = {
        "relations": {
            "adversely_affects": {
                "argument_keys": ["cause", "target"],
                "epistemic_class": "explicit_causal_result",
                "semantic_type_contract_state": (
                    "historical_golden_reviewed_constrained"
                ),
                "semantic_types_allowed": ["health_effect"],
            }
        },
        "argument_role_semantics": {
            "cause": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "causal_driver_or_factor",
            },
            "target": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "target_entity_or_process",
            },
        },
    }
    return build_semantic_candidate_v2_11(
        {
            "c": "claim-1",
            "e": ["ev-1"],
            "t": "health_effect",
            "m": {
                "r": "adversely_affects",
                "a": {
                    "cause": "Ammonia",
                    "target": "medaka",
                },
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-1",
                    "effective_text": text,
                    "evidence": [
                        {
                            "evidence_id": "ev-1",
                            "text": text,
                        }
                    ],
                }
            ]
        },
        registry,
    )


def _storage(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    storage = tmp_path / "storage"
    database = storage / "scientific.sqlite3"
    artifacts = storage / "cas"
    initialize_database(
        PersistenceConfig(database, artifacts),
        repo_root=repo,
    )
    return repo, database, artifacts


def _seed(
    database: Path,
    *,
    text: str = TEXT,
) -> tuple[dict[str, object], tuple[object, ...]]:
    candidate = _candidate(text)
    candidate_json = canonical_json_text(candidate)
    contract = candidate["contract"]
    source = candidate["source"]
    semantic = candidate["semantic"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO knowledge_sources (
                id, source_type, canonical_locator, title, author, language,
                description, imported_at, source_metadata_json,
                logical_identity_sha256, created_at
            ) VALUES (?, ?, ?, ?, NULL, ?, '', ?, '{}', ?, ?)
            """,
            (
                "source-1",
                "fixture",
                "urn:g5:source",
                "G5 fixture",
                "en",
                CREATED_AT,
                "1" * 64,
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO representations (
                id, source_id, origin_raw_artifact_id, logical_key,
                representation_kind, media_type, language, content_sha256,
                artifact_store_key, materialization_status, metadata_json,
                created_at
            ) VALUES (?, ?, NULL, 'main', 'text', 'text/plain', 'en', ?,
                      NULL, 'inline', '{}', ?)
            """,
            (
                "rep-1",
                "source-1",
                _sha(text),
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO segments (
                id, representation_id, segment_index, text_inline, text_sha256,
                materialization_status, representation_char_start,
                representation_char_end, start_seconds_decimal,
                end_seconds_decimal, page_number, frame_start, frame_end,
                review_status, metadata_json, created_at
            ) VALUES (?, ?, 0, ?, ?, 'inline', 0, ?, NULL, NULL, NULL, NULL,
                      NULL, 'accepted', '{}', ?)
            """,
            (
                "seg-1",
                "rep-1",
                text,
                _sha(text),
                len(text),
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO source_evidence (
                id, segment_id, segment_char_start, segment_char_end,
                evidence_text_sha256, start_seconds_decimal,
                end_seconds_decimal, page_number, frame_start, frame_end,
                evidence_metadata_json, created_at
            ) VALUES (?, ?, 0, ?, ?, NULL, NULL, NULL, NULL, NULL, '{}', ?)
            """,
            (
                "ev-1",
                "seg-1",
                len(text),
                _sha(text),
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO source_claims (
                id, source_id, representation_id, parent_claim_id, claim_layer,
                claim_text, claim_text_sha256, claim_kind, semantic_type,
                qualifiers_json, extraction_confidence_decimal,
                source_claim_effective_text_sha256, notes,
                initial_review_status, created_at
            ) VALUES (?, ?, ?, NULL, 'atomic', ?, ?, 'statement', ?,
                      '{}', NULL, ?, '', 'accepted', ?)
            """,
            (
                "claim-1",
                "source-1",
                "rep-1",
                text,
                _sha(text),
                "health_effect",
                _sha(text),
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO claim_evidence_links (
                claim_id, evidence_id, evidence_order, link_role, created_at
            ) VALUES (?, ?, 0, 'supports_source_claim', ?)
            """,
            (
                "claim-1",
                "ev-1",
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO semantic_candidates (
                id, schema_version, semantic_contract_name,
                semantic_contract_version, semantic_contract_sha256,
                relation_type_basis_version, relation_type_registry_sha256,
                grounding_policy_sha256,
                claim_scoped_provenance_policy_sha256,
                source_statement_claim_id,
                source_claim_effective_text_sha256, semantic_type, relation,
                epistemic_class, promotion_readiness,
                automatic_scientific_acceptance,
                canonical_candidate_sha256,
                canonical_candidate_document_sha256,
                canonical_candidate_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?,
                      ?, ?, ?)
            """,
            (
                "candidate-1",
                str(candidate["schema_version"]),
                str(contract["name"]),
                str(contract["version"]),
                str(contract["canonical_sha256"]),
                str(contract["relation_type_basis_version"]),
                str(contract["relation_type_registry_sha256"]),
                str(contract["grounding_policy_sha256"]),
                str(contract["claim_scoped_provenance_policy_sha256"]),
                str(source["source_statement_claim_id"]),
                str(source["source_claim_effective_text_sha256"]),
                str(semantic["semantic_type"]),
                str(semantic["relation"]),
                str(semantic["epistemic_class"]),
                str(candidate["promotion_readiness"]),
                str(candidate["canonical_candidate_sha256"]),
                _sha(candidate_json),
                candidate_json,
                CREATED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO semantic_candidate_evidence_links (
                semantic_candidate_id, source_statement_claim_id, evidence_id,
                evidence_order, created_at
            ) VALUES (?, ?, ?, 0, ?)
            """,
            (
                "candidate-1",
                "claim-1",
                "ev-1",
                CREATED_AT,
            ),
        )

        for entity_id, label in (
            ("entity-ammonia", "Ammonia"),
            ("entity-medaka", "medaka"),
        ):
            connection.execute(
                """
                INSERT INTO scientific_entities (
                    id, entity_kind, created_at, retired_at
                ) VALUES (?, 'scientific_concept', ?, NULL)
                """,
                (
                    entity_id,
                    CREATED_AT,
                ),
            )
            connection.execute(
                """
                INSERT INTO scientific_entity_revisions (
                    entity_id, revision, schema_version, canonical_label,
                    canonical_payload_json, canonical_payload_sha256,
                    review_status, created_at
                ) VALUES (?, 1, 'entity-v1', ?, '{}', ?,
                          'reviewed_confirmed', ?)
                """,
                (
                    entity_id,
                    label,
                    _sha(f"{entity_id}:1"),
                    CREATED_AT,
                ),
            )

        connection.execute(
            """
            INSERT INTO scientific_entity_revisions (
                entity_id, revision, schema_version, canonical_label,
                canonical_payload_json, canonical_payload_sha256,
                review_status, created_at
            ) VALUES (?, 2, 'entity-v1', ?, '{}', ?, 'unreviewed', ?)
            """,
            (
                "entity-ammonia",
                "Ammonia",
                _sha("entity-ammonia:2"),
                CREATED_AT,
            ),
        )

        snapshot = connection.execute(
            "SELECT * FROM semantic_candidates WHERE id='candidate-1'"
        ).fetchone()
        assert snapshot is not None

        for table in (
            "semantic_candidates",
            "scientific_entity_name_usages",
            "semantic_candidate_entity_resolution_events",
        ):
            connection.execute(
                f"""
                CREATE TRIGGER forbid_{table}_update
                BEFORE UPDATE ON {table}
                BEGIN
                    SELECT RAISE(ABORT, 'G5 forbids UPDATE');
                END
                """
            )
            connection.execute(
                f"""
                CREATE TRIGGER forbid_{table}_delete
                BEFORE DELETE ON {table}
                BEGIN
                    SELECT RAISE(ABORT, 'G5 forbids DELETE');
                END
                """
            )

    return candidate, tuple(snapshot)


def _base_args(
    repo: Path,
    database: Path,
    artifacts: Path,
) -> list[str]:
    return [
        "--database",
        str(database),
        "--artifact-store-root",
        str(artifacts),
        "--repository-root",
        str(repo),
    ]


def _accept_candidate(
    common: list[str],
    capsys,
) -> None:
    assert central_main(
        [
            "collector",
            "semantic-candidate-review",
            "candidate-1",
            "accept",
            *common,
            "--reviewer",
            "human-g2",
            "--event-id",
            "candidate-review-1",
            "--reviewed-at",
            "2026-08-17T18:01:00+00:00",
        ]
    ) == 0
    capsys.readouterr()


def _accept_cause_mapping(
    common: list[str],
    capsys,
    *,
    extra: list[str] | None = None,
) -> dict[str, object]:
    args = [
        "collector",
        "semantic-candidate-entity-review",
        "candidate-1",
        "cause",
        "accept",
        *common,
        "--reviewer",
        "human-g5",
        "--entity-id",
        "entity-ammonia",
        "--entity-revision",
        "1",
        "--name-usage-id",
        "usage-ammonia",
        "--event-id",
        "resolution-1",
        "--reviewed-at",
        "2026-08-17T18:02:00+00:00",
    ]
    if extra:
        args.extend(extra)
    assert central_main(args) == 0
    return json.loads(capsys.readouterr().out)


def test_g5_search_show_accept_and_exact_replay(
    tmp_path: Path,
    capsys,
) -> None:
    repo, database, artifacts = _storage(tmp_path)
    candidate, before = _seed(database)
    common = _base_args(repo, database, artifacts)
    _accept_candidate(common, capsys)

    assert central_main(
        [
            "collector",
            "semantic-candidate-entity-search",
            "Ammonia",
            *common,
        ]
    ) == 0
    searched = json.loads(capsys.readouterr().out)
    assert searched["match_mode"] == "exact_canonical_label"
    assert searched["count"] == 1
    assert searched["entity_revisions"][0]["entity_id"] == "entity-ammonia"
    assert searched["entity_revisions"][0]["revision"] == 1

    assert central_main(
        [
            "collector",
            "semantic-candidate-entity-show",
            "candidate-1",
            *common,
        ]
    ) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["candidate_review_status"] == "accept"
    cause = next(
        item for item in shown["arguments"] if item["role"] == "cause"
    )
    assert cause["requires_entity_resolution"] is True
    assert cause["resolution"]["status"] == "pending"

    accepted = _accept_cause_mapping(common, capsys)
    assert accepted["inserted"] is True
    assert accepted["name_usage_inserted"] is True
    assert accepted["resolution_status"] == "accept"
    assert accepted["source_anchor"]["segment_id"] == "seg-1"
    assert accepted["source_anchor"]["segment_char_start"] == 0
    assert accepted["source_anchor"]["segment_char_end"] == 7

    replay = _accept_cause_mapping(common, capsys)
    assert replay["inserted"] is False
    assert replay["name_usage_inserted"] is False
    assert replay["resolution_event_count"] == 1

    with sqlite3.connect(database) as connection:
        after = connection.execute(
            "SELECT * FROM semantic_candidates WHERE id='candidate-1'"
        ).fetchone()
        usages = connection.execute(
            """
            SELECT id, entity_id, source_id, verbatim_name, segment_id,
                   segment_char_start, segment_char_end,
                   mapping_review_status
            FROM scientific_entity_name_usages
            ORDER BY id
            """
        ).fetchall()
        events = connection.execute(
            """
            SELECT id, role, entity_name_usage_id, entity_id, entity_revision,
                   mapping_status, decision, reviewer
            FROM semantic_candidate_entity_resolution_events
            ORDER BY reviewed_at, id
            """
        ).fetchall()

    assert after is not None
    assert tuple(after) == before
    assert usages == [
        (
            "usage-ammonia",
            "entity-ammonia",
            "source-1",
            "Ammonia",
            "seg-1",
            0,
            7,
            "reviewed_confirmed",
        )
    ]
    assert events == [
        (
            "resolution-1",
            "cause",
            "usage-ammonia",
            "entity-ammonia",
            1,
            "exact",
            "accept",
            "human-g5",
        )
    ]
    assert candidate["automatic_scientific_acceptance"] is False


def test_g5_reject_revokes_latest_accepted_mapping(
    tmp_path: Path,
    capsys,
) -> None:
    repo, database, artifacts = _storage(tmp_path)
    _seed(database)
    common = _base_args(repo, database, artifacts)
    _accept_candidate(common, capsys)
    _accept_cause_mapping(common, capsys)

    assert central_main(
        [
            "collector",
            "semantic-candidate-entity-review",
            "candidate-1",
            "cause",
            "reject",
            *common,
            "--reviewer",
            "human-g5",
            "--rationale",
            "mapping withdrawn",
            "--event-id",
            "resolution-2",
            "--reviewed-at",
            "2026-08-17T18:03:00+00:00",
        ]
    ) == 0
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["inserted"] is True
    assert rejected["name_usage_inserted"] is False
    assert rejected["resolution_status"] == "reject"
    assert rejected["resolution_event_count"] == 2

    with pytest.raises(
        ValueError,
        match="latest accepted entity mapping",
    ):
        central_main(
            [
                "collector",
                "semantic-candidate-entity-review",
                "candidate-1",
                "cause",
                "reject",
                *common,
                "--reviewer",
                "human-g5",
            ]
        )


def test_g5_requires_candidate_acceptance_and_explicit_disambiguation(
    tmp_path: Path,
    capsys,
) -> None:
    text = "Ammonia and Ammonia adversely affects medaka."
    repo, database, artifacts = _storage(tmp_path)
    _seed(database, text=text)
    common = _base_args(repo, database, artifacts)

    with pytest.raises(
        SemanticCandidateReviewV1Error,
        match="requires at least one human review event",
    ):
        _accept_cause_mapping(common, capsys)

    _accept_candidate(common, capsys)

    with pytest.raises(
        ValueError,
        match="exactly one Evidence span",
    ):
        _accept_cause_mapping(common, capsys)

    accepted = _accept_cause_mapping(
        common,
        capsys,
        extra=[
            "--evidence-id",
            "ev-1",
            "--segment-char-start",
            "0",
        ],
    )
    assert accepted["inserted"] is True
    assert accepted["source_anchor"]["segment_char_start"] == 0


def test_g5_reject_forbids_mapping_override_arguments(
    tmp_path: Path,
    capsys,
) -> None:
    repo, database, artifacts = _storage(tmp_path)
    _seed(database)
    common = _base_args(repo, database, artifacts)
    _accept_candidate(common, capsys)
    _accept_cause_mapping(common, capsys)

    with pytest.raises(
        ValueError,
        match="reject reuses the latest accepted mapping",
    ):
        central_main(
            [
                "collector",
                "semantic-candidate-entity-review",
                "candidate-1",
                "cause",
                "reject",
                *common,
                "--reviewer",
                "human-g5",
                "--entity-id",
                "entity-medaka",
            ]
        )
