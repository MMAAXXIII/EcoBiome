"""Tests for the high-fidelity diagnostic dashboard layer."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.dashboard import (
    ProjectDashboardSnapshot,
    build_project_dashboard,
)
from ecobiome.journal import JournalEventType
from ecobiome.ui.desktop import (
    DesktopDashboardViewModel,
    ProbabilityBar,
)
from ecobiome.workspace import (
    ProjectManifest,
    ProjectType,
    ProjectWorkspace,
)

NOW = datetime(
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
    """Create one deterministic diagnostic workspace."""
    workspace = ProjectWorkspace.create(
        tmp_path / "diagnostic-project",
        manifest=ProjectManifest(
            project_id=PROJECT_ID,
            name="Aquarium guppys",
            project_type=ProjectType.AQUARIUM,
            created_at=NOW,
            updated_at=NOW,
        ),
    )

    workspace.journal.record(
        event_type=JournalEventType.OBSERVATION,
        title="Observation",
        occurred_at=NOW,
        project_id=PROJECT_ID,
    )

    for index in range(5):
        workspace.journal.record(
            event_type=JournalEventType.HYPOTHESIS,
            title=f"Hypothèse {index + 1}",
            occurred_at=NOW,
            project_id=PROJECT_ID,
        )

    for index in range(3):
        workspace.journal.record(
            event_type=JournalEventType.EXPERIMENT,
            title=f"Expérience {index + 1}",
            occurred_at=NOW,
            project_id=PROJECT_ID,
        )

    workspace.journal.record(
        event_type=JournalEventType.LEARNING,
        title="Conclusion",
        occurred_at=NOW,
        project_id=PROJECT_ID,
    )

    return workspace


def test_builder_exposes_diagnostic_kpi_counts(
    tmp_path: Path,
) -> None:
    snapshot = build_project_dashboard(
        make_workspace(tmp_path),
        quality_score=82,
    )

    assert snapshot.quality_score == 82
    assert snapshot.hypothesis_count == 5
    assert snapshot.experiment_count == 3
    assert snapshot.conclusion_count == 1


def test_builder_rejects_invalid_quality_score(
    tmp_path: Path,
) -> None:
    workspace = make_workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="between zero and one hundred",
    ):
        build_project_dashboard(
            workspace,
            quality_score=101,
        )


def test_snapshot_rejects_invalid_quality_score() -> None:
    with pytest.raises(
        ValueError,
        match="between zero and one hundred",
    ):
        ProjectDashboardSnapshot(
            project_id=PROJECT_ID,
            project_name="Aquarium",
            project_type=ProjectType.AQUARIUM,
            description="",
            updated_at=NOW,
            tags=(),
            journal_event_count=0,
            media_file_count=0,
            diagnostic_count=0,
            learning_count=0,
            biological_event_count=0,
            event_counts=(),
            latest_activity=(),
            quality_score=-1,
        )


def test_view_model_matches_reference_kpi_order(
    tmp_path: Path,
) -> None:
    snapshot = build_project_dashboard(
        make_workspace(tmp_path),
        quality_score=82,
    )

    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            snapshot
        )
    )

    assert tuple(
        metric.label
        for metric in view_model.metrics
    ) == (
        "Observations",
        "Qualité globale",
        "Hypothèses",
        "Expériences",
        "Conclusions",
    )

    assert tuple(
        metric.value
        for metric in view_model.metrics
    ) == (
        "10",
        "82%",
        "5",
        "3",
        "1",
    )


def test_quality_is_not_invented_when_absent(
    tmp_path: Path,
) -> None:
    snapshot = build_project_dashboard(
        make_workspace(tmp_path)
    )

    view_model = (
        DesktopDashboardViewModel.from_snapshot(
            snapshot
        )
    )

    quality_metric = view_model.metrics[1]

    assert quality_metric.label == "Qualité globale"
    assert quality_metric.value == "—"
    assert quality_metric.detail == "Mesure à compléter"


def test_probability_bar_validates_probability() -> None:
    probability = ProbabilityBar(
        identifier="H1",
        label="Capteur de luminance déréglé",
        probability=78,
        accent="#70D68D",
    )

    assert probability.probability == 78

    with pytest.raises(
        ValueError,
        match="between zero and one hundred",
    ):
        ProbabilityBar(
            identifier="H2",
            label="Invalid",
            probability=120,
            accent="#FFFFFF",
        )
