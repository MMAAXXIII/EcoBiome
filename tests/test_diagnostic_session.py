"""Tests for complete traceable diagnostic sessions."""

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
from ecobiome.reasoning.session import (
    DiagnosticSession,
    DiagnosticSessionMetadata,
)

STARTED_AT = datetime(
    2026,
    8,
    2,
    16,
    0,
    tzinfo=UTC,
)

FINISHED_AT = STARTED_AT + timedelta(
    milliseconds=250
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
    """Create one scientific variable for session tests."""
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
    """Create one camera-frame luminance observation."""
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


def make_session(
    *,
    clock: SequenceClock,
) -> DiagnosticSession:
    """Build one operational camera/lux diagnostic session."""
    pipeline = DiagnosticPipelineFactory(
        build_camera_lux_registry()
    ).build()

    return DiagnosticSession(
        pipeline=pipeline,
        profile_id="diagnostic.camera_lux",
        clock=clock,
        package_version="18.0-test",
    )


def test_session_runs_complete_diagnostic_pipeline() -> None:
    session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    result = session.run(
        (
            make_camera_observation(),
            make_lux_observation(),
        ),
        session_id=SESSION_ID,
    )

    assert result.session_id == SESSION_ID
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


def test_session_records_timing_and_version() -> None:
    session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    result = session.run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    assert result.metadata.started_at == STARTED_AT
    assert result.finished_at == FINISHED_AT
    assert result.duration_seconds == pytest.approx(0.25)
    assert result.metadata.ecobiome_version == "18.0-test"
    assert result.metadata.profile_id == (
        "diagnostic.camera_lux"
    )


def test_session_normalizes_tags_and_attributes() -> None:
    session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    result = session.run(
        (
            make_camera_observation(),
            make_lux_observation(),
        ),
        tags=(
            " camera ",
            "diagnostic",
            "camera",
            "",
        ),
        attributes=(
            (" greenhouse ", " north "),
            ("operator", " EcoBiome "),
            ("operator", " autonomous "),
        ),
    )

    assert result.metadata.tags == (
        "camera",
        "diagnostic",
    )

    assert result.metadata.attributes == (
        ("greenhouse", "north"),
        ("operator", "autonomous"),
    )

    assert result.metadata.attribute_map == {
        "greenhouse": "north",
        "operator": "autonomous",
    }


def test_dark_environment_produces_conclusive_empty_session() -> None:
    session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    result = session.run(
        (
            make_camera_observation(),
            make_lux_observation(0.5),
        )
    )

    assert result.succeeded is True
    assert result.has_inconsistency is False
    assert result.proposal_count == 0
    assert result.experiment_count == 0
    assert result.best_experiment is None


def test_generated_session_identifiers_are_unique() -> None:
    first_session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    second_session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    first = first_session.run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    second = second_session.run(
        (
            make_camera_observation(),
            make_lux_observation(),
        )
    )

    assert first.session_id != second.session_id


def test_naive_session_timestamp_is_rejected() -> None:
    naive_timestamp = STARTED_AT.replace(
        tzinfo=None
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        DiagnosticSessionMetadata(
            profile_id="diagnostic.camera_lux",
            started_at=naive_timestamp,
        )


def test_invalid_profile_identifier_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="domain prefix",
    ):
        DiagnosticSessionMetadata(
            profile_id="camera_lux",
            started_at=STARTED_AT,
        )


def test_backward_clock_is_rejected() -> None:
    session = make_session(
        clock=SequenceClock(
            FINISHED_AT,
            STARTED_AT,
        )
    )

    with pytest.raises(
        ValueError,
        match="moved backwards",
    ):
        session.run(
            (
                make_camera_observation(),
                make_lux_observation(),
            )
        )


def test_empty_observation_session_is_supported() -> None:
    session = make_session(
        clock=SequenceClock(
            STARTED_AT,
            FINISHED_AT,
        )
    )

    result = session.run(())

    assert result.succeeded is True
    assert result.observation_count == 0
    assert result.usable_observation_count == 0
    assert result.rejected_observation_count == 0
    assert result.proposal_count == 0
    assert result.experiment_count == 0
