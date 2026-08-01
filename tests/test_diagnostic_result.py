"""Tests for the public DiagnosticResult API."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning.pipeline_factory import (
    DiagnosticPipelineFactory,
)
from ecobiome.reasoning.profiles import (
    build_camera_lux_registry,
)
from ecobiome.reasoning.results import (
    DiagnosticResult,
    DiagnosticStatus,
    DiagnosticTimelineStage,
    diagnostic_result_to_dict,
)
from ecobiome.reasoning.session import DiagnosticSession

STARTED_AT = datetime(
    2026,
    8,
    2,
    18,
    0,
    tzinfo=UTC,
)

FINISHED_AT = STARTED_AT + timedelta(
    milliseconds=350
)

SESSION_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


class SequenceClock:
    """Return deterministic timestamps in sequence."""

    def __init__(
        self,
        *timestamps: datetime,
    ) -> None:
        self._timestamps = timestamps
        self._index = 0

    def __call__(self) -> datetime:
        """Return the next configured timestamp."""
        if self._index >= len(self._timestamps):
            raise RuntimeError(
                "No timestamp remains in the sequence clock."
            )

        timestamp = self._timestamps[self._index]
        self._index += 1
        return timestamp


def make_variable(
    identifier: str,
    *,
    name: str,
    unit: str,
    category: str,
) -> ScientificVariable:
    """Create one scientific variable."""
    return ScientificVariable(
        identifier=identifier,
        name=name,
        description=name,
        unit=unit,
        display_unit=unit,
        category=category,
    )


def make_camera_observation(
    luminance: float = 0.01,
) -> Observation:
    """Create one camera observation."""
    return Observation(
        source="camera-01",
        variable=make_variable(
            "vision.frame_mean_luminance",
            name="Frame luminance",
            unit="dimensionless",
            category="vision",
        ),
        value=luminance,
        acquisition_method=AcquisitionMethod.CAMERA,
        confidence=0.99,
        observed_at=STARTED_AT,
    )


def make_lux_observation(
    lux: float = 40_000.0,
) -> Observation:
    """Create one ambient-light observation."""
    return Observation(
        source="lux-sensor-01",
        variable=make_variable(
            "weather.ambient_light",
            name="Ambient light",
            unit="lux",
            category="weather",
        ),
        value=lux,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
        observed_at=STARTED_AT,
    )


def make_session() -> DiagnosticSession:
    """Build one deterministic diagnostic session."""
    pipeline = DiagnosticPipelineFactory(
        build_camera_lux_registry()
    ).build()

    return DiagnosticSession(
        pipeline=pipeline,
        profile_id="diagnostic.camera_lux",
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        ),
        package_version="19.0-test",
    )


def run_inconsistent_session() -> DiagnosticResult:
    """Run a deterministic inconsistent camera/lux session."""
    return make_session().run(
        (
            make_camera_observation(),
            make_lux_observation(),
        ),
        session_id=SESSION_ID,
    )


def test_session_returns_public_diagnostic_result() -> None:
    result = run_inconsistent_session()

    assert isinstance(result, DiagnosticResult)
    assert result.session_id == SESSION_ID
    assert result.profile_id == "diagnostic.camera_lux"
    assert result.ecobiome_version == "19.0-test"
    assert result.started_at == STARTED_AT
    assert result.finished_at == FINISHED_AT
    assert result.duration_seconds == pytest.approx(0.35)


def test_public_result_preserves_existing_session_api() -> None:
    result = run_inconsistent_session()

    assert result.succeeded is True
    assert result.has_inconsistency is True
    assert result.observation_count == 2
    assert result.usable_observation_count == 2
    assert result.rejected_observation_count == 0
    assert result.proposal_count == 4
    assert result.experiment_count == 3

    assert result.best_experiment is not None
    assert result.best_experiment.identifier == (
        "camera.clean_lens_and_recapture"
    )


def test_public_result_exposes_observation_collections() -> None:
    result = run_inconsistent_session()

    assert len(result.quality_reports) == 2
    assert len(result.usable_observations) == 2
    assert result.rejected_observations == ()


def test_inconsistent_result_has_investigation_status() -> None:
    result = run_inconsistent_session()

    assert result.status is (
        DiagnosticStatus.INVESTIGATION_REQUIRED
    )

    assert result.summary.status is (
        DiagnosticStatus.INVESTIGATION_REQUIRED
    )

    assert result.summary.needs_investigation is True
    assert result.summary.succeeded is True
    assert result.summary.rejection_rate == pytest.approx(0.0)

    assert result.warnings == (
        "A contradiction requiring investigation was detected.",
    )


def test_dark_environment_returns_healthy_status() -> None:
    result = make_session().run(
        (
            make_camera_observation(),
            make_lux_observation(0.5),
        )
    )

    assert result.status is DiagnosticStatus.HEALTHY
    assert result.has_inconsistency is False
    assert result.proposal_count == 0
    assert result.experiment_count == 0
    assert result.warnings == ()


def test_summary_contains_interface_ready_counters() -> None:
    result = run_inconsistent_session()
    summary = result.summary

    assert summary.observation_count == 2
    assert summary.usable_observation_count == 2
    assert summary.rejected_observation_count == 0
    assert summary.proposal_count == 4
    assert summary.experiment_count == 3
    assert summary.duration_seconds == pytest.approx(0.35)


def test_timeline_has_stable_ordered_stages() -> None:
    result = run_inconsistent_session()

    assert tuple(
        entry.sequence
        for entry in result.timeline
    ) == (0, 1, 2, 3, 4, 5)

    assert tuple(
        entry.stage
        for entry in result.timeline
    ) == (
        DiagnosticTimelineStage.SESSION_STARTED,
        DiagnosticTimelineStage.OBSERVATIONS_EVALUATED,
        DiagnosticTimelineStage.CONSISTENCY_EVALUATED,
        DiagnosticTimelineStage.HYPOTHESES_GENERATED,
        DiagnosticTimelineStage.EXPERIMENTS_PLANNED,
        DiagnosticTimelineStage.SESSION_FINISHED,
    )

    assert result.timeline[0].occurred_at == STARTED_AT
    assert result.timeline[-1].occurred_at == FINISHED_AT


def test_result_serialization_contains_public_data() -> None:
    payload = diagnostic_result_to_dict(
        run_inconsistent_session()
    )

    assert payload["session_id"] == str(SESSION_ID)
    assert payload["profile_id"] == "diagnostic.camera_lux"
    assert payload["ecobiome_version"] == "19.0-test"
    assert payload["status"] == "investigation_required"
    assert payload["succeeded"] is True
    assert payload["has_inconsistency"] is True

    assert payload["counts"] == {
        "observations": 2,
        "usable_observations": 2,
        "rejected_observations": 0,
        "proposals": 4,
        "experiments": 3,
    }

    assert payload["best_experiment"] == {
        "identifier": "camera.clean_lens_and_recapture",
    }

    timeline = payload["timeline"]

    assert isinstance(timeline, list)
    assert len(timeline) == 6


def test_empty_session_is_supported_by_public_result() -> None:
    result = make_session().run(())

    assert result.status is DiagnosticStatus.HEALTHY
    assert result.observation_count == 0
    assert result.summary.rejection_rate == pytest.approx(0.0)
    assert result.quality_reports == ()
    assert result.timeline[1].item_count == 0
