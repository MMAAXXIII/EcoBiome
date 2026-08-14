"""Orchestration for source-agnostic EcoBiome Collector acquisition."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionContext,
    AcquisitionRequest,
    AcquisitionResult,
    AdapterMatch,
    AdapterRegistry,
    CanonicalSource,
    validate_acquisition_result,
)
from ecobiome.knowledge_acquisition.adapters import LocalFileAdapter, YouTubeAdapter
from ecobiome.knowledge_acquisition.persistence import (
    AcquisitionReceipt,
    CollectorStore,
)


@dataclass(frozen=True, slots=True)
class AcquisitionRun:
    """One completed adapter selection/acquisition/persistence run."""

    adapter_name: str
    adapter_version: str
    match: AdapterMatch
    result: AcquisitionResult
    receipt: AcquisitionReceipt


def default_adapter_registry() -> AdapterRegistry:
    """Return the deterministic built-in acquisition adapter registry."""
    return AdapterRegistry((YouTubeAdapter(), LocalFileAdapter()))


def acquire_source(
    *,
    source: str,
    database: str | Path,
    language: str = "",
    preferred_languages: tuple[str, ...] = (),
    maximum_input_bytes: int = 8 * 1024 * 1024,
    maximum_passage_characters: int = 1500,
    registry: AdapterRegistry | None = None,
) -> AcquisitionRun:
    """Acquire one source through an adapter and persist it durably."""
    if maximum_input_bytes <= 0:
        raise ValueError("maximum_input_bytes must be greater than zero")
    if maximum_passage_characters <= 0:
        raise ValueError(
            "maximum_passage_characters must be greater than zero"
        )

    request = AcquisitionRequest(
        locator=source,
        language=language,
        preferred_languages=preferred_languages,
        maximum_input_bytes=maximum_input_bytes,
    )
    selected_registry = registry or default_adapter_registry()
    adapter, match = selected_registry.select(request)
    canonical: CanonicalSource = adapter.canonicalize(request)

    store = CollectorStore(database)
    job_id = store.begin_acquisition_job(
        requested_locator=source,
        job_kind="acquire",
        adapter_name=adapter.name,
        adapter_version=adapter.version,
    )

    try:
        store.database_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="ecobiome-acquire-",
            dir=store.database_path.parent,
        ) as temporary:
            context = AcquisitionContext(
                staging_directory=Path(temporary),
                maximum_input_bytes=maximum_input_bytes,
            )
            result = adapter.acquire(request, context)
            validate_acquisition_result(
                result,
                staging_directory=context.staging_directory,
            )
            if (
                result.canonical_source.source_type != canonical.source_type
                or result.canonical_source.canonical_locator
                != canonical.canonical_locator
            ):
                raise RuntimeError(
                    "Adapter logical source identity changed between "
                    "canonicalize and acquire."
                )

            receipt = store.persist_acquisition_result(
                job_id=job_id,
                result=result,
                adapter_name=adapter.name,
                adapter_version=adapter.version,
                maximum_passage_characters=maximum_passage_characters,
            )
            store.finish_acquisition_job(
                job_id,
                status=result.outcome,
                source_id=receipt.source_id,
                diagnostics=result.diagnostics,
            )
    except Exception as exc:
        store.finish_acquisition_job(
            job_id,
            status="failed",
            diagnostics=(),
            error_code="acquire_failed",
            error_message=f"{type(exc).__name__}: {exc}",
        )
        raise

    return AcquisitionRun(
        adapter_name=adapter.name,
        adapter_version=adapter.version,
        match=match,
        result=result,
        receipt=receipt,
    )
