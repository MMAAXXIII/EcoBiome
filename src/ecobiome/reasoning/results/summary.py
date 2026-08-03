"""Public summaries for completed diagnostic investigations."""

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticStatus(StrEnum):
    """High-level status exposed to EcoBiome interfaces."""

    HEALTHY = "healthy"
    INVESTIGATION_REQUIRED = "investigation_required"
    FAILED = "failed"


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticSummary:
    """Compact, interface-ready summary of one diagnostic result."""

    status: DiagnosticStatus
    observation_count: int
    usable_observation_count: int
    rejected_observation_count: int
    proposal_count: int
    experiment_count: int
    duration_seconds: float
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate summary counters and duration."""
        counters = (
            self.observation_count,
            self.usable_observation_count,
            self.rejected_observation_count,
            self.proposal_count,
            self.experiment_count,
        )

        if any(counter < 0 for counter in counters):
            raise ValueError(
                "Diagnostic summary counters cannot be negative."
            )

        if self.duration_seconds < 0.0:
            raise ValueError(
                "Diagnostic summary duration cannot be negative."
            )

        if (
            self.usable_observation_count
            + self.rejected_observation_count
            != self.observation_count
        ):
            raise ValueError(
                "Usable and rejected observations must equal "
                "the total observation count."
            )

        normalized_warnings = tuple(
            dict.fromkeys(
                warning.strip()
                for warning in self.warnings
                if warning.strip()
            )
        )

        object.__setattr__(
            self,
            "warnings",
            normalized_warnings,
        )

    @property
    def succeeded(self) -> bool:
        """Return whether execution completed successfully."""
        return self.status is not DiagnosticStatus.FAILED

    @property
    def needs_investigation(self) -> bool:
        """Return whether a contradiction requires investigation."""
        return (
            self.status
            is DiagnosticStatus.INVESTIGATION_REQUIRED
        )

    @property
    def rejection_rate(self) -> float:
        """Return the rejected-observation share."""
        if self.observation_count == 0:
            return 0.0

        return (
            self.rejected_observation_count
            / self.observation_count
        )
