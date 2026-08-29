"""Local HTTP API bridging EcoBiome workspaces to the Bolt frontend."""

from __future__ import annotations

import json
import os
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from ecobiome.dashboard import build_project_dashboard
from ecobiome.knowledge_persistence.active_foundation_runtime_config_v2 import (
    resolve_default_scientific_foundation_v1,
)
from ecobiome.knowledge_persistence.active_foundation_v2 import (
    ResolvedScientificFoundationV1,
)
from ecobiome.reasoning.human_readable_nitrogen_explanation_v1 import (
    build_human_readable_nitrogen_explanation_v1,
)
from ecobiome.reasoning.nitrogen_vertical_runtime_v1 import (
    SCIENTIFIC_FOUNDATION_V6_SHA256,
    build_frozen_g7a_nitrogen_vertical_demonstration_v1,
    build_resolved_g7a_nitrogen_vertical_demonstration_v1,
)
from ecobiome.workspace import ProjectManifest, ProjectType, ProjectWorkspace

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
WORKSPACE_ENV = "ECOBIOME_WORKSPACE"
DEMO_DATA_ENV = "ECOBIOME_DEMO_DATA"
NITROGEN_SCIENTIFIC_FOUNDATION_ENV = "ECOBIOME_SCIENTIFIC_FOUNDATION_V6"


