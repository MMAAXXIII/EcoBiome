import hashlib
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ecobiome.knowledge_persistence import (
    AssertionClaimLinksRow,
    FilesystemContentAddressedArtifactStore,
    KnowledgeSourcesRow,
    PersistenceConfig,
    ScientificAssertionRevisionsRow,
    ScientificAssertionsRow,
    SourceClaimsRow,
    SQLiteScientificFoundationUnitOfWork,
    initialize_database,
)
from ecobiome.knowledge_persistence.contracts import (
    AcquisitionJobsRow,
    ClaimReviewEventsRow,
    SegmentReviewEventsRow,
)
from ecobiome.knowledge_persistence.errors import (
    DuplicateIdentityConflict,
    PersistenceIntegrityError,
    ScopeAlignmentError,
)
from ecobiome.knowledge_persistence.serialization import (
    canonical_assertion_payload,
    canonical_json_text,
    canonical_sha256,
)

CREATED_AT = "2026-08-13T00:00:00Z"


def _config_and_artifacts(
    tmp_path: Path,
) -> tuple[
    PersistenceConfig,
    FilesystemContentAddressedArtifactStore,
    Path,
]:
    repo = tmp_path / "repo"
    repo.mkdir()
    storage = tmp_path / "storage"
    config = PersistenceConfig(
        storage / "scientific.sqlite3",
        storage / "artifacts",
    )
    initialize_database(config, repo_root=repo)
    artifacts = FilesystemContentAddressedArtifactStore(
        config.artifact_store_root
    )
    return config, artifacts, repo


def _link(
    *,
    scope_alignment: str = "exact",
    semantic_alignment: str = "exact",
) -> AssertionClaimLinksRow:
    return AssertionClaimLinksRow(
        id="link-1",
        assertion_id="assertion-1",
        assertion_revision=1,
        claim_id="claim-1",
        stance="supports",
        support_mode="direct_observation",
        scope_alignment=scope_alignment,
        semantic_alignment=semantic_alignment,
        review_status="reviewed_fixture",
        reviewed_by="fixture",
        reviewed_at=CREATED_AT,
        created_at=CREATED_AT,
    )


