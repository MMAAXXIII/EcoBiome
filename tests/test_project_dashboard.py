"""Tests for EcoBiome project-dashboard snapshots."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.dashboard import (
    DashboardActivityItem,
    DashboardEventCount,
    ProjectDashboardSnapshot,
    build_project_dashboard,
    project_dashboard_to_dict,
)
from ecobiome.journal import JournalEventType
from ecobiome.media import MediaMetadata
from ecobiome.workspace import (
    ProjectManifest,
    ProjectType,
    ProjectWorkspace,
)

CREATED_AT = datetime(
    2026,
    8,
    2,
    20,
    0,
    tzinfo=UTC,
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_workspace(
    tmp_path: Path,
) -> ProjectWorkspace:
    """Create one deterministic dashboard-test workspace."""
    return ProjectWorkspace.create(
        tmp_path / "aquarium-guppys",
        manifest=ProjectManifest(
            project_id=PROJECT_ID,
            name="Aquarium guppys",
            project_type=ProjectType.AQUARIUM,
            description="Suivi des guppys et des alevins.",
            created_at=CREATED_AT,
            updated_at=CREATED_AT,
            tags=("guppy", "aquarium"),
            attributes=(
                ("volume_liters", "90"),
            ),
        ),
    )


def test_empty_workspace_has_empty_dashboard(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    dashboard = build_project_dashboard(workspace)

    assert dashboard.project_id == PROJECT_ID
    assert dashboard.project_name == "Aquarium guppys"
    assert dashboard.project_type is ProjectType.AQUARIUM
    assert dashboard.journal_event_count == 0
    assert dashboard.media_file_count == 0
    assert dashboard.diagnostic_count == 0
    assert dashboard.learning_count == 0
    assert dashboard.biological_event_count == 0
    assert dashboard.event_counts == ()
    assert dashboard.latest_activity == ()
    assert dashboard.has_activity is False
    assert dashboard.has_media is False


def test_dashboard_counts_journal_event_types(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    workspace.journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title="Naissance de mes premiers guppys",
        occurred_at=CREATED_AT,
        project_id=PROJECT_ID,
    )

    workspace.journal.record(
        event_type=JournalEventType.DIAGNOSTIC,
        title="Diagnostic terminé",
        occurred_at=CREATED_AT + timedelta(minutes=1),
        project_id=PROJECT_ID,
    )

    workspace.journal.record(
        event_type=JournalEventType.LEARNING,
        title="Hypothèse confirmée",
        occurred_at=CREATED_AT + timedelta(minutes=2),
        project_id=PROJECT_ID,
    )

    dashboard = build_project_dashboard(workspace)

    assert dashboard.journal_event_count == 3
    assert dashboard.diagnostic_count == 1
    assert dashboard.learning_count == 1
    assert dashboard.biological_event_count == 1

    assert dashboard.event_count_for(
        JournalEventType.DIAGNOSTIC
    ) == 1

    assert dashboard.event_count_for(
        JournalEventType.MEDIA
    ) == 0


def test_dashboard_event_counts_have_stable_enum_order(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    workspace.journal.record(
        event_type=JournalEventType.LEARNING,
        title="Learning",
        occurred_at=CREATED_AT,
    )

    workspace.journal.record(
        event_type=JournalEventType.MEDIA,
        title="Media",
        occurred_at=CREATED_AT + timedelta(minutes=1),
    )

    dashboard = build_project_dashboard(workspace)

    assert tuple(
        counter.event_type
        for counter in dashboard.event_counts
    ) == (
        JournalEventType.MEDIA,
        JournalEventType.LEARNING,
    )


def test_dashboard_latest_activity_is_newest_first(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    workspace.journal.record(
        event_type=JournalEventType.NOTE,
        title="First",
        occurred_at=CREATED_AT,
    )

    workspace.journal.record(
        event_type=JournalEventType.MEDIA,
        title="Second",
        occurred_at=CREATED_AT + timedelta(minutes=1),
    )

    workspace.journal.record(
        event_type=JournalEventType.DIAGNOSTIC,
        title="Third",
        occurred_at=CREATED_AT + timedelta(minutes=2),
    )

    dashboard = build_project_dashboard(
        workspace,
        latest_limit=2,
    )

    assert tuple(
        item.title
        for item in dashboard.latest_activity
    ) == (
        "Third",
        "Second",
    )


def test_dashboard_zero_latest_limit_returns_no_activity(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    workspace.journal.record(
        event_type=JournalEventType.NOTE,
        title="One note",
        occurred_at=CREATED_AT,
    )

    dashboard = build_project_dashboard(
        workspace,
        latest_limit=0,
    )

    assert dashboard.journal_event_count == 1
    assert dashboard.latest_activity == ()


def test_negative_latest_limit_is_rejected(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        build_project_dashboard(
            workspace,
            latest_limit=-1,
        )


def test_dashboard_counts_stored_media_files(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    first_source = tmp_path / "guppy-1.jpg"
    first_source.write_bytes(b"first-guppy-image")

    second_source = tmp_path / "guppy-2.jpg"
    second_source.write_bytes(b"second-guppy-image")

    workspace.media.import_file(
        first_source,
        metadata=MediaMetadata(
            title="Première photo",
            captured_at=CREATED_AT,
        ),
        project_id=PROJECT_ID,
    )

    workspace.media.import_file(
        second_source,
        metadata=MediaMetadata(
            title="Deuxième photo",
            captured_at=CREATED_AT,
        ),
        project_id=PROJECT_ID,
    )

    dashboard = build_project_dashboard(workspace)

    assert dashboard.media_file_count == 2
    assert dashboard.has_media is True


def test_media_count_survives_workspace_restart(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    source = tmp_path / "persistent-photo.jpg"
    source.write_bytes(b"persistent-media")

    workspace.media.import_file(
        source,
        metadata=MediaMetadata(
            title="Photo persistante",
            captured_at=CREATED_AT,
        ),
        project_id=PROJECT_ID,
    )

    reopened = ProjectWorkspace.open(
        workspace.layout.root
    )

    dashboard = build_project_dashboard(reopened)

    assert dashboard.media_file_count == 1
    assert dashboard.has_media is True


def test_dashboard_activity_preserves_event_metadata(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    event = workspace.journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title=" Naissance de guppys ",
        description=" Premiers alevins observés. ",
        occurred_at=CREATED_AT,
        tags=("Guppy", "Alevins"),
    )

    dashboard = build_project_dashboard(workspace)

    activity = dashboard.latest_activity[0]

    assert activity.event_id == event.event_id
    assert activity.title == "Naissance de guppys"
    assert activity.description == (
        "Premiers alevins observés."
    )
    assert activity.tags == (
        "guppy",
        "alevins",
    )


def test_dashboard_survives_workspace_restart(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    workspace.journal.record(
        event_type=JournalEventType.DIAGNOSTIC,
        title="Diagnostic aquarium",
        occurred_at=CREATED_AT,
        project_id=PROJECT_ID,
    )

    reopened = ProjectWorkspace.open(
        workspace.layout.root
    )

    dashboard = build_project_dashboard(reopened)

    assert dashboard.journal_event_count == 1
    assert dashboard.diagnostic_count == 1
    assert dashboard.latest_activity[0].title == (
        "Diagnostic aquarium"
    )


def test_dashboard_serialization_is_interface_ready(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    event = workspace.journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title="Naissance de mes premiers guppys",
        occurred_at=CREATED_AT,
        project_id=PROJECT_ID,
        tags=("guppy", "naissance"),
    )

    payload = project_dashboard_to_dict(
        build_project_dashboard(workspace)
    )

    assert payload["project"] == {
        "project_id": str(PROJECT_ID),
        "name": "Aquarium guppys",
        "project_type": "aquarium",
        "description": "Suivi des guppys et des alevins.",
        "updated_at": CREATED_AT.isoformat(),
        "tags": ["guppy", "aquarium"],
    }

    assert payload["summary"][
        "journal_event_count"
    ] == 1

    assert payload["summary"][
        "biological_event_count"
    ] == 1

    assert payload["latest_activity"][0][
        "event_id"
    ] == str(event.event_id)


def test_dashboard_models_reject_invalid_values() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        DashboardEventCount(
            event_type=JournalEventType.NOTE,
            count=-1,
        )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        DashboardActivityItem(
            event_id=PROJECT_ID,
            event_type=JournalEventType.NOTE,
            title="Invalid activity",
            description="",
            occurred_at=CREATED_AT.replace(
                tzinfo=None
            ),
        )


def test_dashboard_snapshot_validates_event_total() -> None:
    with pytest.raises(
        ValueError,
        match="must equal",
    ):
        ProjectDashboardSnapshot(
            project_id=PROJECT_ID,
            project_name="Aquarium guppys",
            project_type=ProjectType.AQUARIUM,
            description="",
            updated_at=CREATED_AT,
            tags=(),
            journal_event_count=2,
            media_file_count=0,
            diagnostic_count=0,
            learning_count=0,
            biological_event_count=0,
            event_counts=(
                DashboardEventCount(
                    event_type=JournalEventType.NOTE,
                    count=1,
                ),
            ),
            latest_activity=(),
        )
