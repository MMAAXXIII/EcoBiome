from fastapi import FastAPI
from pathlib import Path

from ecobiome.dashboard.builder import build_project_dashboard
from ecobiome.workspace.workspace import ProjectWorkspace
from ecobiome.workspace.manifest import ProjectManifest
from ecobiome.workspace.project_type import ProjectType

app = FastAPI()

@app.get("/dashboard")
def get_dashboard():
    root = Path("./workspace")

    # Si le workspace n'existe pas encore -> on le crée
    if not root.exists():
        manifest = ProjectManifest(
            name="EcoBiome Project",
            description="Workspace auto-généré pour le dashboard",
            project_type=ProjectType.OTHER,
            tags=("ecobiome",),
            attributes=(),
        )

        workspace = ProjectWorkspace.create(
            root=root,
            manifest=manifest,
        )
    else:
        # Sinon -> on l'ouvre
        workspace = ProjectWorkspace.open(root=root)

    dashboard = build_project_dashboard(workspace)
    return dashboard