def test_uow_insert_commit_and_duplicate_idempotence(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    row = KnowledgeSourcesRow(
        id="source-1",
        source_type="test",
        canonical_locator="urn:test:source-1",
        title="test source",
        author=None,
        language="en",
        description="",
        imported_at=CREATED_AT,
        source_metadata_json="{}",
        logical_identity_sha256="0" * 64,
        created_at=CREATED_AT,
    )

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.add_knowledge_source(row) is True
        uow.commit()

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.add_knowledge_source(row) is False


def test_exact_scope_support_link_is_persisted(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    source = KnowledgeSourcesRow(
        id="source-1",
        source_type="test",
        canonical_locator="urn:test:source-1",
        title="test source",
        author=None,
        language="en",
        description="",
        imported_at=CREATED_AT,
        source_metadata_json="{}",
        logical_identity_sha256="0" * 64,
        created_at=CREATED_AT,
    )
    claim = SourceClaimsRow(
        id="claim-1",
        source_id=source.id,
        representation_id=None,
        parent_claim_id=None,
        claim_layer="atomic",
        claim_text="scope guard fixture claim",
        claim_text_sha256="1" * 64,
        claim_kind="fixture",
        semantic_type="fixture",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256="1" * 64,
        notes="",
        initial_review_status="reviewed_fixture",
        created_at=CREATED_AT,
    )
    payload = canonical_assertion_payload(
        assertion_kind="event",
        predicate="scope_guard_fixture",
        participants=[],
        value={"kind": "none"},
        qualifiers={},
    )
    assertion = ScientificAssertionsRow(
        id="assertion-1",
        created_at=CREATED_AT,
        retired_at=None,
    )
    revision = ScientificAssertionRevisionsRow(
        assertion_id=assertion.id,
        revision=1,
        schema_version="scientific-assertion-v1.1",
        assertion_kind="event",
        predicate="scope_guard_fixture",
        participants_json=canonical_json_text(payload["participants"]),
        value_json=canonical_json_text(payload["value"]),
        qualifiers_json=canonical_json_text(payload["qualifiers"]),
        normalized_text="scope guard fixture",
        canonical_payload_sha256=canonical_sha256(payload),
        created_at=CREATED_AT,
    )

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.add_knowledge_source(source) is True
        assert uow.provenance.add_source_claims([claim]) == 1
        assert uow.assertions.add_assertion(assertion) is True
        assert uow.assertions.add_assertion_revision(revision) is True
        assert uow.assertions.add_assertion_claim_link(_link()) is True
        uow.commit()


def test_source_narrower_support_link_is_rejected(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow, pytest.raises(ScopeAlignmentError):
        uow.assertions.add_assertion_claim_link(
            _link(scope_alignment="source_narrower")
        )


def test_invalid_scope_alignment_vocabulary_is_rejected(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow, pytest.raises(PersistenceIntegrityError):
        uow.assertions.add_assertion_claim_link(
            _link(scope_alignment="species_magic")
        )


def test_insufficient_semantic_alignment_cannot_support(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow, pytest.raises(PersistenceIntegrityError):
        uow.assertions.add_assertion_claim_link(
            _link(semantic_alignment="insufficient_to_link")
        )


def _seed_segment_for_review(config: PersistenceConfig) -> None:
    with sqlite3.connect(config.database_path) as connection:
        connection.execute(
            "INSERT INTO knowledge_sources "
            "(id, source_type, canonical_locator, title, author, language, description, imported_at, source_metadata_json, logical_identity_sha256, created_at) "
            "VALUES ('source-review', 'test', 'urn:test:review', 'review', NULL, 'en', '', ?, '{}', ?, ?)",
            (CREATED_AT, "0" * 64, CREATED_AT),
        )
        connection.execute(
            "INSERT INTO representations "
            "(id, source_id, origin_raw_artifact_id, logical_key, representation_kind, media_type, language, content_sha256, artifact_store_key, materialization_status, metadata_json, created_at) "
            "VALUES ('representation-review', 'source-review', NULL, 'main', 'text', 'text/plain', 'en', ?, NULL, 'inline', '{}', ?)",
            ("1" * 64, CREATED_AT),
        )
        connection.execute(
            "INSERT INTO segments "
            "(id, representation_id, segment_index, text_inline, text_sha256, materialization_status, review_status, metadata_json, created_at) "
            "VALUES ('segment-review', 'representation-review', 0, 'original source text', ?, 'inline', 'pending', '{}', ?)",
            (hashlib.sha256(b"original source text").hexdigest(), CREATED_AT),
        )


def _review_event(
    *,
    event_id: str = "review-1",
    decision: str = "accept",
    corrected_text: str | None = None,
    reviewed_at: str = "2026-08-13T00:00:01Z",
) -> SegmentReviewEventsRow:
    corrected_sha = (
        None
        if corrected_text is None
        else hashlib.sha256(corrected_text.encode("utf-8")).hexdigest()
    )
    return SegmentReviewEventsRow(
        id=event_id,
        segment_id="segment-review",
        decision=decision,
        reviewer="fixture",
        rationale="fixture review",
        corrected_text=corrected_text,
        corrected_text_sha256=corrected_sha,
        review_metadata_json="{}",
        reviewed_at=reviewed_at,
    )


def _segment_snapshot(config: PersistenceConfig) -> tuple[str, str, str]:
    with sqlite3.connect(config.database_path) as connection:
        row = connection.execute(
            "SELECT text_inline, text_sha256, review_status FROM segments WHERE id='segment-review'"
        ).fetchone()
    assert row is not None
    return str(row[0]), str(row[1]), str(row[2])


def test_segment_review_accept_is_append_only_and_projects_status(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    before = _segment_snapshot(config)
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow:
        assert uow.provenance.record_segment_review_event(_review_event()) is True
        uow.commit()
    after = _segment_snapshot(config)
    assert before[:2] == after[:2]
    assert after[2] == "accepted"


def test_segment_review_correct_requires_non_empty_text(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow, pytest.raises(PersistenceIntegrityError):
        uow.provenance.record_segment_review_event(_review_event(decision="correct"))


def test_segment_review_correct_validates_sha(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    row = replace(_review_event(decision="correct", corrected_text="corrected"), corrected_text_sha256="f" * 64)
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow, pytest.raises(PersistenceIntegrityError):
        uow.provenance.record_segment_review_event(row)


def test_segment_review_correct_preserves_source_text(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    before = _segment_snapshot(config)
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow:
        uow.provenance.record_segment_review_event(_review_event(decision="correct", corrected_text="corrected interpretation"))
        uow.commit()
    after = _segment_snapshot(config)
    assert before[:2] == after[:2]
    assert after[2] == "corrected"


def test_segment_review_reject_projects_rejected(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow:
        uow.provenance.record_segment_review_event(_review_event(decision="reject"))
        uow.commit()
    assert _segment_snapshot(config)[2] == "rejected"


def test_segment_review_invalid_vocabulary_is_rejected(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow, pytest.raises(PersistenceIntegrityError):
        uow.provenance.record_segment_review_event(_review_event(decision="approve"))


def test_segment_review_unknown_segment_fk_is_rejected(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    row = replace(_review_event(), segment_id="missing-segment")
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow, pytest.raises(PersistenceIntegrityError):
        uow.provenance.record_segment_review_event(row)


def test_segment_review_history_order_and_out_of_order_replay(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    newer = _review_event(event_id="review-2", decision="reject", reviewed_at="2026-08-13T00:00:02Z")
    older = _review_event(event_id="review-1", decision="accept", reviewed_at="2026-08-13T00:00:01Z")
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow:
        assert uow.provenance.record_segment_review_event(newer) is True
        assert uow.provenance.record_segment_review_event(older) is True
        history = uow.provenance.get_segment_review_events("segment-review")
        uow.commit()
    assert [row.id for row in history] == ["review-1", "review-2"]
    assert _segment_snapshot(config)[2] == "rejected"


def test_segment_review_idempotent_replay_does_not_regress(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    newer = _review_event(event_id="review-2", decision="reject", reviewed_at="2026-08-13T00:00:02Z")
    older = _review_event(event_id="review-1", decision="accept", reviewed_at="2026-08-13T00:00:01Z")
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow:
        uow.provenance.add_segment_review_events([older, newer])
        assert uow.provenance.record_segment_review_event(older) is False
        uow.commit()
    assert _segment_snapshot(config)[2] == "rejected"


def test_segment_review_event_identity_conflict_is_rejected(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_segment_for_review(config)
    row = _review_event()
    with SQLiteScientificFoundationUnitOfWork(config, repo_root=repo, artifact_store=artifacts) as uow:
        assert uow.provenance.record_segment_review_event(row) is True
        with pytest.raises(DuplicateIdentityConflict):
            uow.provenance.record_segment_review_event(
                replace(row, rationale="changed")
            )


def _seed_claim_for_review(config: PersistenceConfig) -> None:
    with sqlite3.connect(config.database_path) as connection:
        connection.execute(
            "INSERT INTO knowledge_sources "
            "(id, source_type, canonical_locator, title, author, language, description, imported_at, source_metadata_json, logical_identity_sha256, created_at) "
            "VALUES ('source-claim-review', 'test', 'urn:test:claim-review', 'review', NULL, 'en', '', ?, '{}', ?, ?)",
            (CREATED_AT, "2" * 64, CREATED_AT),
        )
        connection.execute(
            "INSERT INTO source_claims "
            "(id, source_id, representation_id, parent_claim_id, claim_layer, claim_text, claim_text_sha256, claim_kind, semantic_type, qualifiers_json, extraction_confidence_decimal, source_claim_effective_text_sha256, notes, initial_review_status, created_at) "
            "VALUES ('claim-review', 'source-claim-review', NULL, NULL, 'extracted', 'original claim', ?, 'fixture', 'fixture', '{}', NULL, ?, '', 'pending', ?)",
            (
                hashlib.sha256(b"original claim").hexdigest(),
                hashlib.sha256(b"original claim").hexdigest(),
                CREATED_AT,
            ),
        )


def _claim_review_event(
    *,
    event_id: str = "claim-review-event-1",
    decision: str = "accept",
    corrected_text: str | None = None,
    reviewed_at: str = "2026-08-13T00:00:01Z",
) -> ClaimReviewEventsRow:
    corrected_sha = (
        None
        if corrected_text is None
        else hashlib.sha256(corrected_text.encode("utf-8")).hexdigest()
    )
    return ClaimReviewEventsRow(
        id=event_id,
        claim_id="claim-review",
        decision=decision,
        reviewer="fixture",
        notes="fixture rationale",
        corrected_text=corrected_text,
        corrected_text_sha256=corrected_sha,
        review_metadata_json="{}",
        reviewed_at=reviewed_at,
    )


def test_v4_acquisition_job_can_start_without_source(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    row = AcquisitionJobsRow(
        id="job-before-source",
        source_id=None,
        adapter_name="fixture",
        adapter_version="1",
        requested_locator="urn:test:not-yet-resolved",
        requested_language=None,
        preferred_languages_json="[]",
        maximum_input_bytes=None,
        outcome="running",
        request_json="{}",
        diagnostics_json="[]",
        started_at=CREATED_AT,
        completed_at=None,
        created_at=CREATED_AT,
    )
    with SQLiteScientificFoundationUnitOfWork(
        config, repo_root=repo, artifact_store=artifacts
    ) as uow:
        assert uow.provenance.add_acquisition_job(row) is True
        uow.commit()

    with sqlite3.connect(config.database_path) as connection:
        stored = connection.execute(
            "SELECT source_id, outcome FROM acquisition_jobs WHERE id=?",
            (row.id,),
        ).fetchone()
    assert stored == (None, "running")


def test_v4_failed_acquisition_job_can_remain_source_less(tmp_path: Path) -> None:
    config, _, _ = _config_and_artifacts(tmp_path)
    with sqlite3.connect(config.database_path) as connection:
        connection.execute(
            "INSERT INTO acquisition_jobs "
            "(id, source_id, adapter_name, adapter_version, requested_locator, "
            "requested_language, preferred_languages_json, maximum_input_bytes, "
            "outcome, request_json, diagnostics_json, started_at, completed_at, created_at) "
            "VALUES ('job-failed-before-source', NULL, 'fixture', '1', 'urn:test:fail', "
            "NULL, '[]', NULL, 'failed', '{}', '[]', ?, ?, ?)",
            (CREATED_AT, CREATED_AT, CREATED_AT),
        )
        row = connection.execute(
            "SELECT source_id, outcome FROM acquisition_jobs "
            "WHERE id='job-failed-before-source'"
        ).fetchone()
    assert row == (None, "failed")


def test_claim_review_correction_is_explicit_and_append_only(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_claim_for_review(config)
    corrected = "corrected effective claim"
    event = _claim_review_event(decision="correct", corrected_text=corrected)

    with SQLiteScientificFoundationUnitOfWork(
        config, repo_root=repo, artifact_store=artifacts
    ) as uow:
        assert uow.provenance.record_claim_review_event(event) is True
        history = uow.provenance.get_claim_review_events("claim-review")
        original = uow.provenance.get_source_claim("claim-review")
        uow.commit()

    assert original is not None
    assert original.claim_text == "original claim"
    assert [item.id for item in history] == [event.id]
    assert history[0].corrected_text == corrected
    assert history[0].corrected_text_sha256 == hashlib.sha256(
        corrected.encode("utf-8")
    ).hexdigest()


def test_claim_review_correction_requires_text_and_valid_sha(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_claim_for_review(config)

    with SQLiteScientificFoundationUnitOfWork(
        config, repo_root=repo, artifact_store=artifacts
    ) as uow:
        with pytest.raises(PersistenceIntegrityError):
            uow.provenance.record_claim_review_event(
                _claim_review_event(decision="correct")
            )
        with pytest.raises(PersistenceIntegrityError):
            uow.provenance.record_claim_review_event(
                replace(
                    _claim_review_event(
                        decision="correct",
                        corrected_text="corrected",
                    ),
                    corrected_text_sha256="f" * 64,
                )
            )


def test_claim_review_history_order_is_deterministic(tmp_path: Path) -> None:
    config, artifacts, repo = _config_and_artifacts(tmp_path)
    _seed_claim_for_review(config)
    later = _claim_review_event(
        event_id="claim-review-event-2",
        decision="reject",
        reviewed_at="2026-08-13T00:00:02Z",
    )
    earlier = _claim_review_event(
        event_id="claim-review-event-1",
        decision="accept",
        reviewed_at="2026-08-13T00:00:01Z",
    )
    with SQLiteScientificFoundationUnitOfWork(
        config, repo_root=repo, artifact_store=artifacts
    ) as uow:
        assert uow.provenance.record_claim_review_event(later) is True
        assert uow.provenance.record_claim_review_event(earlier) is True
        history = uow.provenance.get_claim_review_events("claim-review")
        uow.commit()
    assert [item.id for item in history] == [
        "claim-review-event-1",
        "claim-review-event-2",
    ]
