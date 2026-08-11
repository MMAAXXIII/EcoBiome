"""Unified access to one durable EcoBiome project workspace."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ecobiome.integrations.journal import (
    JournalIntegrationService,
)
from ecobiome.journal import (
    JsonlJournalEventStore,
    ScientificJournal,
)
from ecobiome.media import (
    LocalMediaStorage,
    MediaLibrary,
)
from ecobiome.workspace.layout import ProjectWorkspaceLayout
from ecobiome.workspace.manifest import ProjectManifest
from ecobiome.workspace.serializers import (
    read_project_manifest,
    write_project_manifest,
)


class ProjectWorkspace:
    """Group project metadata, media and journal persistence."""

    def __init__(
        self,
        *,
        layout: ProjectWorkspaceLayout,
        manifest: ProjectManifest,
    ) -> None:
        self._layout = layout
        self._manifest = manifest

        self._journal = ScientificJournal(
            JsonlJournalEventStore(
                layout.journal_path
            )
        )

        self._media_library = MediaLibrary(
            LocalMediaStorage(
                layout.media_directory
            ),
            index_path=layout.media_index_path,
        )

        self._integrations = JournalIntegrationService(
            self._journal
        )

    @classmethod
    def create(
        cls,
        root: str | Path,
        *,
        manifest: ProjectManifest,
    ) -> ProjectWorkspace:
        """Create a new project workspace."""
        layout = ProjectWorkspaceLayout(
            Path(root)
        )

        if layout.manifest_path.exists():
            raise FileExistsError(
                "A project workspace already exists at "
                f"{layout.root}."
            )

        layout.create_directories()

        write_project_manifest(
            layout.manifest_path,
            manifest,
        )

        return cls(
            layout=layout,
            manifest=manifest,
        )

    @classmethod
    def open(
        cls,
        root: str | Path,
    ) -> ProjectWorkspace:
        """Open an existing project workspace."""
        layout = ProjectWorkspaceLayout(
            Path(root)
        )

        manifest = read_project_manifest(
            layout.manifest_path
        )

        layout.create_directories()

        return cls(
            layout=layout,
            manifest=manifest,
        )

    @property
    def layout(self) -> ProjectWorkspaceLayout:
        """Return the workspace filesystem layout."""
        return self._layout

    @property
    def manifest(self) -> ProjectManifest:
        """Return the current project manifest."""
        return self._manifest

    @property
    def journal(self) -> ScientificJournal:
        """Return the persistent scientific journal."""
        return self._journal

    @property
    def media(self) -> MediaLibrary:
        """Return the project media library."""
        return self._media_library

    @property
    def integrations(self) -> JournalIntegrationService:
        """Return automatic journal integration bridges."""
        return self._integrations

    def update_manifest(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        tags: tuple[str, ...] | None = None,
        attributes: tuple[tuple[str, str], ...] | None = None,
        updated_at: datetime | None = None,
    ) -> ProjectManifest:
        """Update and persist project metadata."""
        updated_manifest = self._manifest.updated(
            name=name,
            description=description,
            tags=tags,
            attributes=attributes,
            updated_at=updated_at,
        )

        write_project_manifest(
            self._layout.manifest_path,
            updated_manifest,
        )

        self._manifest = updated_manifest

        return updated_manifest
