"""Traceable metadata and results for diagnostic sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from uuid import UUID, uuid4

from ecobiome.reasoning.diagnostic_pipeline import (
    DiagnosticInvestigationReport,
)
from ecobiome.reasoning.experiment.experiment import Experiment


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def ecobiome_version() -> str:
    """Return the installed EcoBiome package version."""
    try:
        return version("ecobiome")
    except PackageNotFoundError:
        return "0.0.0+unknown"


@dataclass(frozen=True, slots=True, kw_only=True)
class DiagnosticSessionMetadata:
    """Describe one uniquely identifiable diagnostic session."""

    profile_id: str
    session_id: UUID = field(default_factory=uuid4)
    started_at: datetime = field(default_factory=utc_now)
    ecobiome_version: str = field(
        default_factory=ecobiome_version
    )
    tags: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate and normalize session metadata."""
        profile_id = self.profile_id.strip()
        package_version = self.ecobiome_version.strip()

        if not profile_id:
            raise ValueError(
                "A diagnostic session requires a profile identifier."
            )

        if "." not in profile_id:
            raise ValueError(
                "Profile identifier must contain a domain prefix."
            )

        if self.started_at.tzinfo is None:
            raise ValueError(
                "Session start timestamp must be timezone-aware."
            )

        if not package_version:
            raise ValueError(
                "EcoBiome version cannot be empty."
            )

        tags = tuple(
            dict.fromkeys(
                tag.strip()
                for tag in self.tags
                if tag.strip()
            )
        )

        normalized_attributes: dict[str, str] = {}

        for raw_key, raw_value in self.attributes:
            key = raw_key.strip()
            value = raw_value.strip()

            if not key:
                raise ValueError(
                    "Session attribute keys cannot be empty."
                )

            normalized_attributes[key] = value

        object.__setattr__(
            self,
            "profile_id",
            profile_id,
        )
        object.__setattr__(
            self,
            "ecobiome_version",
            package_version,
        )
        object.__setattr__(
            self,
            "tags",
            tags,
        )
        object.__setattr__(
            self,
            "attributes",
            tuple(normalized_attributes.items()),
        )

    @property
    def attribute_map(self) -> dict[str, str]:
        """Return session attributes as a new dictionary."""
        return dict(self.attributes)


@dataclass(frozen=True, slots=True)
class DiagnosticSessionResult:
    """Contain the complete output of one diagnostic session."""

    metadata: DiagnosticSessionMetadata
    finished_at: datetime
    duration_seconds: float
    investigation: DiagnosticInvestigationReport

    def __post_init__(self) -> None:
        """Validate session completion information."""
        if self.finished_at.tzinfo is None:
            raise ValueError(
                "Session finish timestamp must be timezone-aware."
            )

        if self.finished_at < self.metadata.started_at:
            raise ValueError(
                "Session finish timestamp cannot precede its start."
            )

        if self.duration_seconds < 0.0:
            raise ValueError(
                "Session duration cannot be negative."
            )

    @property
    def session_id(self) -> UUID:
        """Return the session identifier."""
        return self.metadata.session_id

    @property
    def succeeded(self) -> bool:
        """Return whether every investigation stage succeeded."""
        return self.investigation.succeeded

    @property
    def has_inconsistency(self) -> bool:
        """Return whether the session detected a contradiction."""
        return self.investigation.has_inconsistency

    @property
    def proposal_count(self) -> int:
        """Return the number of generated hypotheses."""
        return self.investigation.proposal_count

    @property
    def experiment_count(self) -> int:
        """Return the number of planned experiments."""
        return self.investigation.experiment_count

    @property
    def best_experiment(self) -> Experiment | None:
        """Return the highest-ranked proposed experiment."""
        return self.investigation.best_experiment

    @property
    def observation_count(self) -> int:
        """Return the number of evaluated observations."""
        return len(self.investigation.quality_reports)

    @property
    def usable_observation_count(self) -> int:
        """Return the number of observations used for reasoning."""
        return len(self.investigation.usable_observations)

    @property
    def rejected_observation_count(self) -> int:
        """Return the number of rejected observations."""
        return len(self.investigation.rejected_observations)
