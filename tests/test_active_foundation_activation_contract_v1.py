from __future__ import annotations

import json
from pathlib import Path

import pytest

from ecobiome.knowledge_persistence.active_foundation_activation_contract_v1 import (
    ActivationIdentitySetV1,
    ActivationPathSetV1,
    InjectedActivationFailure,
    audit_activation_paths_v1,
    audit_ancestor_chain_v1,
    build_pointer_from_runtime_policy_v1,
    first_activation_contract_document_v1,
    publish_pointer_dry_run_v1,
)
from ecobiome.knowledge_persistence.active_foundation_v1 import (
    AUTHORIZE_ACTIVE_SNAPSHOT,
    ActiveScientificFoundationRuntimePolicyV1,
    build_runtime_policy_document,
)
from ecobiome.knowledge_persistence.errors import (
    PersistenceConfigurationError,
    PersistenceIntegrityError,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
ZERO = "0" * 64


def _identities() -> ActivationIdentitySetV1:
    return ActivationIdentitySetV1(
        parent_database_sha256=A,
        snapshot_database_sha256=B,
        snapshot_manifest_file_sha256=C,
        snapshot_manifest_payload_sha256=D,
        pointer_contract_payload_sha256=E,
        resolver_code_sha256=F,
        consumer_migration_identity_sha256=ZERO,
    )


def _policy_document() -> dict[str, object]:
    identities = _identities()
    policy = ActiveScientificFoundationRuntimePolicyV1(
        activation_decision=AUTHORIZE_ACTIVE_SNAPSHOT,
        pointer_required=True,
        parent_database_sha256=identities.parent_database_sha256,
        snapshot_database_sha256=identities.snapshot_database_sha256,
        snapshot_manifest_file_sha256=(
            identities.snapshot_manifest_file_sha256
        ),
        snapshot_manifest_payload_sha256=(
            identities.snapshot_manifest_payload_sha256
        ),
        pointer_contract_payload_sha256=(
            identities.pointer_contract_payload_sha256
        ),
        resolver_code_sha256=identities.resolver_code_sha256,
        consumer_migration_identity_sha256=(
            identities.consumer_migration_identity_sha256
        ),
        created_at="2026-08-27T05:32:00+02:00",
    )
    return build_runtime_policy_document(policy)


def _pointer_document() -> dict[str, object]:
    document = _policy_document()
    expected_sha = document["runtime_policy_payload_sha256"]
    assert isinstance(expected_sha, str)
    return build_pointer_from_runtime_policy_v1(
        document,
        expected_runtime_policy_payload_sha256=expected_sha,
        expected_identities=_identities(),
    )


def test_policy_requires_independently_supplied_matching_sha() -> None:
    document = _policy_document()
    with pytest.raises(
        PersistenceIntegrityError,
        match="canonical/trusted SHA mismatch",
    ):
        build_pointer_from_runtime_policy_v1(
            document,
            expected_runtime_policy_payload_sha256="1" * 64,
            expected_identities=_identities(),
        )


def test_policy_identity_drift_fails_closed() -> None:
    document = _policy_document()
    expected_sha = document["runtime_policy_payload_sha256"]
    assert isinstance(expected_sha, str)
    wrong = ActivationIdentitySetV1(
        parent_database_sha256=A,
        snapshot_database_sha256="1" * 64,
        snapshot_manifest_file_sha256=C,
        snapshot_manifest_payload_sha256=D,
        pointer_contract_payload_sha256=E,
        resolver_code_sha256=F,
        consumer_migration_identity_sha256=ZERO,
    )
    with pytest.raises(
        PersistenceIntegrityError,
        match="snapshot_database_sha256",
    ):
        build_pointer_from_runtime_policy_v1(
            document,
            expected_runtime_policy_payload_sha256=expected_sha,
            expected_identities=wrong,
        )


@pytest.mark.parametrize(
    "failure_point",
    ["after_temp_write", "before_replace"],
)
def test_pre_replace_failures_leave_pointer_absent(
    tmp_path: Path,
    failure_point: str,
) -> None:
    target = tmp_path / "scientific-foundation-active.json"
    with pytest.raises(InjectedActivationFailure):
        publish_pointer_dry_run_v1(
            target,
            _pointer_document(),
            failure_point=failure_point,  # type: ignore[arg-type]
        )
    assert not target.exists()
    assert not list(tmp_path.glob(".scientific-foundation-active.json.tmp-*"))


def test_post_replace_failure_leaves_complete_pointer(
    tmp_path: Path,
) -> None:
    target = tmp_path / "scientific-foundation-active.json"
    document = _pointer_document()

    with pytest.raises(InjectedActivationFailure):
        publish_pointer_dry_run_v1(
            target,
            document,
            failure_point="after_replace_before_verify",
        )

    assert target.is_file()
    assert json.loads(target.read_text(encoding="utf-8")) == document


def test_successful_dry_run_publication_is_exact(
    tmp_path: Path,
) -> None:
    target = tmp_path / "scientific-foundation-active.json"
    document = _pointer_document()

    result = publish_pointer_dry_run_v1(target, document)

    assert result.target_path == target
    assert result.bytes_written == len(target.read_bytes())
    assert json.loads(target.read_text(encoding="utf-8")) == document


def test_rate3q_refuses_real_data_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ecobiome.knowledge_persistence import (
        active_foundation_activation_contract_v1 as module,
    )

    real_root = tmp_path / "real-data"
    real_root.mkdir()
    monkeypatch.setattr(module, "REAL_DATA_ROOT", real_root)

    with pytest.raises(
        PersistenceConfigurationError,
        match="forbids writes under the real EcoBiome data root",
    ):
        publish_pointer_dry_run_v1(
            real_root / "scientific-foundation-active.json",
            _pointer_document(),
        )


def test_ancestor_audit_rejects_link_like_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ecobiome.knowledge_persistence import (
        active_foundation_activation_contract_v1 as module,
    )

    first = tmp_path / "first"
    first.mkdir()
    leaf = first / "leaf.json"
    leaf.write_text("{}", encoding="utf-8")

    original = module._is_link_like

    def fake_is_link_like(path: Path) -> bool:
        if path == first:
            return True
        return original(path)

    monkeypatch.setattr(module, "_is_link_like", fake_is_link_like)

    with pytest.raises(
        PersistenceConfigurationError,
        match="symlink/junction/reparse point",
    ):
        audit_ancestor_chain_v1(leaf)


def test_activation_path_audit_covers_all_required_paths(
    tmp_path: Path,
) -> None:
    data = tmp_path / "data"
    cas = data / "scientific-artifact-cas"
    snapshots = data / "scientific-foundation-snapshots"
    snapshot_dir = snapshots / B
    legacy_dir = data / "scientific-foundation-v6"
    policy_dir = tmp_path / "trust-source"

    cas.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)
    legacy_dir.mkdir(parents=True)
    policy_dir.mkdir(parents=True)

    snapshot_db = snapshot_dir / "scientific-foundation.sqlite3"
    snapshot_manifest = snapshot_dir / "snapshot-manifest.json"
    legacy_db = legacy_dir / "scientific-foundation-v6.sqlite3"
    policy_path = policy_dir / "active-runtime-policy.json"

    for path in (
        snapshot_db,
        snapshot_manifest,
        legacy_db,
        policy_path,
    ):
        path.write_text("x", encoding="utf-8")

    result = audit_activation_paths_v1(
        ActivationPathSetV1(
            persistent_pointer_path=(
                data / "scientific-foundation-active.json"
            ),
            runtime_policy_path=policy_path,
            legacy_database_path=legacy_db,
            cas_root=cas,
            snapshot_root=snapshots,
            snapshot_directory=snapshot_dir,
            snapshot_database_path=snapshot_db,
            snapshot_manifest_path=snapshot_manifest,
        )
    )

    assert set(result) == {
        "persistent_pointer",
        "runtime_policy",
        "legacy_database",
        "cas_root",
        "snapshot_root",
        "snapshot_directory",
        "snapshot_database",
        "snapshot_manifest",
    }


def test_contract_keeps_persistent_activation_forbidden() -> None:
    contract = first_activation_contract_document_v1(
        expected_identities=_identities(),
    )
    boundary = contract["authorization_boundary"]
    assert isinstance(boundary, dict)
    assert boundary["persistent_active_pointer_write_authorized"] is False
    assert boundary["persistent_runtime_policy_publication_authorized"] is False
    rollback = contract["rollback"]
    assert isinstance(rollback, dict)
    assert rollback["separate_human_review_required"] is True
