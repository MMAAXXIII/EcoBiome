"""Launch a populated EcoBiome desktop-dashboard demonstration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from PIL import Image, ImageDraw

from ecobiome.dashboard import build_project_dashboard
from ecobiome.journal import JournalEventType
from ecobiome.media import MediaMetadata
from ecobiome.ui.desktop import (
    DashboardLayoutStore,
    DesktopDashboardViewModel,
    DiagnosticAnalyticsViewModel,
    HypothesisDetailViewModel,
    build_media_gallery,
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

    hypothesis_titles = (
        "Capteur de luminance déréglé",
        "Source lumineuse parasite",
        "Réflexion environnementale",
        "Erreur de synchronisation",
        "Bruit électronique",
    )

    for index, hypothesis_title in enumerate(
        hypothesis_titles,
        start=1,
    ):
        workspace.journal.record(
            event_type=JournalEventType.HYPOTHESIS,
            title=hypothesis_title,
            description=(
                "Hypothèse générée automatiquement "
                "à partir des observations disponibles."
            ),
            occurred_at=(
                NOW
                - timedelta(
                    minutes=95 - index
                )
            ),
            project_id=PROJECT_ID,
            tags=("hypothèse", "diagnostic"),
        )

    experiment_titles = (
        "Test d'obscurité contrôlé",
        "Recalibrage du capteur",
        "Comparaison avec une source étalon",
    )

    for index, experiment_title in enumerate(
        experiment_titles,
        start=1,
    ):
        workspace.journal.record(
            event_type=JournalEventType.EXPERIMENT,
            title=experiment_title,
            description=(
                "Expérience proposée pour discriminer "
                "les hypothèses principales."
            ),
            occurred_at=(
                NOW
                - timedelta(
                    minutes=70 - index
                )
            ),
            project_id=PROJECT_ID,
            tags=("expérience", "diagnostic"),
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

    image_palettes = (
        (
            "#0B2D3D",
            "#27A6A1",
            "#7CE3B3",
        ),
        (
            "#192E29",
            "#4E9A55",
            "#C3DA7A",
        ),
        (
            "#25304B",
            "#7156B8",
            "#E4A8F4",
        ),
    )

    for index, palette in enumerate(
        image_palettes,
        start=1,
    ):
        source = (
            root.parent
            / f"guppy-{index}.png"
        )

        image = Image.new(
            "RGB",
            (720, 420),
            palette[0],
        )

        drawing = ImageDraw.Draw(image)

        drawing.ellipse(
            (
                80 + index * 25,
                90,
                480 + index * 25,
                310,
            ),
            fill=palette[1],
        )

        drawing.polygon(
            (
                (445 + index * 25, 200),
                (610, 90 + index * 15),
                (610, 310 - index * 15),
            ),
            fill=palette[2],
        )

        drawing.ellipse(
            (
                180 + index * 25,
                145,
                205 + index * 25,
                170,
            ),
            fill="#FFFFFF",
        )

        drawing.text(
            (28, 25),
            f"EcoBiome · Alevins {index}",
            fill="#FFFFFF",
        )

        drawing.text(
            (28, 370),
            "Aquarium guppys · Démonstration",
            fill=palette[2],
        )

        image.save(
            source,
            format="PNG",
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
            quality_score=82,
        )

        view_model = (
            DesktopDashboardViewModel.from_snapshot(
                snapshot
            )
        )

        gallery_items = build_media_gallery(
            workspace.layout.media_directory,
            limit=8,
        )

        analytics = DiagnosticAnalyticsViewModel(
            quality_score=82,
            quality_history=(
                58,
                62,
                66,
                64,
                71,
                74,
                79,
                77,
                82,
            ),
            high_quality_count=18,
            medium_quality_count=6,
            low_quality_count=2,
            rejected_count=1,
            hypotheses=(
                HypothesisDetailViewModel(
                    identifier="H1",
                    title="Capteur de luminance déréglé",
                    explanation=(
                        "Les écarts observés sont compatibles "
                        "avec une dérive progressive du capteur."
                    ),
                    recommendation=(
                        "Recalibrer le capteur puis répéter "
                        "trois mesures avec une source étalon."
                    ),
                    probability=78,
                    accent="#70D68D",
                ),
                HypothesisDetailViewModel(
                    identifier="H2",
                    title="Source lumineuse parasite",
                    explanation=(
                        "Une lumière extérieure pourrait "
                        "contaminer les mesures en obscurité."
                    ),
                    recommendation=(
                        "Effectuer un test dans une chambre "
                        "complètement occultée."
                    ),
                    probability=64,
                    accent="#4FA4FF",
                ),
                HypothesisDetailViewModel(
                    identifier="H3",
                    title="Réflexion environnementale",
                    explanation=(
                        "Les parois claires peuvent réfléchir "
                        "une partie du flux lumineux."
                    ),
                    recommendation=(
                        "Répéter l'expérience avec des parois "
                        "mates et sombres."
                    ),
                    probability=46,
                    accent="#A78BFA",
                ),
                HypothesisDetailViewModel(
                    identifier="H4",
                    title="Erreur de synchronisation",
                    explanation=(
                        "Le capteur et la caméra pourraient "
                        "enregistrer à des instants différents."
                    ),
                    recommendation=(
                        "Synchroniser les horodatages avant "
                        "une nouvelle acquisition."
                    ),
                    probability=31,
                    accent="#F2A65A",
                ),
                HypothesisDetailViewModel(
                    identifier="H5",
                    title="Bruit électronique",
                    explanation=(
                        "Le niveau de bruit est présent mais "
                        "semble insuffisant pour expliquer "
                        "l'ensemble des écarts."
                    ),
                    recommendation=(
                        "Réaliser une mesure de référence "
                        "avec l'entrée du capteur isolée."
                    ),
                    probability=18,
                    accent="#EC6B72",
                ),
            ),
        )

        layout_store = DashboardLayoutStore(
            path=(
                Path.home()
                / ".ecobiome"
                / "dashboard-layout.json"
            )
        )

        run_desktop_dashboard(
            view_model,
            gallery_items=gallery_items,
            analytics_view_model=analytics,
            layout_store=layout_store,
        )


if __name__ == "__main__":
    main()
