"""Tests for durable EcoBiome project workspaces."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.journal import JournalEventType
from ecobiome.media import MediaMetadata
from ecobiome.workspace import (
    ProjectManifest,
    ProjectType,
    ProjectWorkspace,
    ProjectWorkspaceLayout,
    project_manifest_from_dict,
    project_manifest_to_dict,
)

CREATED_AT = datetime(
    2026,
    8,
    2,
    20,
    0,
    tzinfo=UTC,
)

UPDATED_AT = CREATED_AT + timedelta(hours=1)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_manifest() -> ProjectManifest:
    """Create one deterministic project manifest."""
    return ProjectManifest(
        project_id=PROJECT_ID,
        name=" Aquarium guppys ",
        project_type=ProjectType.AQUARIUM,
        description=" Suivi de mes guppys et alevins. ",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        tags=(
            "Guppy",
            "Aquarium",
            "guppy",
        ),
        attributes=(
            ("volume_liters", "90"),
            ("location", "salon"),
        ),
    )


def test_manifest_normalizes_project_metadata() -> None:
    manifest = make_manifest()

    assert manifest.name == "Aquarium guppys"
    assert manifest.description == (
        "Suivi de mes guppys et alevins."
    )

    assert manifest.tags == (
        "guppy",
        "aquarium",
    )

    assert manifest.attribute_map == {
        "volume_liters": "90",
        "location": "salon",
    }


def test_manifest_survives_primitive_round_trip() -> None:
    manifest = make_manifest()

    payload = project_manifest_to_dict(manifest)
    restored = project_manifest_from_dict(payload)

    assert restored == manifest
    assert payload["project_type"] == "aquarium"
    assert payload["project_id"] == str(PROJECT_ID)


def test_workspace_creation_builds_expected_layout(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    workspace = ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    assert workspace.layout.root == root
    assert workspace.layout.manifest_path.is_file()
    assert workspace.layout.journal_directory.is_dir()
    assert workspace.layout.media_directory.is_dir()
    assert workspace.layout.exports_directory.is_dir()
    assert workspace.layout.cache_directory.is_dir()


def test_workspace_reopens_with_same_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    reopened = ProjectWorkspace.open(root)

    assert reopened.manifest == make_manifest()
    assert reopened.manifest.project_id == PROJECT_ID


def test_duplicate_workspace_creation_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    with pytest.raises(
        FileExistsError,
        match="already exists",
    ):
        ProjectWorkspace.create(
            root,
            manifest=make_manifest(),
        )


def test_missing_workspace_manifest_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="does not exist",
    ):
        ProjectWorkspace.open(
            tmp_path / "missing"
        )


def test_workspace_journal_survives_restart(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    workspace = ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    event = workspace.journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title="Naissance de mes premiers guppys",
        description="Premiers alevins observés.",
        occurred_at=CREATED_AT,
        project_id=PROJECT_ID,
        tags=("guppy", "alevins"),
    )

    reopened = ProjectWorkspace.open(root)

    assert reopened.journal.timeline() == (event,)
    assert reopened.journal.get(event.event_id) == event


def test_workspace_media_uses_project_directory(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    workspace = ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    source = tmp_path / "guppys.jpg"
    source.write_bytes(b"guppy-image")

    asset = workspace.media.import_file(
        source,
        metadata=MediaMetadata(
            title="Premiers alevins",
            captured_at=CREATED_AT,
            tags=("guppy", "alevins"),
        ),
        project_id=PROJECT_ID,
    )

    assert asset.stored_path.is_file()
    assert workspace.layout.media_directory in (
        asset.stored_path.parents
    )


def test_workspace_integrations_record_media_in_journal(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    workspace = ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    source = tmp_path / "birth.jpg"
    source.write_bytes(b"birth-image")

    asset = workspace.media.import_file(
        source,
        metadata=MediaMetadata(
            title="Naissance de mes premiers guppys",
            captured_at=CREATED_AT,
            tags=("guppy", "naissance"),
        ),
        project_id=PROJECT_ID,
    )

    journal_event = (
        workspace.integrations.media.record_import(
            asset
        )
    )

    assert journal_event.project_id == PROJECT_ID
    assert journal_event.title == asset.metadata.title
    assert workspace.journal.timeline() == (
        journal_event,
    )


def test_journal_integration_idempotence_survives_restart(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    workspace = ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    source = tmp_path / "birth.jpg"
    source.write_bytes(b"persistent-birth-image")

    asset = workspace.media.import_file(
        source,
        metadata=MediaMetadata(
            title="Guppy birth",
            captured_at=CREATED_AT,
        ),
        project_id=PROJECT_ID,
    )

    first_event = (
        workspace.integrations.media.record_import(
            asset
        )
    )

    reopened = ProjectWorkspace.open(root)

    second_event = (
        reopened.integrations.media.record_import(
            asset
        )
    )

    assert second_event == first_event
    assert reopened.journal.timeline() == (
        first_event,
    )


def test_manifest_update_is_persisted(
    tmp_path: Path,
) -> None:
    root = tmp_path / "aquarium-guppys"

    workspace = ProjectWorkspace.create(
        root,
        manifest=make_manifest(),
    )

    updated = workspace.update_manifest(
        name="Aquarium guppys principal",
        description="Suivi complet de la reproduction.",
        tags=("guppy", "reproduction"),
        attributes=(
            ("volume_liters", "90"),
            ("population", "25"),
        ),
        updated_at=UPDATED_AT,
    )

    reopened = ProjectWorkspace.open(root)

    assert reopened.manifest == updated
    assert reopened.manifest.name == (
        "Aquarium guppys principal"
    )
    assert reopened.manifest.updated_at == UPDATED_AT
    assert reopened.manifest.attribute_map[
        "population"
    ] == "25"


def test_manifest_rejects_naive_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        ProjectManifest(
            name="Invalid project",
            project_type=ProjectType.OTHER,
            created_at=CREATED_AT.replace(
                tzinfo=None
            ),
            updated_at=CREATED_AT,
        )


def test_manifest_rejects_backward_update_time() -> None:
    with pytest.raises(
        ValueError,
        match="cannot precede",
    ):
        ProjectManifest(
            name="Invalid project",
            project_type=ProjectType.OTHER,
            created_at=CREATED_AT,
            updated_at=CREATED_AT - timedelta(seconds=1),
        )


def test_layout_paths_are_deterministic(
    tmp_path: Path,
) -> None:
    layout = ProjectWorkspaceLayout(
        tmp_path / "project"
    )

    assert layout.manifest_path == (
        layout.root / "workspace.json"
    )

    assert layout.journal_path == (
        layout.root
        / "journal"
        / "events.jsonl"
    )

    assert layout.media_directory == (
        layout.root / "media"
    )
