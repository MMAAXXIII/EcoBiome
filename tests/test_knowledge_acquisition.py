"""Tests for knowledge acquisition."""

from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition import (
    ClaimKind,
    ExtractedClaim,
    KnowledgeSource,
    SourceType,
    load_transcript,
    split_into_passages,
)


def test_create_youtube_source() -> None:
    source = KnowledgeSource(
        title="Aquatic ecosystem feedback",
        source_type=SourceType.YOUTUBE,
        locator="https://www.youtube.com/watch?v=example",
        author="Example creator",
    )

    assert source.source_type is SourceType.YOUTUBE
    assert source.title == "Aquatic ecosystem feedback"


def test_load_transcript(tmp_path: Path) -> None:
    transcript_path = tmp_path / "transcript.txt"
    transcript_path.write_text(
        "A large water volume improves thermal stability.",
        encoding="utf-8",
    )

    imported = load_transcript(
        transcript_path,
        title="Thermal stability",
        locator="local:test-transcript",
    )

    assert "thermal stability" in imported.text
    assert imported.source.title == "Thermal stability"


def test_split_transcript_into_passages() -> None:
    text = "First scientific passage.\n\nSecond scientific passage."

    passages = split_into_passages(text, maximum_characters=40)

    assert passages == (
        "First scientific passage.",
        "Second scientific passage.",
    )


def test_create_unverified_claim() -> None:
    source = KnowledgeSource(
        title="Field feedback",
        source_type=SourceType.USER_FEEDBACK,
        locator="feedback:001",
    )

    claim = ExtractedClaim(
        source_id=source.id,
        text="The pond remained stable without mechanical filtration.",
        kind=ClaimKind.OBSERVATION,
        confidence=0.60,
    )

    assert claim.confidence == pytest.approx(0.60)
    assert claim.kind is ClaimKind.OBSERVATION


def test_claim_rejects_invalid_confidence() -> None:
    source = KnowledgeSource(
        title="Invalid example",
        source_type=SourceType.OTHER,
        locator="example:invalid",
    )

    with pytest.raises(ValueError, match="between 0 and 1"):
        ExtractedClaim(
            source_id=source.id,
            text="Invalid confidence.",
            confidence=1.5,
        )
