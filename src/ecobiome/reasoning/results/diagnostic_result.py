"""Stable public facade for complete diagnostic-session results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from ecobiome.reasoning.diagnostic_pipeline import (
    DiagnosticInvestigationReport,
)
from ecobiome.reasoning.experiment.experiment import Experiment
from ecobiome.reasoning.results.summary import (
    DiagnosticStatus,
    DiagnosticSummary,
)
from ecobiome.reasoning.results.timeline import (
    DiagnosticTimelineEntry,
    build_diagnostic_timeline,
)

if TYPE_CHECKING:
    from ecobiome.reasoning.session.models import (
        DiagnosticSessionMetadata,
        DiagnosticSessionResult,
    )


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    """Public, interface-ready view of one diagnostic session."""

    _session_result: DiagnosticSessionResult

    @classmethod
    def from_session_result(
        cls,
        session_result: DiagnosticSessionResult,
    ) -> DiagnosticResult:
        """Build a public result from an internal session result."""
        return cls(session_result)

    @property
    def metadata(self) -> DiagnosticSessionMetadata:
        """Return immutable session metadata."""
        return self._session_result.metadata

    @property
    def investigation(self) -> DiagnosticInvestigationReport:
        """Return the underlying detailed investigation report."""
        return self._session_result.investigation

    @property
    def session_id(self) -> UUID:
        """Return the session identifier."""
        return self._session_result.session_id

    @property
    def profile_id(self) -> str:
        """Return the diagnostic profile identifier."""
        return self.metadata.profile_id

    @property
    def ecobiome_version(self) -> str:
        """Return the EcoBiome version used by the session."""
        return self.metadata.ecobiome_version

    @property
    def started_at(self) -> datetime:
        """Return the session start timestamp."""
        return self.metadata.started_at

    @property
    def finished_at(self) -> datetime:
        """Return the session finish timestamp."""
        return self._session_result.finished_at

    @property
    def duration_seconds(self) -> float:
        """Return the measured session duration."""
        return self._session_result.duration_seconds

    @property
    def succeeded(self) -> bool:
        """Return whether every diagnostic stage succeeded."""
        return self._session_result.succeeded

    @property
    def has_inconsistency(self) -> bool:
        """Return whether a contradiction was detected."""
        return self._session_result.has_inconsistency

    @property
    def observation_count(self) -> int:
        """Return the total number of evaluated observations."""
        return self._session_result.observation_count

    @property
    def usable_observation_count(self) -> int:
        """Return the number of usable observations."""
        return self._session_result.usable_observation_count

    @property
    def rejected_observation_count(self) -> int:
        """Return the number of rejected observations."""
        return self._session_result.rejected_observation_count

    @property
    def proposal_count(self) -> int:
        """Return the number of generated hypothesis proposals."""
        return self._session_result.proposal_count

    @property
    def experiment_count(self) -> int:
        """Return the number of planned experiments."""
        return self._session_result.experiment_count

    @property
    def best_experiment(self) -> Experiment | None:
        """Return the highest-ranked proposed experiment."""
        return self._session_result.best_experiment

    @property
    def quality_reports(self) -> tuple[object, ...]:
        """Return the observation-quality reports."""
        return tuple(self.investigation.quality_reports)

    @property
    def usable_observations(self) -> tuple[object, ...]:
        """Return observations accepted for reasoning."""
        return tuple(self.investigation.usable_observations)

    @property
    def rejected_observations(self) -> tuple[object, ...]:
        """Return observations rejected before reasoning."""
        return tuple(self.investigation.rejected_observations)

    @property
    def status(self) -> DiagnosticStatus:
        """Return the public high-level diagnostic status."""
        if not self.succeeded:
            return DiagnosticStatus.FAILED

        if self.has_inconsistency:
            return DiagnosticStatus.INVESTIGATION_REQUIRED

        return DiagnosticStatus.HEALTHY

    @property
    def warnings(self) -> tuple[str, ...]:
        """Return concise warnings suitable for interfaces."""
        warnings: list[str] = []

        if not self.succeeded:
            warnings.append(
                "The diagnostic investigation did not complete "
                "successfully."
            )

        if self.rejected_observation_count:
            warnings.append(
                f"{self.rejected_observation_count} observation(s) "
                "were rejected before reasoning."
            )

        if self.has_inconsistency:
            warnings.append(
                "A contradiction requiring investigation was detected."
            )

        return tuple(warnings)

    @property
    def summary(self) -> DiagnosticSummary:
        """Return an interface-ready diagnostic summary."""
        return DiagnosticSummary(
            status=self.status,
            observation_count=self.observation_count,
            usable_observation_count=(
                self.usable_observation_count
            ),
            rejected_observation_count=(
                self.rejected_observation_count
            ),
            proposal_count=self.proposal_count,
            experiment_count=self.experiment_count,
            duration_seconds=self.duration_seconds,
            warnings=self.warnings,
        )

    @property
    def timeline(self) -> tuple[DiagnosticTimelineEntry, ...]:
        """Return the logical diagnostic execution timeline."""
        return build_diagnostic_timeline(
            started_at=self.started_at,
            finished_at=self.finished_at,
            observation_count=self.observation_count,
            usable_observation_count=(
                self.usable_observation_count
            ),
            rejected_observation_count=(
                self.rejected_observation_count
            ),
            has_inconsistency=self.has_inconsistency,
            proposal_count=self.proposal_count,
            experiment_count=self.experiment_count,
        )
