"""Tests for the Knowledge object."""

import pytest

from ecobiome.knowledge.knowledge import Knowledge, KnowledgeStatus


def test_create_candidate_knowledge() -> None:
    knowledge = Knowledge(
        identifier="physics.water_volume.thermal_stability",
        title="Water volume improves thermal stability",
        statement="A larger water volume reduces temperature fluctuations.",
        domain="physics",
        confidence=0.65,
        source_ids=("source:paper-001",),
    )

    assert knowledge.status is KnowledgeStatus.CANDIDATE
    assert knowledge.confidence == pytest.approx(0.65)


def test_validated_knowledge_requires_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one source or claim",
    ):
        Knowledge(
            identifier="physics.invalid.knowledge",
            title="Unsupported knowledge",
            statement="This statement has no evidence.",
            domain="physics",
            status=KnowledgeStatus.VALIDATED,
            confidence=0.95,
        )


def test_knowledge_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        Knowledge(
            identifier="physics.invalid.confidence",
            title="Invalid confidence",
            statement="Confidence cannot exceed one.",
            domain="physics",
            confidence=1.25,
        )
