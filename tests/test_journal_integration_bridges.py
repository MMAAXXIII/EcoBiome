"""Tests for automatic scientific-journal bridges."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.integrations.journal import (
    JournalIntegrationService,
)
from ecobiome.journal import (
    InMemoryJournalEventStore,
    JournalEventType,
    ScientificJournal,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.media import (
    LocalMediaStorage,
    MediaLibrary,
    MediaMetadata,
)
from ecobiome.reasoning.learning import (
    InMemoryLearningEventStore,
    LearningEngine,
    LearningOutcome,
)
from ecobiome.reasoning.pipeline_factory import (
    DiagnosticPipelineFactory,
)
from ecobiome.reasoning.profiles import (
    build_camera_lux_registry,
)
from ecobiome.reasoning.session import DiagnosticSession

OCCURRED_AT = datetime(
    2026,
    8,
    2,
    18,
    42,
    tzinfo=UTC,
)

FINISHED_AT = OCCURRED_AT + timedelta(
    milliseconds=250
)

PROJECT_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)

HYPOTHESIS_ID = UUID(
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
)

EVIDENCE_ID = UUID(
    "cccccccc-cccc-cccc-cccc-cccccccccccc"
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
        timestamp = self._timestamps[self._index]
        self._index += 1
        return timestamp


def make_integrations() -> tuple[
    ScientificJournal,
    JournalIntegrationService,
]:
    """Create one empty journal and its integration service."""
    journal = ScientificJournal(
        InMemoryJournalEventStore()
    )

    return (
        journal,
        JournalIntegrationService(journal),
    )


def make_variable(
    identifier: str,
    *,
    unit: str,
    category: str,
) -> ScientificVariable:
    """Create one deterministic scientific variable."""
    return ScientificVariable(
        identifier=identifier,
        name=identifier,
        description=identifier,
        unit=unit,
        display_unit=unit,
        category=category,
    )


def make_diagnostic_result():
    """Run one deterministic camera/lux diagnostic."""
    pipeline = DiagnosticPipelineFactory(
        build_camera_lux_registry()
    ).build()

    session = DiagnosticSession(
        pipeline=pipeline,
        profile_id="diagnostic.camera_lux",
        clock=SequenceClock(
            OCCURRED_AT,
            FINISHED_AT,
        ),
        package_version="22.0-test",
    )

    camera = Observation(
        source="camera-01",
        variable=make_variable(
            "vision.frame_mean_luminance",
            unit="dimensionless",
            category="vision",
        ),
        value=0.01,
        acquisition_method=AcquisitionMethod.CAMERA,
        confidence=0.99,
        observed_at=OCCURRED_AT,
    )

    lux = Observation(
        source="lux-sensor-01",
        variable=make_variable(
            "weather.ambient_light",
            unit="lux",
            category="weather",
        ),
        value=40_000.0,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.99,
        observed_at=OCCURRED_AT,
    )

    return session.run((camera, lux))


def test_media_bridge_records_imported_asset(
    tmp_path: Path,
) -> None:
    source = tmp_path / "premiers-guppys.jpg"
    source.write_bytes(b"guppy-image")

    library = MediaLibrary(
        LocalMediaStorage(tmp_path / "media")
    )

    asset = library.import_file(
        source,
        metadata=MediaMetadata(
            title="Naissance de mes premiers guppys",
            description="Premiers alevins observés.",
            captured_at=OCCURRED_AT,
            tags=("guppy", "alevins"),
        ),
        project_id=PROJECT_ID,
    )

    journal, integrations = make_integrations()

    event = integrations.media.record_import(asset)

    assert event.event_type is JournalEventType.MEDIA
    assert event.title == asset.metadata.title
    assert event.occurred_at == OCCURRED_AT
    assert event.project_id == PROJECT_ID
    assert event.tags == ("guppy", "alevins")
    assert event.references[0].entity_id == asset.asset_id
    assert journal.timeline() == (event,)


def test_media_bridge_is_idempotent(
    tmp_path: Path,
) -> None:
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"one-image")

    asset = MediaLibrary(
        LocalMediaStorage(tmp_path / "media")
    ).import_file(
        source,
        metadata=MediaMetadata(
            title="Photo",
            captured_at=OCCURRED_AT,
        ),
    )

    journal, integrations = make_integrations()

    first = integrations.media.record_import(asset)
    second = integrations.media.record_import(asset)

    assert second == first
    assert journal.timeline() == (first,)


def test_media_bridge_falls_back_to_import_timestamp(
    tmp_path: Path,
) -> None:
    source = tmp_path / "undated.jpg"
    source.write_bytes(b"undated-image")

    asset = MediaLibrary(
        LocalMediaStorage(tmp_path / "media")
    ).import_file(
        source,
        metadata=MediaMetadata(
            title="Undated photograph",
        ),
    )

    _, integrations = make_integrations()

    event = integrations.media.record_import(asset)

    assert event.occurred_at == asset.imported_at


def test_diagnostic_bridge_records_public_result() -> None:
    result = make_diagnostic_result()
    journal, integrations = make_integrations()

    event = integrations.diagnostics.record_result(
        result,
        project_id=PROJECT_ID,
    )

    assert event.event_type is JournalEventType.DIAGNOSTIC
    assert event.occurred_at == result.finished_at
    assert event.project_id == PROJECT_ID
    assert event.attribute_map["status"] == (
        "investigation_required"
    )
    assert event.payload_map["observation_count"] == 2
    assert event.payload_map["proposal_count"] == 4
    assert event.payload_map["experiment_count"] == 3
    assert event.references[0].entity_id == result.session_id
    assert journal.timeline() == (event,)


def test_diagnostic_bridge_preserves_best_experiment() -> None:
    result = make_diagnostic_result()
    _, integrations = make_integrations()

    event = integrations.diagnostics.record_result(result)

    assert event.payload_map["best_experiment_id"] == (
        "camera.clean_lens_and_recapture"
    )


def test_diagnostic_bridge_is_idempotent() -> None:
    result = make_diagnostic_result()
    journal, integrations = make_integrations()

    first = integrations.diagnostics.record_result(result)
    second = integrations.diagnostics.record_result(result)

    assert second == first
    assert journal.timeline() == (first,)


def test_learning_bridge_records_confidence_revision() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    learning_event = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        strength=0.50,
        occurred_at=OCCURRED_AT,
        evidence_ids=(EVIDENCE_ID,),
        notes="Lens cleaning restored the image.",
    )

    journal, integrations = make_integrations()

    event = integrations.learning.record_learning(
        learning_event,
        project_id=PROJECT_ID,
    )

    assert event.event_type is JournalEventType.LEARNING
    assert event.project_id == PROJECT_ID
    assert event.attribute_map["outcome"] == "confirmed"
    assert event.payload_map["confidence_before"] == (
        pytest.approx(0.40)
    )
    assert event.payload_map["confidence_after"] == (
        pytest.approx(0.70)
    )
    assert event.references[0].entity_id == (
        learning_event.event_id
    )
    assert event.references[1].entity_id == HYPOTHESIS_ID
    assert journal.timeline() == (event,)


def test_learning_bridge_preserves_evidence_ids() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    learning_event = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.CONFIRMED,
        confidence_before=0.40,
        strength=0.50,
        occurred_at=OCCURRED_AT,
        evidence_ids=(EVIDENCE_ID,),
    )

    _, integrations = make_integrations()

    event = integrations.learning.record_learning(
        learning_event
    )

    assert event.payload_map["evidence_ids"] == (
        str(EVIDENCE_ID),
    )


def test_learning_bridge_is_idempotent() -> None:
    engine = LearningEngine(
        InMemoryLearningEventStore()
    )

    learning_event = engine.record(
        hypothesis_id=HYPOTHESIS_ID,
        experiment_id="camera.clean_lens",
        outcome=LearningOutcome.REFUTED,
        confidence_before=0.80,
        strength=0.50,
        occurred_at=OCCURRED_AT,
    )

    journal, integrations = make_integrations()

    first = integrations.learning.record_learning(
        learning_event
    )

    second = integrations.learning.record_learning(
        learning_event
    )

    assert second == first
    assert journal.timeline() == (first,)


def test_all_bridges_share_one_chronological_journal(
    tmp_path: Path,
) -> None:
    journal, integrations = make_integrations()

    source = tmp_path / "guppy.jpg"
    source.write_bytes(b"timeline-image")

    asset = MediaLibrary(
        LocalMediaStorage(tmp_path / "media")
    ).import_file(
        source,
        metadata=MediaMetadata(
            title="Guppy photograph",
            captured_at=OCCURRED_AT,
        ),
        project_id=PROJECT_ID,
    )

    media_event = integrations.media.record_import(asset)

    diagnostic_result = make_diagnostic_result()

    diagnostic_event = (
        integrations.diagnostics.record_result(
            diagnostic_result,
            project_id=PROJECT_ID,
        )
    )

    assert journal.timeline() == (
        media_event,
        diagnostic_event,
    )


def test_service_exposes_three_bridges() -> None:
    _, integrations = make_integrations()

    assert integrations.media is not None
    assert integrations.diagnostics is not None
    assert integrations.learning is not None


def test_integration_packages_import_independently() -> None:
    from ecobiome.integrations.journal import (
        DiagnosticJournalBridge,
        LearningJournalBridge,
        MediaJournalBridge,
    )

    assert DiagnosticJournalBridge is not None
    assert LearningJournalBridge is not None
    assert MediaJournalBridge is not None