def resolve_nitrogen_scientific_foundation_path() -> Path:
    override = os.environ.get(NITROGEN_SCIENTIFIC_FOUNDATION_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (
        Path.home()
        / "Documents"
        / "EcoBiome-data"
        / "scientific-foundation-v6"
        / "scientific-foundation-v6.sqlite3"
    ).resolve()


def _render_nitrogen_demo_payload(
    demonstration: Any,
    *,
    scientific_foundation_sha256: str,
    resolution_mode: str,
) -> dict[str, Any]:
    artifact = demonstration.canonical_payload()
    boundary = artifact.get("model_boundary")
    if not isinstance(boundary, dict) or boundary != {
        "extent_is_explicit_input": True,
        "kinetic_or_rate_model_present": False,
        "dt_or_elapsed_time_prediction_present": False,
        "forecast_claim": False,
    }:
        raise RuntimeError(
            "nitrogen UI requires the frozen non-predictive model boundary"
        )
    human_explanation = build_human_readable_nitrogen_explanation_v1(artifact)
    technical_explanation = demonstration.auditable_explanation.render_text()
    return {
        "status": "reviewed_scenario",
        "artifact_sha256": demonstration.canonical_sha256,
        "scientific_foundation_sha256": scientific_foundation_sha256,
        "scientific_foundation_resolution_mode": resolution_mode,
        "non_predictive": True,
        "human_explanation": {
            "canonical_sha256": human_explanation.canonical_sha256,
            **human_explanation.canonical_payload(),
        },
        "technical_explanation": technical_explanation,
        "explanation": technical_explanation,
        "artifact": artifact,
    }


def _nitrogen_demo_payload_from_resolved(
    resolved: ResolvedScientificFoundationV1,
) -> dict[str, Any]:
    demonstration = build_resolved_g7a_nitrogen_vertical_demonstration_v1(
        resolved
    )
    return _render_nitrogen_demo_payload(
        demonstration,
        scientific_foundation_sha256=resolved.database_sha256,
        resolution_mode=resolved.resolution_mode,
    )


def _nitrogen_demo_payload(
    database_path: Path | None = None,
) -> dict[str, Any]:
    if database_path is not None:
        demonstration = build_frozen_g7a_nitrogen_vertical_demonstration_v1(
            database_path
        )
        return _render_nitrogen_demo_payload(
            demonstration,
            scientific_foundation_sha256=SCIENTIFIC_FOUNDATION_V6_SHA256,
            resolution_mode="explicit_legacy_override",
        )

    override = os.environ.get(NITROGEN_SCIENTIFIC_FOUNDATION_ENV)
    if override:
        path = resolve_nitrogen_scientific_foundation_path()
        demonstration = build_frozen_g7a_nitrogen_vertical_demonstration_v1(
            path
        )
        return _render_nitrogen_demo_payload(
            demonstration,
            scientific_foundation_sha256=SCIENTIFIC_FOUNDATION_V6_SHA256,
            resolution_mode="explicit_legacy_override",
        )

    return _nitrogen_demo_payload_from_resolved(
        resolve_default_scientific_foundation_v1()
    )

def resolve_workspace_path() -> Path:
    override = os.environ.get(WORKSPACE_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / "Documents" / "EcoBiome" / "Workspace").resolve()

def open_or_create_workspace(path: Path) -> ProjectWorkspace:
    if (path / "workspace.json").exists():
        return ProjectWorkspace.open(path)
    return ProjectWorkspace.create(
        path,
        manifest=ProjectManifest(
            name="EcoBiome",
            project_type=ProjectType.POND,
            description=(
                "Projet EcoBiome local. Ajoutez vos observations, medias et "
                "evenements pour alimenter progressivement le tableau de bord."
            ),
            tags=("local",),
        ),
    )

def _demo_enabled() -> bool:
    return os.environ.get(DEMO_DATA_ENV, "").strip().lower() in {
        "1", "true", "yes", "on"
    }

def _iso(day: int, hour: int = 12) -> str:
    return f"2026-08-{day:02d}T{hour:02d}:00:00+02:00"

def _demo_water_bodies() -> list[dict[str, Any]]:
    return [
        {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Bassin Medaka 250 L",
            "type": "pond",
            "volume_liters": 250,
            "status": "stable",
            "created_at": _iso(1),
            "updated_at": _iso(11, 7),
        },
        {
            "id": "22222222-2222-4222-8222-222222222222",
            "name": "Bac experimental 90 L",
            "type": "aquaponic",
            "volume_liters": 90,
            "status": "warning",
            "created_at": _iso(3),
            "updated_at": _iso(11, 6),
        },
    ]

def _demo_measurements() -> list[dict[str, Any]]:
    first = "11111111-1111-4111-8111-111111111111"
    second = "22222222-2222-4222-8222-222222222222"
    groups = [
        (first, "temperature", "degC", [24.1, 24.4, 24.8, 25.0]),
        (first, "ph", "", [7.6, 7.7, 7.8, 7.8]),
        (first, "oxygen", "mg/L", [7.4, 7.8, 8.0, 8.1]),
        (first, "nitrate", "mg/L", [7.0, 8.0, 9.0, 10.0]),
        (second, "temperature", "degC", [25.0, 25.4, 25.9, 26.2]),
        (second, "ph", "", [7.3, 7.2, 7.1, 7.0]),
        (second, "oxygen", "mg/L", [6.8, 6.4, 6.1, 5.9]),
        (second, "nitrate", "mg/L", [18.0, 22.0, 27.0, 31.0]),
    ]
    rows: list[dict[str, Any]] = []
    counter = 1
    for water_body_id, metric, unit, series in groups:
        for day, value in zip((8, 9, 10, 11), series, strict=True):
            rows.append(
                {
                    "id": f"00000000-0000-4000-8000-{counter:012d}",
                    "water_body_id": water_body_id,
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "recorded_at": _iso(day, 8),
                }
            )
            counter += 1
    return rows

def _demo_diagnostics() -> list[dict[str, Any]]:
    return [
        {
            "id": "33333333-3333-4333-8333-333333333331",
            "water_body_id": "11111111-1111-4111-8111-111111111111",
            "status": "healthy",
            "summary": "Parametres coherents et oxygene stable.",
            "root_cause": "",
            "confidence": 91,
            "created_at": _iso(11, 6),
        },
        {
            "id": "33333333-3333-4333-8333-333333333332",
            "water_body_id": "22222222-2222-4222-8222-222222222222",
            "status": "warning",
            "summary": "Baisse progressive de l'oxygene et hausse des nitrates.",
            "root_cause": "Charge biologique et brassage a verifier.",
            "confidence": 82,
            "created_at": _iso(11, 5),
        },
    ]

def _demo_findings() -> list[dict[str, Any]]:
    return [
        {
            "id": "44444444-4444-4444-8444-444444444441",
            "diagnostic_id": "33333333-3333-4333-8333-333333333332",
            "severity": "warning",
            "metric": "Oxygene",
            "observation": "5.9 mg/L au dernier releve.",
            "explanation": "La tendance descendante justifie une surveillance du brassage.",
            "causal_chain": ["brassage", "oxygene dissous", "stress biologique"],
        },
        {
            "id": "44444444-4444-4444-8444-444444444442",
            "diagnostic_id": "33333333-3333-4333-8333-333333333332",
            "severity": "info",
            "metric": "Nitrates",
            "observation": "31 mg/L au dernier releve.",
            "explanation": "La hausse est compatible avec une accumulation progressive.",
            "causal_chain": ["mineralisation", "nitrification", "nitrates"],
        },
    ]

def _demo_journal() -> list[dict[str, Any]]:
    return [
        {
            "id": "55555555-5555-4555-8555-555555555551",
            "title": "Mise en service du bassin",
            "source": "manual",
            "source_ref": "",
            "tags": ["bassin", "medaka", "baseline"],
            "summary": "Configuration initiale du bassin de 250 litres.",
            "content": "Bassin exterieur plante, filtration sous gravier et aeration.",
            "created_at": _iso(7, 18),
        },
        {
            "id": "55555555-5555-4555-8555-555555555552",
            "title": "Observation oxygene",
            "source": "manual",
            "source_ref": "",
            "tags": ["oxygene", "mesure"],
            "summary": "Serie de mesures de demonstration.",
            "content": "Donnees synthetiques pour le smoke-test visuel.",
            "created_at": _iso(10, 21),
        },
        {
            "id": "55555555-5555-4555-8555-555555555553",
            "title": "Hypothese sur le brassage",
            "source": "literature",
            "source_ref": "demo://ecobiome/runtime",
            "tags": ["hypothese", "brassage"],
            "summary": "Lien a tester entre brassage et oxygene dissous.",
            "content": "Hypothese synthetique, non persistante.",
            "created_at": _iso(11, 6),
        },
    ]

def _demo_media() -> list[dict[str, Any]]:
    ids = [
        ("66666666-6666-4666-8666-666666666661", "11111111-1111-4111-8111-111111111111", "Bassin principal", "photo", "bassin.svg"),
        ("66666666-6666-4666-8666-666666666662", "11111111-1111-4111-8111-111111111111", "Vegetation aquatique", "illustration", "plantes.svg"),
        ("66666666-6666-4666-8666-666666666663", "22222222-2222-4222-8222-222222222222", "Schema du bac test", "diagram", "bac.svg"),
    ]
    return [
        {
            "id": item_id,
            "water_body_id": water_body_id,
            "title": title,
            "kind": kind,
            "url": f"/api/demo-media/{filename}",
            "caption": "Illustration synthetique de demonstration.",
            "created_at": _iso(9 + index, 15),
        }
        for index, (item_id, water_body_id, title, kind, filename) in enumerate(ids)
    ]

def _demo_organisms() -> list[dict[str, Any]]:
    return [
        {
            "id": "77777777-7777-4777-8777-777777777771",
            "water_body_id": "11111111-1111-4111-8111-111111111111",
            "name": "Medaka",
            "kind": "animal",
            "population": 12,
            "health": 92,
            "created_at": _iso(8),
        },
        {
            "id": "77777777-7777-4777-8777-777777777772",
            "water_body_id": "11111111-1111-4111-8111-111111111111",
            "name": "Egeria densa",
            "kind": "plant",
            "population": 8,
            "health": 88,
            "created_at": _iso(8),
        },
        {
            "id": "77777777-7777-4777-8777-777777777773",
            "water_body_id": "22222222-2222-4222-8222-222222222222",
            "name": "Bacteries nitrifiantes",
            "kind": "bacteria",
            "population": 1,
            "health": 76,
            "created_at": _iso(8),
        },
    ]

def _demo_dashboard() -> dict[str, Any]:
    return {
        "description": "MODE DEMO - donnees synthetiques non persistantes.",
        "project_type": "pond",
        "tags": ["demo", "runtime", "bolt"],
        "journal_event_count": len(_demo_journal()),
        "media_file_count": len(_demo_media()),
        "diagnostic_count": len(_demo_diagnostics()),
        "hypothesis_count": 1,
        "experiment_count": 1,
        "conclusion_count": 1,
    }

def _demo_svg(name: str) -> bytes:
    labels = {
        "bassin.svg": ("Bassin Medaka", "#0f766e", "#67e8f9"),
        "plantes.svg": ("Vegetation aquatique", "#14532d", "#86efac"),
        "bac.svg": ("Bac experimental", "#1e3a8a", "#93c5fd"),
    }
    label, background, accent = labels.get(
        name, ("EcoBiome", "#0f172a", "#5eead4")
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800">'
        f'<rect width="1200" height="800" fill="{background}"/>'
        f'<circle cx="240" cy="320" r="160" fill="{accent}" opacity="0.28"/>'
        f'<circle cx="930" cy="230" r="210" fill="{accent}" opacity="0.16"/>'
        f'<text x="70" y="110" fill="#f8fafc" font-family="sans-serif" '
        f'font-size="54" font-weight="700">{label}</text>'
        '<text x="72" y="170" fill="#cbd5e1" font-family="sans-serif" '
        'font-size="28">EcoBiome - illustration de demonstration</text>'
        '</svg>'
    )
    return svg.encode("utf-8")

def _real_dashboard(workspace: ProjectWorkspace) -> dict[str, Any]:
    dashboard = build_project_dashboard(workspace)
    return {
        "description": dashboard.description,
        "project_type": dashboard.project_type.value,
        "tags": list(dashboard.tags),
        "journal_event_count": dashboard.journal_event_count,
        "media_file_count": dashboard.media_file_count,
        "diagnostic_count": dashboard.diagnostic_count,
        "hypothesis_count": dashboard.hypothesis_count,
        "experiment_count": dashboard.experiment_count,
        "conclusion_count": dashboard.conclusion_count,
    }

def _real_water_bodies(workspace: ProjectWorkspace) -> list[dict[str, Any]]:
    manifest = workspace.manifest
    attributes = manifest.attribute_map
    raw_type = manifest.project_type.value
    water_body_type = raw_type if raw_type in {"aquarium", "pond", "aquaponic"} else "pond"
    try:
        volume = float(attributes.get("volume_liters", "0"))
    except ValueError:
        volume = 0.0
    return [
        {
            "id": str(manifest.project_id),
            "name": manifest.name,
            "type": water_body_type,
            "volume_liters": volume,
            "status": "stable",
            "created_at": manifest.created_at.isoformat(),
            "updated_at": manifest.updated_at.isoformat(),
        }
    ]

def _real_journal(workspace: ProjectWorkspace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in reversed(workspace.journal.timeline()):
        event_type = event.event_type.value
        rows.append(
            {
                "id": str(event.event_id),
                "title": event.title,
                "source": "manual",
                "source_ref": "",
                "tags": [event_type, *event.tags],
                "summary": event.description or event.title,
                "content": event.description or event.title,
                "created_at": event.occurred_at.isoformat(),
            }
        )
    return rows

def _real_diagnostics(workspace: ProjectWorkspace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    project_id = str(workspace.manifest.project_id)
    for event in reversed(workspace.journal.timeline()):
        if event.event_type.value != "diagnostic":
            continue
        rows.append(
            {
                "id": str(event.event_id),
                "water_body_id": project_id,
                "status": "warning",
                "summary": event.description or event.title,
                "root_cause": "",
                "confidence": 0,
                "created_at": event.occurred_at.isoformat(),
            }
        )
    return rows

def _real_media(workspace: ProjectWorkspace) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    project_id = str(workspace.manifest.project_id)
    for asset in reversed(workspace.media.all()):
        tags = set(asset.metadata.tags)
        kind = "diagram" if "diagram" in tags else (
            "illustration" if "illustration" in tags else "photo"
        )
        rows.append(
            {
                "id": str(asset.asset_id),
                "water_body_id": project_id,
                "title": asset.metadata.title or asset.original_filename,
                "kind": kind,
                "url": f"/api/media/{asset.asset_id}/content",
                "caption": asset.metadata.description,
                "created_at": asset.imported_at.isoformat(),
            }
        )
    return rows

class EcoBiomeApiServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        workspace: ProjectWorkspace,
        demo_data: bool,
    ) -> None:
        self.workspace = workspace
        self.demo_data = demo_data
        super().__init__(server_address, EcoBiomeApiHandler)

class EcoBiomeApiHandler(BaseHTTPRequestHandler):
    server: EcoBiomeApiServer

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._route(parsed.path, parse_qs(parsed.query))
        except KeyError:
            self._send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        except (OSError, ValueError, RuntimeError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        if isinstance(payload, tuple):
            body, content_type = payload
            self._send_bytes(body, content_type)
        else:
            self._send_json(payload)

    def _route(
        self,
        path: str,
        query: dict[str, list[str]],
    ) -> object | tuple[bytes, str]:
        workspace = self.server.workspace
        demo = self.server.demo_data

        if path == "/api/health":
            return {
                "status": "ok",
                "mode": "demo" if demo else "workspace",
                "project_id": str(workspace.manifest.project_id),
            }
        if path == "/api/dashboard":
            return _demo_dashboard() if demo else _real_dashboard(workspace)
        if path == "/api/nitrogen-demo":
            return _nitrogen_demo_payload()
        if path == "/api/water-bodies":
            return _demo_water_bodies() if demo else _real_water_bodies(workspace)
        if path == "/api/measurements":
            rows = _demo_measurements() if demo else []
            wanted = query.get("water_body_id", [None])[0]
            return [row for row in rows if row["water_body_id"] == wanted] if wanted else rows
        if path == "/api/diagnostics":
            return _demo_diagnostics() if demo else _real_diagnostics(workspace)
        if path == "/api/diagnostic-findings":
            rows = _demo_findings() if demo else []
            wanted = query.get("diagnostic_id", [None])[0]
            return [row for row in rows if row["diagnostic_id"] == wanted] if wanted else rows
        if path == "/api/journal":
            return _demo_journal() if demo else _real_journal(workspace)
        if path == "/api/media":
            return _demo_media() if demo else _real_media(workspace)
        if path == "/api/organisms":
            rows = _demo_organisms() if demo else []
            wanted = query.get("water_body_id", [None])[0]
            return [row for row in rows if row["water_body_id"] == wanted] if wanted else rows
        if path.startswith("/api/demo-media/") and demo:
            return _demo_svg(path.removeprefix("/api/demo-media/")), "image/svg+xml; charset=utf-8"
        if path.startswith("/api/media/") and path.endswith("/content"):
            raw_id = path.removeprefix("/api/media/").removesuffix("/content")
            asset = workspace.media.get(UUID(raw_id))
            stored_path = asset.stored_path.resolve()
            media_root = workspace.layout.media_directory.resolve()
            if stored_path != media_root and media_root not in stored_path.parents:
                raise ValueError("Media path escapes the workspace media directory.")
            return stored_path.read_bytes(), asset.mime_type
        raise KeyError(path)

def start_api_server(
    workspace_path: Path | None = None,
    *,
    host: str = DEFAULT_API_HOST,
    port: int = DEFAULT_API_PORT,
    demo_data: bool | None = None,
) -> tuple[EcoBiomeApiServer, threading.Thread, Path]:
    path = (workspace_path or resolve_workspace_path()).resolve()
    workspace = open_or_create_workspace(path)
    demo = _demo_enabled() if demo_data is None else demo_data
    server = EcoBiomeApiServer((host, port), workspace=workspace, demo_data=demo)
    thread = threading.Thread(
        target=server.serve_forever,
        name="EcoBiomeLocalApi",
        daemon=True,
    )
    thread.start()
    return server, thread, path

def stop_api_server(
    server: EcoBiomeApiServer,
    thread: threading.Thread,
) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
