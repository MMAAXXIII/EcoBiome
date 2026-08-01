"""Execution of complete, traceable diagnostic sessions."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from uuid import UUID, uuid4

from ecobiome.core.observation.observation import Observation
from ecobiome.reasoning.diagnostic_pipeline import (
    DiagnosticInvestigationPipeline,
)
from ecobiome.reasoning.results.diagnostic_result import DiagnosticResult
from ecobiome.reasoning.session.models import (
    DiagnosticSessionMetadata,
    DiagnosticSessionResult,
    ecobiome_version,
    utc_now,
)


class DiagnosticSession:
    """Execute one complete diagnostic investigation session."""

    def __init__(
        self,
        *,
        pipeline: DiagnosticInvestigationPipeline,
        profile_id: str,
        clock: Callable[[], datetime] = utc_now,
        package_version: str | None = None,
    ) -> None:
        normalized_profile_id = profile_id.strip()

        if not normalized_profile_id:
            raise ValueError(
                "A diagnostic session requires a profile identifier."
            )

        if "." not in normalized_profile_id:
            raise ValueError(
                "Profile identifier must contain a domain prefix."
            )

        self._pipeline = pipeline
        self._profile_id = normalized_profile_id
        self._clock = clock
        self._package_version = (
            package_version.strip()
            if package_version is not None
            else ecobiome_version()
        )

        if not self._package_version:
            raise ValueError(
                "EcoBiome version cannot be empty."
            )

    def run(
        self,
        observations: Iterable[Observation],
        *,
        session_id: UUID | None = None,
        tags: tuple[str, ...] = (),
        attributes: tuple[tuple[str, str], ...] = (),
    ) -> DiagnosticResult:
        """Run the complete pipeline and preserve session metadata."""
        started_at = self._clock()

        if started_at.tzinfo is None:
            raise ValueError(
                "Session clock must return timezone-aware timestamps."
            )

        metadata = DiagnosticSessionMetadata(
            session_id=(
                session_id
                if session_id is not None
                else uuid4()
            ),
            profile_id=self._profile_id,
            started_at=started_at,
            ecobiome_version=self._package_version,
            tags=tags,
            attributes=attributes,
        )

        investigation = self._pipeline.run(observations)

        finished_at = self._clock()

        if finished_at.tzinfo is None:
            raise ValueError(
                "Session clock must return timezone-aware timestamps."
            )

        if finished_at < started_at:
            raise ValueError(
                "Session clock moved backwards during execution."
            )

        duration_seconds = (
            finished_at - started_at
        ).total_seconds()

        session_result = DiagnosticSessionResult(
            metadata=metadata,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
            investigation=investigation,
        )

        return DiagnosticResult.from_session_result(
            session_result
        )
