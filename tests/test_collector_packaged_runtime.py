# Regression coverage for PR #10 post-review persistence findings.

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.collector_cli import build_parser
from ecobiome.knowledge_persistence.collector_compat import (
    CollectorStoreCompatibilityFacade,
)
from ecobiome.knowledge_persistence.config import (
    PersistenceConfig,
    PersistenceConfigurationError,
)


def test_persistence_config_without_repo_context_accepts_runtime_paths(
    tmp_path: Path,
) -> None:
    config = PersistenceConfig(
        database_path=tmp_path / "data" / "collector.sqlite3",
        artifact_store_root=tmp_path / "data" / "collector.cas",
    )
    assert config.validated() is config


def test_persistence_config_with_repo_context_keeps_repo_boundary_guard(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config = PersistenceConfig(
        database_path=repo_root / "collector.sqlite3",
        artifact_store_root=tmp_path / "collector.cas",
    )
    with pytest.raises(
        PersistenceConfigurationError,
        match="DB/CAS must remain outside Git repository",
    ):
        config.validated(repo_root)


def test_collector_store_initializes_outside_git_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_cwd = tmp_path / "runtime-cwd"
    runtime_cwd.mkdir()
    monkeypatch.chdir(runtime_cwd)
    monkeypatch.delenv("ECOBIOME_REPO_ROOT", raising=False)

    database = tmp_path / "runtime-data" / "collector.sqlite3"
    store = CollectorStoreCompatibilityFacade(database)

    assert store._repo_root() is None
    store.initialize()
    assert store.schema_version() == 2

    with sqlite3.connect(database) as connection:
        metadata = connection.execute(
            "SELECT schema_version FROM sf_schema_metadata "
            "WHERE schema_name='scientific_foundation'"
        ).fetchone()
    assert metadata == (4,)


def test_collector_init_help_describes_fresh_only_database_contract() -> None:
    help_text = " ".join(build_parser().format_help().split())

    assert "Create or validate a fresh-only Collector SQLite database." in help_text
    assert "Create or migrate a Collector SQLite database." not in help_text
