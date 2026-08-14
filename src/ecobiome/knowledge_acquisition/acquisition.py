"""Source-agnostic acquisition contracts for EcoBiome Collector."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class AcquisitionError(RuntimeError):
    """Base error for acquisition orchestration failures."""


class UnsupportedSourceError(AcquisitionError):
    """No registered adapter can handle the requested source."""


class AmbiguousAdapterError(AcquisitionError):
    """More than one adapter matched at the same highest priority."""


class AcquisitionValidationError(AcquisitionError):
    """An adapter returned an internally inconsistent acquisition result."""


@dataclass(frozen=True, slots=True)
class AcquisitionRequest:
    """One source requested by the user or a future research orchestrator."""

    locator: str
    language: str = ""
    preferred_languages: tuple[str, ...] = ()
    maximum_input_bytes: int = 8 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class AdapterMatch:
    """Deterministic adapter-routing result, never scientific confidence."""

    priority: int
    reason: str


@dataclass(frozen=True, slots=True)
class CanonicalSource:
    """Logical source identity independent from any retrieved byte snapshot."""

    source_type: str
    canonical_locator: str
    title: str
    author: str = ""
    language: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AcquisitionDiagnostic:
    """Structured acquisition diagnostic separate from lifecycle status."""

    severity: str
    code: str
    message: str = ""
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievedPayload:
    """One exact retrieved payload staged outside the canonical CAS."""

    logical_key: str
    staged_path: Path
    media_type: str
    original_locator: str
    canonical_locator: str
    protocol: str
    request_metadata: dict[str, object] = field(default_factory=dict)
    response_metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SegmentDraft:
    """One adapter-provided segment with only authoritative anchors."""

    text: str
    start_char: int | None = None
    end_char: int | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    page_number: int | None = None
    frame_start: int | None = None
    frame_end: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RepresentationDraft:
    """One immutable derived representation staged by an adapter."""

    logical_key: str
    staged_path: Path
    representation_kind: str
    media_type: str
    language: str
    parent_payload_key: str
    derivation_method: str
    tool_name: str
    tool_version: str
    derivation_parameters: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)
    text: str | None = None
    segments: tuple[SegmentDraft, ...] = ()


@dataclass(frozen=True, slots=True)
class AcquisitionResult:
    """Structured adapter output validated before canonical persistence."""

    canonical_source: CanonicalSource
    payloads: tuple[RetrievedPayload, ...]
    representations: tuple[RepresentationDraft, ...]
    diagnostics: tuple[AcquisitionDiagnostic, ...] = ()
    outcome: str = "succeeded"


@dataclass(frozen=True, slots=True)
class AcquisitionContext:
    """Per-run staging and resource policy supplied by the orchestrator."""

    staging_directory: Path
    maximum_input_bytes: int


class AcquisitionAdapter(Protocol):
    """Source adapter contract.

    Adapters may read sources and write only inside the provided staging
    directory. They must not open the Collector SQLite database or write to
    the canonical content-addressed store.
    """

    name: str
    version: str

    def match(self, request: AcquisitionRequest) -> AdapterMatch | None:
        """Return deterministic routing metadata or None."""
        ...

    def canonicalize(self, request: AcquisitionRequest) -> CanonicalSource:
        """Return logical source identity without persisting anything."""
        ...

    def acquire(
        self,
        request: AcquisitionRequest,
        context: AcquisitionContext,
    ) -> AcquisitionResult:
        """Retrieve/derive staged artifacts without persistence side effects."""
        ...


class AdapterRegistry:
    """Deterministically select one acquisition adapter."""

    def __init__(self, adapters: tuple[AcquisitionAdapter, ...] = ()) -> None:
        self._adapters = list(adapters)

    def register(self, adapter: AcquisitionAdapter) -> None:
        """Register one adapter."""
        self._adapters.append(adapter)

    @property
    def adapters(self) -> tuple[AcquisitionAdapter, ...]:
        """Return registered adapters in registration order."""
        return tuple(self._adapters)

    def select(
        self,
        request: AcquisitionRequest,
    ) -> tuple[AcquisitionAdapter, AdapterMatch]:
        """Select exactly one highest-priority adapter."""
        matches: list[tuple[AcquisitionAdapter, AdapterMatch]] = []
        for adapter in self._adapters:
            match = adapter.match(request)
            if match is not None:
                matches.append((adapter, match))

        if not matches:
            raise UnsupportedSourceError(
                f"No Collector acquisition adapter supports: {request.locator}"
            )

        highest = max(match.priority for _, match in matches)
        winners = [
            (adapter, match)
            for adapter, match in matches
            if match.priority == highest
        ]
        if len(winners) != 1:
            names = ", ".join(
                sorted(adapter.name for adapter, _ in winners)
            )
            raise AmbiguousAdapterError(
                "Multiple acquisition adapters matched at priority "
                f"{highest}: {names}"
            )
        return winners[0]


def validate_acquisition_result(
    result: AcquisitionResult,
    *,
    staging_directory: Path,
) -> None:
    """Validate adapter output without touching SQLite or canonical storage."""
    if result.outcome not in {"succeeded", "partial"}:
        raise AcquisitionValidationError(
            "Adapter result outcome must be succeeded or partial."
        )

    payload_keys: set[str] = set()
    staging_root = staging_directory.resolve()

    for payload in result.payloads:
        if not payload.logical_key:
            raise AcquisitionValidationError(
                "Payload logical_key must not be empty."
            )
        if payload.logical_key in payload_keys:
            raise AcquisitionValidationError(
                f"Duplicate payload logical key: {payload.logical_key}"
            )
        payload_keys.add(payload.logical_key)

        path = payload.staged_path.resolve()
        try:
            path.relative_to(staging_root)
        except ValueError as exc:
            raise AcquisitionValidationError(
                "Adapter payload escaped its staging directory."
            ) from exc
        if not path.is_file():
            raise AcquisitionValidationError(
                f"Staged payload does not exist: {path}"
            )

    representation_keys: set[str] = set()
    for representation in result.representations:
        if not representation.logical_key:
            raise AcquisitionValidationError(
                "Representation logical_key must not be empty."
            )
        if representation.logical_key in representation_keys:
            raise AcquisitionValidationError(
                "Duplicate representation logical key: "
                f"{representation.logical_key}"
            )
        representation_keys.add(representation.logical_key)

        if representation.parent_payload_key not in payload_keys:
            raise AcquisitionValidationError(
                "Representation references an unknown payload: "
                f"{representation.parent_payload_key}"
            )

        path = representation.staged_path.resolve()
        try:
            path.relative_to(staging_root)
        except ValueError as exc:
            raise AcquisitionValidationError(
                "Adapter representation escaped its staging directory."
            ) from exc
        if not path.is_file():
            raise AcquisitionValidationError(
                f"Staged representation does not exist: {path}"
            )

        previous_end_char = -1
        for segment in representation.segments:
            if not segment.text:
                raise AcquisitionValidationError(
                    "Adapter-provided segment text must not be empty."
                )
            if (segment.start_char is None) != (segment.end_char is None):
                raise AcquisitionValidationError(
                    "Segment character anchors must be paired."
                )
            if (
                segment.start_char is not None
                and segment.end_char is not None
            ):
                if (
                    segment.start_char < 0
                    or segment.end_char < segment.start_char
                ):
                    raise AcquisitionValidationError(
                        "Segment character anchors are invalid."
                    )
                if representation.text is None:
                    raise AcquisitionValidationError(
                        "Character-anchored segment requires representation text."
                    )
                if segment.end_char > len(representation.text):
                    raise AcquisitionValidationError(
                        "Segment character anchor exceeds representation text."
                    )
                if (
                    representation.text[
                        segment.start_char : segment.end_char
                    ]
                    != segment.text
                ):
                    raise AcquisitionValidationError(
                        "Segment text does not match its character anchor."
                    )
                if segment.start_char < previous_end_char:
                    raise AcquisitionValidationError(
                        "Character-anchored segments must not overlap."
                    )
                previous_end_char = segment.end_char

            if (
                segment.start_seconds is None
            ) != (segment.end_seconds is None):
                raise AcquisitionValidationError(
                    "Segment time anchors must be paired."
                )
            if (
                segment.start_seconds is not None
                and segment.end_seconds is not None
                and (
                    segment.start_seconds < 0
                    or segment.end_seconds < segment.start_seconds
                )
            ):
                raise AcquisitionValidationError(
                    "Segment time anchors are invalid."
                )
            if segment.page_number is not None and segment.page_number < 1:
                raise AcquisitionValidationError(
                    "Segment page_number must be positive."
                )
            if (segment.frame_start is None) != (segment.frame_end is None):
                raise AcquisitionValidationError(
                    "Segment frame anchors must be paired."
                )
            if (
                segment.frame_start is not None
                and segment.frame_end is not None
                and (
                    segment.frame_start < 0
                    or segment.frame_end < segment.frame_start
                )
            ):
                raise AcquisitionValidationError(
                    "Segment frame anchors are invalid."
                )

    for diagnostic in result.diagnostics:
        if diagnostic.severity not in {"info", "warning", "error"}:
            raise AcquisitionValidationError(
                f"Invalid diagnostic severity: {diagnostic.severity}"
            )
        if not diagnostic.code:
            raise AcquisitionValidationError(
                "Diagnostic code must not be empty."
            )
