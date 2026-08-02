"""JSON serialization for EcoBiome project manifests."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ecobiome.workspace.manifest import ProjectManifest
from ecobiome.workspace.project_type import ProjectType


def project_manifest_to_dict(
    manifest: ProjectManifest,
) -> dict[str, Any]:
    """Convert one manifest to JSON-compatible primitives."""
    return {
        "schema_version": manifest.schema_version,
        "project_id": str(manifest.project_id),
        "name": manifest.name,
        "project_type": manifest.project_type.value,
        "description": manifest.description,
        "created_at": manifest.created_at.isoformat(),
        "updated_at": manifest.updated_at.isoformat(),
        "tags": list(manifest.tags),
        "attributes": [
            [key, value]
            for key, value in manifest.attributes
        ],
    }


def _decode_attribute_pair(
    item: Any,
) -> tuple[str, str]:
    """Decode one ordered project attribute pair."""
    if (
        not isinstance(item, list)
        or len(item) != 2
    ):
        raise TypeError(
            "Project manifest attribute entries must be "
            "two-item arrays."
        )

    return (
        str(item[0]),
        str(item[1]),
    )


def project_manifest_from_dict(
    payload: dict[str, Any],
) -> ProjectManifest:
    """Rebuild one project manifest from primitive data."""
    raw_tags = payload["tags"]
    raw_attributes = payload["attributes"]

    if not isinstance(raw_tags, list):
        raise TypeError(
            "Project manifest tags must be a JSON array."
        )

    if not isinstance(raw_attributes, list):
        raise TypeError(
            "Project manifest attributes must be a JSON array."
        )

    return ProjectManifest(
        schema_version=int(payload["schema_version"]),
        project_id=UUID(str(payload["project_id"])),
        name=str(payload["name"]),
        project_type=ProjectType(
            str(payload["project_type"])
        ),
        description=str(payload["description"]),
        created_at=datetime.fromisoformat(
            str(payload["created_at"])
        ),
        updated_at=datetime.fromisoformat(
            str(payload["updated_at"])
        ),
        tags=tuple(
            str(tag)
            for tag in raw_tags
        ),
        attributes=tuple(
            _decode_attribute_pair(item)
            for item in raw_attributes
        ),
    )


def write_project_manifest(
    path: str | Path,
    manifest: ProjectManifest,
) -> None:
    """Write one project manifest atomically."""
    destination = Path(path)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    serialized = json.dumps(
        project_manifest_to_dict(manifest),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    temporary.write_text(
        serialized + "\n",
        encoding="utf-8",
    )

    temporary.replace(destination)


def read_project_manifest(
    path: str | Path,
) -> ProjectManifest:
    """Load one project manifest from disk."""
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(
            f"Project manifest does not exist: {source}."
        )

    try:
        payload = json.loads(
            source.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid project manifest JSON: {error.msg}."
        ) from error

    if not isinstance(payload, dict):
        raise TypeError(
            "Project manifest must contain a JSON object."
        )

    try:
        return project_manifest_from_dict(payload)
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            f"Invalid project manifest: {error}."
        ) from error
