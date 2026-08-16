from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionContext,
    AcquisitionRequest,
    AcquisitionResult,
    AcquisitionValidationError,
    AdapterMatch,
    AdapterRegistry,
    AmbiguousAdapterError,
    CanonicalSource,
    RetrievedPayload,
    validate_acquisition_result,
)
from ecobiome.knowledge_acquisition.adapters.local_file import LocalFileAdapter
from ecobiome.knowledge_acquisition.collector_acquire import (
    acquire_source,
    default_adapter_registry,
)
from ecobiome.knowledge_acquisition.collector_cli import main as collector_main
from ecobiome.knowledge_acquisition.persistence import CollectorStore


@dataclass
class _FakeAdapter:
    name: str
    priority: int
    version: str = "1"

    def match(self, request: AcquisitionRequest) -> AdapterMatch | None:
        return AdapterMatch(self.priority, f"fake:{self.name}")

    def canonicalize(self, request: AcquisitionRequest) -> CanonicalSource:
        return CanonicalSource("other", request.locator, request.locator)

    def acquire(
        self,
        request: AcquisitionRequest,
        context: AcquisitionContext,
    ) -> AcquisitionResult:
        del request, context
        raise AssertionError("not used by registry-only test")


def _count(database: Path, table: str) -> int:
    with sqlite3.connect(database) as connection:
        return int(
            connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        )


def test_registry_selects_unique_highest_priority() -> None:
    registry = AdapterRegistry(
        (
            _FakeAdapter("low", 10),
            _FakeAdapter("high", 100),
        )
    )

    adapter, match = registry.select(
        AcquisitionRequest("fixture")
    )

    assert adapter.name == "high"
    assert match.priority == 100
    assert match.reason == "fake:high"


def test_registry_rejects_equal_priority_ambiguity() -> None:
    registry = AdapterRegistry(
        (
            _FakeAdapter("a", 100),
            _FakeAdapter("b", 100),
        )
    )

    with pytest.raises(AmbiguousAdapterError):
        registry.select(AcquisitionRequest("fixture"))


def test_http_source_routes_to_generic_web_without_network() -> None:
    adapter, match = default_adapter_registry().select(
        AcquisitionRequest("https://example.invalid/source")
    )

    assert adapter.name == "web-page"
    assert match.reason == "generic_public_http_or_https_url"


def test_local_file_acquisition_persists_v2_provenance(
    tmp_path: Path,
) -> None:
    source = tmp_path / "observations.txt"
    source.write_text(
        "Water temperature was stable.\n\nPlants provided cover.",
        encoding="utf-8",
    )
    database = tmp_path / "collector.sqlite3"

    run = acquire_source(
        source=str(source),
        database=database,
        language="en",
        maximum_passage_characters=40,
    )

    assert run.adapter_name == "local-file"
    assert run.result.canonical_source.canonical_locator == source.as_uri()
    assert run.result.canonical_source.language == "en"

    assert len(run.receipt.payloads) == 1
    assert len(run.receipt.representations) == 1
    representation = run.receipt.representations[0]
    assert not representation.duplicate
    assert len(representation.segment_ids) == 2
    assert representation.segment_review_statuses == ("pending", "pending")

    store = CollectorStore(database)
    summary = store.summary()
    assert summary["sources"] == 1
    assert summary["raw_artifacts"] == 1
    assert summary["retrievals"] == 1
    assert summary["representations"] == 1
    assert summary["representation_derivations"] == 1
    assert summary["segments"] == 2
    assert summary["acquisition_jobs"] == 1

    raw = run.receipt.payloads[0]
    assert raw.stored_path.is_file()
    assert raw.stored_path.read_bytes() == source.read_bytes()

    assert representation.stored_path.is_file()
    assert representation.stored_path.read_text(encoding="utf-8") == (
        source.read_text(encoding="utf-8")
    )


