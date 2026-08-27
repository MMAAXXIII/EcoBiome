from __future__ import annotations

from pathlib import Path
from typing import Any

from ecobiome.knowledge_persistence.active_foundation_v1 import (
    ResolvedScientificFoundationV1,
)
from ecobiome.reasoning import nitrogen_vertical_runtime_v1 as runtime


class _Sentinel:
    pass


def _resolved(
    tmp_path: Path,
    database_sha256: str,
) -> ResolvedScientificFoundationV1:
    return ResolvedScientificFoundationV1(
        resolution_mode="active_snapshot",
        database_path=tmp_path / "foundation.sqlite3",
        database_sha256=database_sha256,
        schema_version=6,
        schema_design_sha256=(
            runtime.SCIENTIFIC_FOUNDATION_V6_DESIGN_SHA256
        ),
        snapshot_manifest_path=tmp_path / "snapshot-manifest.json",
        snapshot_manifest_file_sha256="1" * 64,
        snapshot_manifest_payload_sha256="2" * 64,
        pointer_payload_sha256="3" * 64,
        activation_authorization_payload_sha256="4" * 64,
        runtime_policy_payload_sha256="4" * 64,
    )


def test_resolved_builder_uses_resolved_snapshot_identity(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    database_sha = "9" * 64
    resolved = _resolved(tmp_path, database_sha)
    sentinel = _Sentinel()
    observed: dict[str, object] = {}

    monkeypatch.setattr(
        runtime,
        "validate_resolved_scientific_foundation_read_only",
        lambda value: value.database_path,
    )

    def fake_build(
        path: Path,
        *,
        scientific_foundation_snapshot: object,
        require_frozen_demonstration_identity: bool,
    ) -> _Sentinel:
        observed["path"] = path
        observed["snapshot"] = scientific_foundation_snapshot
        observed["require_frozen"] = (
            require_frozen_demonstration_identity
        )
        return sentinel

    monkeypatch.setattr(
        runtime,
        "_build_g7a_nitrogen_vertical_demonstration_v1",
        fake_build,
    )

    result = runtime.build_resolved_g7a_nitrogen_vertical_demonstration_v1(
        resolved
    )
    assert result is sentinel
    assert observed["path"] == resolved.database_path
    snapshot = observed["snapshot"]
    assert isinstance(
        snapshot,
        runtime.ScientificFoundationSnapshotRefV1,
    )
    assert snapshot.database_sha256 == database_sha
    assert snapshot.schema_version == 6
    assert observed["require_frozen"] is False


def test_resolved_historical_v6_preserves_frozen_identity_guard(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    resolved = _resolved(
        tmp_path,
        runtime.SCIENTIFIC_FOUNDATION_V6_SHA256,
    )
    sentinel = _Sentinel()
    observed: dict[str, object] = {}

    monkeypatch.setattr(
        runtime,
        "validate_resolved_scientific_foundation_read_only",
        lambda value: value.database_path,
    )

    def fake_build(
        path: Path,
        *,
        scientific_foundation_snapshot: object,
        require_frozen_demonstration_identity: bool,
    ) -> _Sentinel:
        observed["require_frozen"] = (
            require_frozen_demonstration_identity
        )
        return sentinel

    monkeypatch.setattr(
        runtime,
        "_build_g7a_nitrogen_vertical_demonstration_v1",
        fake_build,
    )

    result = runtime.build_resolved_g7a_nitrogen_vertical_demonstration_v1(
        resolved
    )
    assert result is sentinel
    assert observed["require_frozen"] is True
