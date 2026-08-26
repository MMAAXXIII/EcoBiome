from __future__ import annotations

import hashlib

import pytest

from ecobiome.knowledge_persistence.snapshot_promotion_v1 import (
    SnapshotPromotionError,
    canonical_sha256,
    locate_anchor_paragraph_v1,
    normalized_jats_text_v1,
    validate_manifest_document,
)


def test_canonical_sha256_is_key_order_independent() -> None:
    left = {"b": 2, "a": {"y": 2, "x": 1}}
    right = {"a": {"x": 1, "y": 2}, "b": 2}
    assert canonical_sha256(left) == canonical_sha256(right)


def test_jats_normalization_and_anchor_selection_are_deterministic() -> None:
    raw = (
        b"<article><body>"
        b"<p>Short.</p>"
        b"<p>Nitrification is a two-step process in this synthetic fixture.</p>"
        b"<p>Another sufficiently long paragraph for deterministic ordering.</p>"
        b"</body></article>"
    )
    representation, paragraphs = normalized_jats_text_v1(raw)
    assert representation == "\n\n".join(paragraphs)
    index, paragraph = locate_anchor_paragraph_v1(
        paragraphs,
        ["Nitrification is a two-step process"],
    )
    assert index == 0
    assert hashlib.sha256(paragraph.encode()).hexdigest()


def test_manifest_rejects_knowledge_synthesis_delta() -> None:
    manifest = {
        "schema_version": "ecobiome-first-derived-snapshot-replay-manifest-v1",
        "rows": [
            {
                "table": "scientific_entities",
                "row_id": "synthetic",
                "canonical_row_payload_sha256": "0" * 64,
                "identity_where": {"id": "synthetic"},
                "row_payload_redacted": {"id": "synthetic"},
                "protected_fields": {},
            }
        ],
        "expected_table_delta": {
            "scientific_entities": 1,
            "knowledge_syntheses": 1,
            "source_lineage_edges": 0,
        },
    }
    with pytest.raises(SnapshotPromotionError):
        validate_manifest_document(manifest)


def test_manifest_rejects_unsafe_identifier() -> None:
    manifest = {
        "schema_version": "ecobiome-first-derived-snapshot-replay-manifest-v1",
        "rows": [
            {
                "table": "scientific_entities;drop",
                "row_id": "synthetic",
                "canonical_row_payload_sha256": "0" * 64,
                "identity_where": {"id": "synthetic"},
                "row_payload_redacted": {"id": "synthetic"},
                "protected_fields": {},
            }
        ],
        "expected_table_delta": {
            "knowledge_syntheses": 0,
            "source_lineage_edges": 0,
        },
    }
    with pytest.raises(SnapshotPromotionError):
        validate_manifest_document(manifest)