def test_exact_reacquisition_deduplicates_content_and_preserves_review(
    tmp_path: Path,
) -> None:
    source = tmp_path / "notes.md"
    source.write_text("One stable observation.", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"

    first = acquire_source(
        source=str(source),
        database=database,
    )
    first_representation = first.receipt.representations[0]
    segment_id = first_representation.segment_ids[0]

    store = CollectorStore(database)
    store.record_review_decision(
        target_type="passage",
        target_id=segment_id,
        decision="accept",
    )

    second = acquire_source(
        source=str(source),
        database=database,
    )
    second_representation = second.receipt.representations[0]

    assert second.receipt.source_id == first.receipt.source_id
    assert second_representation.representation_id == (
        first_representation.representation_id
    )
    assert second_representation.duplicate
    assert second_representation.segment_ids == (segment_id,)
    assert second_representation.segment_review_statuses == ("accepted",)

    summary = store.summary()
    assert summary["raw_artifacts"] == 1
    assert summary["representations"] == 1
    assert summary["segments"] == 1
    assert summary["retrievals"] == 2
    assert summary["acquisition_jobs"] == 2


def test_changed_local_file_creates_new_snapshot_same_logical_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "observations.txt"
    database = tmp_path / "collector.sqlite3"

    source.write_text("Version one.", encoding="utf-8")
    first = acquire_source(source=str(source), database=database)

    source.write_text("Version two.", encoding="utf-8")
    second = acquire_source(source=str(source), database=database)

    assert second.receipt.source_id == first.receipt.source_id
    assert (
        second.receipt.payloads[0].raw_artifact_id
        != first.receipt.payloads[0].raw_artifact_id
    )
    assert (
        second.receipt.representations[0].representation_id
        != first.receipt.representations[0].representation_id
    )

    store = CollectorStore(database)
    summary = store.summary()
    assert summary["sources"] == 1
    assert summary["raw_artifacts"] == 2
    assert summary["retrievals"] == 2
    assert summary["representations"] == 2
    assert summary["acquisition_jobs"] == 2


def test_binary_like_file_fails_and_records_failed_job(
    tmp_path: Path,
) -> None:
    source = tmp_path / "binary.txt"
    source.write_bytes(b"abc\x00def")
    database = tmp_path / "collector.sqlite3"

    with pytest.raises(ValueError, match="binary-like"):
        acquire_source(source=str(source), database=database)

    store = CollectorStore(database)
    summary = store.summary()
    assert summary["acquisition_jobs"] == 1
    assert summary["failed_jobs"] == 1
    assert summary["job_diagnostics"] == 1
    assert summary["raw_artifacts"] == 0


def test_oversized_local_file_fails_before_canonical_persistence(
    tmp_path: Path,
) -> None:
    source = tmp_path / "large.txt"
    source.write_text("1234567890", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"

    with pytest.raises(ValueError, match="maximum_input_bytes"):
        acquire_source(
            source=str(source),
            database=database,
            maximum_input_bytes=5,
        )

    store = CollectorStore(database)
    summary = store.summary()
    assert summary["failed_jobs"] == 1
    assert summary["raw_artifacts"] == 0
    assert summary["retrievals"] == 0


def test_adapter_result_cannot_escape_staging_directory(
    tmp_path: Path,
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    escaped = tmp_path / "escaped.txt"
    escaped.write_text("data", encoding="utf-8")

    result = AcquisitionResult(
        canonical_source=CanonicalSource(
            source_type="other",
            canonical_locator="file:///fixture",
            title="fixture",
        ),
        payloads=(
            RetrievedPayload(
                logical_key="raw",
                staged_path=escaped,
                media_type="text/plain",
                original_locator=str(escaped),
                canonical_locator="file:///fixture",
                protocol="file",
            ),
        ),
        representations=(),
    )

    with pytest.raises(AcquisitionValidationError, match="escaped"):
        validate_acquisition_result(
            result,
            staging_directory=staging,
        )



def test_local_file_adapter_matches_windows_drive_path() -> None:
    adapter = LocalFileAdapter()

    match = adapter.match(
        AcquisitionRequest(r"C:\\Users\\example\\observations.txt")
    )

    assert match is not None
    assert match.reason == "windows_local_drive_path"


def test_local_file_adapter_does_not_match_unc_network_path() -> None:
    adapter = LocalFileAdapter()

    match = adapter.match(
        AcquisitionRequest(r"\\\\server\\share\\observations.txt")
    )

    assert match is None

def test_local_file_adapter_rejects_unsupported_extension(
    tmp_path: Path,
) -> None:
    source = tmp_path / "binary.dat"
    source.write_text("text", encoding="utf-8")
    adapter = LocalFileAdapter()
    request = AcquisitionRequest(str(source))

    assert adapter.match(request) is not None
    with pytest.raises(ValueError, match="extension"):
        adapter.canonicalize(request)


def test_collector_cli_acquire_writes_manifest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "data.csv"
    source.write_text("species,value\nmedaka,24\n", encoding="utf-8")
    database = tmp_path / "collector.sqlite3"
    manifest_path = tmp_path / "manifest.json"

    code = collector_main(
        [
            "acquire",
            str(source),
            "--database",
            str(database),
            "--language",
            "en",
            "--output",
            str(manifest_path),
        ]
    )

    assert code == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert manifest["adapter"]["name"] == "local-file"
    assert manifest["job"]["status"] == "succeeded"
    assert manifest["source"]["canonical_locator"] == source.as_uri()
    assert len(manifest["raw_artifacts"]) == 1
    assert len(manifest["representations"]) == 1

    printed = json.loads(capsys.readouterr().out)
    assert printed["job"]["id"] == manifest["job"]["id"]
