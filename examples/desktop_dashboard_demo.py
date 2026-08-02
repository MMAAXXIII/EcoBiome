"""Launch a populated EcoBiome desktop-dashboard demonstration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from ecobiome.dashboard import build_project_dashboard
from ecobiome.journal import JournalEventType
from ecobiome.media import MediaMetadata
from ecobiome.ui.desktop import (
    DesktopDashboardViewModel,
    run_desktop_dashboard,
)
from ecobiome.workspace import (
    ProjectManifest,
    ProjectType,
    ProjectWorkspace,
)

NOW = datetime.now(UTC).replace(
    second=0,
    microsecond=0,
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def populate_demo_workspace(
    root: Path,
) -> ProjectWorkspace:
    """Create a realistic temporary aquarium workspace."""
    workspace = ProjectWorkspace.create(
        root,
        manifest=ProjectManifest(
            project_id=PROJECT_ID,
            name="Aquarium guppys",
            project_type=ProjectType.AQUARIUM,
            description=(
                "Suivi scientifique de la reproduction, "
                "de la qualité de l'eau et des alevins."
            ),
            created_at=NOW - timedelta(days=45),
            updated_at=NOW,
            tags=(
                "guppy",
                "aquarium",
                "reproduction",
            ),
            attributes=(
                ("volume_liters", "90"),
                ("location", "salon"),
            ),
        ),
    )

    workspace.journal.record(
        event_type=JournalEventType.BIOLOGICAL_EVENT,
        title="Naissance de mes premiers guppys",
        description=(
            "Premiers alevins observés près "
            "des plantes flottantes."
        ),
        occurred_at=NOW - timedelta(hours=3),
        project_id=PROJECT_ID,
        tags=("guppy", "alevins", "naissance"),
    )

    workspace.journal.record(
        event_type=JournalEventType.MEASUREMENT,
        title="Paramètres de l'eau relevés",
        description=(
            "Température 25,2 °C · pH 7,3 · "
            "conductivité 620 µS/cm."
        ),
        occurred_at=NOW - timedelta(hours=2),
        project_id=PROJECT_ID,
        tags=("eau", "mesure"),
    )

    workspace.journal.record(
        event_type=JournalEventType.DIAGNOSTIC,
        title="Diagnostic de l'aquarium terminé",
        description=(
            "Aucune contradiction critique détectée. "
            "Les paramètres sont compatibles avec les guppys."
        ),
        occurred_at=NOW - timedelta(hours=1),
        project_id=PROJECT_ID,
        tags=("diagnostic", "healthy"),
    )

    workspace.journal.record(
        event_type=JournalEventType.LEARNING,
        title="Hypothèse confirmée",
        description=(
            "La présence de plantes flottantes semble "
            "favoriser la protection des alevins."
        ),
        occurred_at=NOW - timedelta(minutes=35),
        project_id=PROJECT_ID,
        tags=("learning", "confirmed"),
    )

    workspace.journal.record(
        event_type=JournalEventType.NOTE,
        title="Observation du soir",
        description=(
            "Les alevins restent actifs et se déplacent "
            "principalement dans la partie supérieure."
        ),
        occurred_at=NOW - timedelta(minutes=10),
        project_id=PROJECT_ID,
        tags=("observation", "alevins"),
    )

    for index in range(1, 4):
        source = root.parent / f"guppy-{index}.jpg"
        source.write_bytes(
            f"demo-image-{index}".encode()
        )

        workspace.media.import_file(
            source,
            metadata=MediaMetadata(
                title=f"Photo des alevins {index}",
                captured_at=(
                    NOW
                    - timedelta(
                        hours=4 - index
                    )
                ),
                tags=("guppy", "alevins"),
            ),
            project_id=PROJECT_ID,
        )

    return workspace


def main() -> None:
    """Build and display the EcoBiome dashboard demonstration."""
    with TemporaryDirectory(
        prefix="ecobiome-dashboard-"
    ) as temporary_directory:
        workspace = populate_demo_workspace(
            Path(temporary_directory)
            / "aquarium-guppys"
        )

        snapshot = build_project_dashboard(
            workspace,
            latest_limit=8,
        )

        view_model = (
            DesktopDashboardViewModel.from_snapshot(
                snapshot
            )
        )

        run_desktop_dashboard(view_model)


if __name__ == "__main__":
    main()
