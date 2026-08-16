"""Local N7 ecology state and append-only operation journal.

This application persistence deliberately stays outside the Scientific Foundation
schema. Static topology continues to live in EcosystemProfileV1; changing user
state and operational history live here until a future canonical core seam is
explicitly frozen.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import cast

from ecobiome.knowledge_persistence.serialization import (
    canonical_json_text,
    canonical_sha256,
    normalize_decimal,
)

ECOLOGY_STATE_SCHEMA_V1 = "ecobiome-local-ecology-state-v1"
ECOLOGY_OPERATION_SCHEMA_V1 = "ecobiome-local-ecology-operation-v1"


def ecology_dir(project_dir: Path) -> Path:
    return project_dir / "ecology"


def state_path(project_dir: Path) -> Path:
    return ecology_dir(project_dir) / "state.json"


def operations_path(project_dir: Path) -> Path:
    return ecology_dir(project_dir) / "events.jsonl"


def empty_state() -> dict[str, object]:
    return {
        "schema_version": ECOLOGY_STATE_SCHEMA_V1,
        "livestock": [],
        "plants": [],
        "water_sources": [],
        "substrate_layers": [],
    }


def load_state(project_dir: Path) -> dict[str, object]:
    path = state_path(project_dir)
    if not path.exists():
        return empty_state()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("ecology state must be a JSON object")
    if raw.get("schema_version") != ECOLOGY_STATE_SCHEMA_V1:
        raise ValueError("unsupported ecology state schema")
    for field in ("livestock", "plants", "water_sources", "substrate_layers"):
        if not isinstance(raw.get(field), list):
            raise TypeError(f"ecology state {field} must be an array")
    return cast(dict[str, object], raw)


def save_state(project_dir: Path, state: dict[str, object]) -> None:
    if state.get("schema_version") != ECOLOGY_STATE_SCHEMA_V1:
        raise ValueError("invalid ecology state schema")
    path = state_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(canonical_json_text(state) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def decimal_text(value: float | str) -> str:
    return normalize_decimal(str(value))


def _validate_operation_event(
    event: dict[str, object],
    *,
    project_id: str,
    previous_sha: str | None,
) -> str:
    if event.get("schema_version") != ECOLOGY_OPERATION_SCHEMA_V1:
        raise ValueError("unsupported ecology operation schema")
    if event.get("project_id") != project_id:
        raise ValueError("ecology operation project identity mismatch")
    if event.get("previous_event_sha256") != previous_sha:
        raise ValueError("ecology operation hash chain mismatch")
    supplied = event.get("event_sha256")
    if not isinstance(supplied, str):
        raise TypeError("ecology operation event_sha256 must be a string")
    body = dict(event)
    del body["event_sha256"]
    actual = canonical_sha256(body)
    if supplied != actual:
        raise ValueError("ecology operation SHA-256 mismatch")
    return supplied


def read_operations(project_dir: Path, project_id: str) -> list[dict[str, object]]:
    path = operations_path(project_dir)
    if not path.exists():
        return []
    result: list[dict[str, object]] = []
    previous_sha: str | None = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise TypeError(f"ecology operation line {line_number} must be an object")
        event = cast(dict[str, object], raw)
        previous_sha = _validate_operation_event(
            event,
            project_id=project_id,
            previous_sha=previous_sha,
        )
        result.append(event)
    return result


def append_operation(
    project_dir: Path,
    *,
    project_id: str,
    event_id: str,
    occurred_at: datetime,
    operation_type: str,
    details: dict[str, object],
    note: str = "",
    subject_id: str | None = None,
) -> dict[str, object]:
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("ecology operation occurred_at must be timezone-aware")
    operation_type = operation_type.strip()
    if not operation_type:
        raise ValueError("operation_type must be non-empty")
    prior = read_operations(project_dir, project_id)
    previous_sha = (
        cast(str, prior[-1]["event_sha256"])
        if prior
        else None
    )
    body: dict[str, object] = {
        "schema_version": ECOLOGY_OPERATION_SCHEMA_V1,
        "project_id": project_id,
        "event_id": event_id,
        "occurred_at": occurred_at.isoformat(),
        "operation_type": operation_type,
        "subject_id": subject_id,
        "details": details,
        "note": note.strip(),
        "previous_event_sha256": previous_sha,
    }
    event = dict(body)
    event["event_sha256"] = canonical_sha256(body)
    path = operations_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json_text(event) + "\n")
    return event
