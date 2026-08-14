"""Regression tests for the PR #10 final-review findings."""

from argparse import Namespace
from pathlib import Path
from uuid import uuid4

import pytest

from ecobiome.cli.replay_events import replay_events_command
from ecobiome.cli.water_level import water_level_command
from ecobiome.core.events import (
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
)
from ecobiome.knowledge_acquisition import split_into_passages
from ecobiome.media import DuplicateMediaError, MediaMetadata
from ecobiome.reasoning import (
    Evidence,
    EvidenceRelation,
    Hypothesis,
    InferenceEngine,
)
from ecobiome.workspace import ProjectManifest, ProjectType, ProjectWorkspace
from ecobiome.world.persistence import load_world_state, save_world_state
from ecobiome.world.water_geometry import RectangularGeometry
from ecobiome.world.water_state import WaterBodyState
from ecobiome.world.world_state import WorldState


def test_water_level_event_log_replays_into_world_state(
    tmp_path: Path,
) -> None:
    world_path = tmp_path / "world.json"
    event_path = tmp_path / "events.jsonl"
    replayed_path = tmp_path / "replayed.json"

    world = WorldState()
    world.add_water_body(
        WaterBodyState(
            name="Review pond",
            geometry=RectangularGeometry(
                length_m=2.0,
                width_m=1.0,
                height_m=1.0,
            ),
            water_height_m=0.5,
        )
    )
    save_world_state(world, world_path)

    assert water_level_command(
        Namespace(
            name="Review pond",
            shape="rectangular",
            length=2.0,
            width=1.0,
            radius=None,
            container_height=1.0,
            current_height=0.5,
            remove=0.1,
            cause="user_removal",
            note="Controlled review removal",
            event_log=event_path,
        )
    ) == 0

    store = JsonLinesEventStore(
        path=event_path,
        registry=create_default_event_registry(),
    )
    stored_events = store.load()

    assert len(stored_events) == 1
    event = stored_events[0]
    assert isinstance(event, WaterRemovedEvent)
    assert event.note == "Controlled review removal"

    assert replay_events_command(
        Namespace(
            world=str(world_path),
            events=str(event_path),
            output=str(replayed_path),
        )
    ) == 0

    replayed = load_world_state(replayed_path)
    assert replayed.get_water_body("Review pond").water_height_m == pytest.approx(
        0.4
    )


def test_workspace_media_index_survives_reopen(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    source = tmp_path / "field-note.txt"
    source.write_text("stable pond observation", encoding="utf-8")

    manifest = ProjectManifest(
        name="Review workspace",
        project_type=ProjectType.POND,
    )
    workspace = ProjectWorkspace.create(
        workspace_root,
        manifest=manifest,
    )

    asset = workspace.media.import_file(
        source,
        metadata=MediaMetadata(
            title="Field note",
            tags=("field", "pond"),
            attributes=(("observer", "review"),),
        ),
        project_id=manifest.project_id,
        related_entity_ids=(uuid4(),),
    )

    assert workspace.layout.media_index_path.is_file()

    reopened = ProjectWorkspace.open(workspace_root)
    restored = reopened.media.get(asset.asset_id)

    assert reopened.media.count() == 1
    assert restored.asset_id == asset.asset_id
    assert restored.checksum_sha256 == asset.checksum_sha256
    assert restored.metadata.tags == ("field", "pond")
    assert restored.metadata.attribute_map == {"observer": "review"}
    assert restored.project_id == manifest.project_id
    assert restored.related_entity_ids == asset.related_entity_ids
    assert restored.stored_path.is_file()
    assert reopened.media.search(tags=("pond",)) == (restored,)

    with pytest.raises(DuplicateMediaError):
        reopened.media.import_file(
            source,
            metadata=MediaMetadata(title="Duplicate"),
            project_id=manifest.project_id,
        )


def test_split_oversized_passage_respects_character_limit() -> None:
    text = "x" * 5_000

    passages = split_into_passages(
        text,
        maximum_characters=1_500,
    )

    assert len(passages) == 4
    assert all(0 < len(passage) <= 1_500 for passage in passages)
    assert "".join(passages) == text


def test_split_oversized_passage_prefers_readable_boundaries() -> None:
    text = (
        "First sentence has useful evidence. "
        "Second sentence has more evidence. "
        "Third sentence closes the paragraph."
    )

    passages = split_into_passages(
        text,
        maximum_characters=50,
    )

    assert all(len(passage) <= 50 for passage in passages)
    assert passages[0].endswith(".")
    assert passages == split_into_passages(
        text,
        maximum_characters=50,
    )


def test_inference_tracks_only_supporting_observation_ids() -> None:
    hypothesis = Hypothesis(
        identifier="water.oxygen",
        title="Oxygen stability",
        statement="Aeration improves dissolved oxygen stability.",
        confidence=0.5,
    )

    supporting_id = uuid4()
    contradicting_id = uuid4()
    neutral_id = uuid4()

    evidence = (
        Evidence(
            observation_id=supporting_id,
            hypothesis_id=hypothesis.hypothesis_id,
            relation=EvidenceRelation.SUPPORTS,
            weight=0.2,
            explanation="Measured oxygen increased.",
            source_rule="review.support",
        ),
        Evidence(
            observation_id=contradicting_id,
            hypothesis_id=hypothesis.hypothesis_id,
            relation=EvidenceRelation.CONTRADICTS,
            weight=0.1,
            explanation="A separate measurement decreased.",
            source_rule="review.contradict",
        ),
        Evidence(
            observation_id=neutral_id,
            hypothesis_id=hypothesis.hypothesis_id,
            relation=EvidenceRelation.NEUTRAL,
            weight=0.8,
            explanation="Observation is not directional.",
            source_rule="review.neutral",
        ),
    )

    result = InferenceEngine().revise(hypothesis, evidence)

    assert result.revised_hypothesis.supporting_observation_ids == (
        supporting_id,
    )
    assert set(result.applied_evidence_ids) == {
        item.evidence_id
        for item in evidence
    }
    assert result.supporting_weight == pytest.approx(0.2)
    assert result.contradicting_weight == pytest.approx(0.1)
