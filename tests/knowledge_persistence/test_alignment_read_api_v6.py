from pathlib import Path

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
from ecobiome.knowledge_persistence.serialization import (
    canonical_assertion_payload,
    canonical_sha256,
)

CREATED_AT = "2026-08-21T00:00:00Z"


def _setup(
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


def test_assertion_root_and_claim_link_read_api_round_trip(
    tmp_path: Path,
) -> None:
    config, artifacts, repo = _setup(tmp_path)

    source = KnowledgeSourcesRow(
        id="source-1",
        source_type="fixture",
        canonical_locator="urn:fixture:source",
        title="fixture",
        author=None,
        language="en",
        description="",
        imported_at=CREATED_AT,
        source_metadata_json="{}",
        logical_identity_sha256="1" * 64,
        created_at=CREATED_AT,
    )
    claim = SourceClaimsRow(
        id="claim-1",
        source_id=source.id,
        representation_id=None,
        parent_claim_id=None,
        claim_layer="atomic",
        claim_text="fixture mechanism claim",
        claim_text_sha256="2" * 64,
        claim_kind="fixture",
        semantic_type="fixture",
        qualifiers_json="{}",
        extraction_confidence_decimal=None,
        source_claim_effective_text_sha256="2" * 64,
        notes="",
        initial_review_status="reviewed_fixture",
        created_at=CREATED_AT,
    )
    root = ScientificAssertionsRow(
        id="assertion-1",
        created_at=CREATED_AT,
        retired_at=None,
    )
    assertion_payload = canonical_assertion_payload(
        assertion_kind="relational",
        predicate="fixture_direct_mechanism",
        participants=[],
        value={"kind": "none"},
        qualifiers={},
    )
    revision = ScientificAssertionRevisionsRow(
        assertion_id=root.id,
        revision=1,
        schema_version="scientific-assertion-v1.1",
        assertion_kind="relational",
        predicate="fixture_direct_mechanism",
        participants_json="[]",
        value_json='{"kind":"none"}',
        qualifiers_json="{}",
        normalized_text="fixture mechanism",
        canonical_payload_sha256=canonical_sha256(assertion_payload),
        created_at=CREATED_AT,
    )
    link = AssertionClaimLinksRow(
        id="link-1",
        assertion_id=root.id,
        assertion_revision=revision.revision,
        claim_id=claim.id,
        stance="supports",
        support_mode="direct_observation",
        scope_alignment="exact",
        semantic_alignment="exact",
        review_status="reviewed_fixture",
        reviewed_by="fixture-reviewer",
        reviewed_at=CREATED_AT,
        created_at=CREATED_AT,
    )

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.provenance.add_knowledge_source(source)
        assert uow.provenance.add_source_claims([claim]) == 1
        assert uow.assertions.add_assertion(root)
        assert uow.assertions.add_assertion_revision(revision)
        assert uow.assertions.add_assertion_claim_link(link)
        uow.commit()

    with SQLiteScientificFoundationUnitOfWork(
        config,
        repo_root=repo,
        artifact_store=artifacts,
    ) as uow:
        assert uow.assertions.get_assertion(root.id) == root
        assert (
            uow.assertions.get_assertion_revision(
                root.id,
                revision.revision,
            )
            == revision
        )
        assert uow.assertions.find_by_canonical_payload_sha256(
            revision.canonical_payload_sha256
        ) == (revision,)
        assert uow.assertions.list_assertion_claim_links(
            root.id,
            revision.revision,
        ) == (link,)
