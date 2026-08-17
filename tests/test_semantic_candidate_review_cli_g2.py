from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from ecobiome.cli.main import main as central_main
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    build_semantic_candidate_v2_11,
)
from ecobiome.knowledge_persistence import (
    PersistenceConfig,
    initialize_database,
)
from ecobiome.knowledge_persistence.serialization import canonical_json_text

CREATED_AT = "2026-08-16T21:00:00+00:00"
TEXT = "Temperature was maintained at 26.5 °C."


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _candidate() -> dict[str, object]:
    registry = {
        "relations": {
            "maintained_at": {
                "argument_keys": ["variable", "value", "unit"],
                "epistemic_class": "study_context_non_result",
                "semantic_type_contract_state":
                    "historical_golden_reviewed_constrained",
                "semantic_types_allowed": ["experimental_condition"],
            }
        },
        "argument_role_semantics": {
            "variable": {
                "grounding_class": "open_text_source_grounded",
                "semantic_domain": "measurable_or_described_variable",
            },
            "value": {
                "grounding_class": "exact_numeric_source_grounded",
                "semantic_domain": "numeric_value",
            },
            "unit": {
                "grounding_class": "controlled_literal_source_grounded",
                "semantic_domain": "controlled_measurement_or_time_unit",
            },
        },
    }
    return build_semantic_candidate_v2_11(
        {
            "c": "claim-1",
            "e": ["ev-1"],
            "t": "experimental_condition",
            "m": {
                "r": "maintained_at",
                "a": {
                    "variable": "temperature",
                    "value": 26.5,
                    "unit": "degree celsius",
                },
            },
        },
        {
            "source_claims": [
                {
                    "claim_id": "claim-1",
                    "effective_text": TEXT,
                    "evidence": [{"evidence_id": "ev-1", "text": "26.5 °C"}],
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


def _seed_candidate(database: Path) -> tuple[dict[str, object], tuple[object, ...]]:
    candidate = _candidate()
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
                "urn:g2:source",
                "G2 fixture",
                "en",
                CREATED_AT,
                "1" * 64,
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
            ) VALUES (?, ?, NULL, NULL, 'atomic', ?, ?, 'statement', ?,
                      '{}', NULL, ?, '', 'accepted', ?)
            """,
            (
                "claim-1",
                "source-1",
                TEXT,
                _sha(TEXT),
                "experimental_condition",
                _sha(TEXT),
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
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
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
        snapshot = connection.execute(
            "SELECT * FROM semantic_candidates WHERE id='candidate-1'"
        ).fetchone()
        assert snapshot is not None

        for table in (
            "semantic_candidates",
            "semantic_candidate_review_events",
        ):
            connection.execute(
                f"""
                CREATE TRIGGER forbid_{table}_update
                BEFORE UPDATE ON {table}
                BEGIN
                    SELECT RAISE(ABORT, 'G2 forbids UPDATE');
                END
                """
            )
            connection.execute(
                f"""
                CREATE TRIGGER forbid_{table}_delete
                BEFORE DELETE ON {table}
                BEGIN
                    SELECT RAISE(ABORT, 'G2 forbids DELETE');
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


def test_g2_cli_lists_shows_and_appends_without_update_delete(
    tmp_path: Path,
    capsys,
) -> None:
    repo, database, artifacts = _storage(tmp_path)
    candidate, before = _seed_candidate(database)
    common = _base_args(repo, database, artifacts)

    assert central_main(
        ["collector", "semantic-candidate-list", *common]
    ) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["count"] == 1
    assert listed["candidates"][0]["id"] == "candidate-1"
    assert listed["candidates"][0]["review_status"] == "pending"

    assert central_main(
        [
            "collector",
            "semantic-candidate-show",
            "candidate-1",
            *common,
        ]
    ) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["candidate"]["canonical_candidate"] == candidate
    assert shown["review_status"] == "pending"
    assert shown["review_history"] == []

    with pytest.raises(
        ValueError,
        match="correct requires --replacement-candidate-id",
    ):
        central_main(
            [
                "collector",
                "semantic-candidate-review",
                "candidate-1",
                "correct",
                *common,
                "--reviewer",
                "human-g2",
            ]
        )

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
            "review-1",
            "--reviewed-at",
            "2026-08-16T21:01:00+00:00",
        ]
    ) == 0
    accepted = json.loads(capsys.readouterr().out)
    assert accepted["inserted"] is True
    assert accepted["review_status"] == "accepted"
    assert accepted["review_event_count"] == 1

    assert central_main(
        [
            "collector",
            "semantic-candidate-review",
            "candidate-1",
            "reject",
            *common,
            "--reviewer",
            "human-g2",
            "--rationale",
            "insufficient evidence",
            "--event-id",
            "review-2",
            "--reviewed-at",
            "2026-08-16T21:02:00+00:00",
        ]
    ) == 0
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["inserted"] is True
    assert rejected["review_status"] == "rejected"
    assert rejected["review_event_count"] == 2

    assert central_main(
        [
            "collector",
            "semantic-candidate-review",
            "candidate-1",
            "reject",
            *common,
            "--reviewer",
            "human-g2",
            "--rationale",
            "insufficient evidence",
            "--event-id",
            "review-2",
            "--reviewed-at",
            "2026-08-16T21:02:00+00:00",
        ]
    ) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["inserted"] is False
    assert replay["review_event_count"] == 2

    assert central_main(
        [
            "collector",
            "semantic-candidate-list",
            *common,
            "--status",
            "rejected",
        ]
    ) == 0
    filtered = json.loads(capsys.readouterr().out)
    assert filtered["count"] == 1
    assert filtered["candidates"][0]["review_status"] == "rejected"

    with sqlite3.connect(database) as connection:
        after = connection.execute(
            "SELECT * FROM semantic_candidates WHERE id='candidate-1'"
        ).fetchone()
        reviews = connection.execute(
            """
            SELECT id, decision, reviewer, rationale
            FROM semantic_candidate_review_events
            WHERE semantic_candidate_id='candidate-1'
            ORDER BY reviewed_at, id
            """
        ).fetchall()

    assert after is not None
    assert tuple(after) == before
    assert reviews == [
        ("review-1", "accept", "human-g2", ""),
        (
            "review-2",
            "reject",
            "human-g2",
            "insufficient evidence",
        ),
    ]
