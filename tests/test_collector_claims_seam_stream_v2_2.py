from __future__ import annotations

from ecobiome.knowledge_acquisition.claim_candidates import (
    SEAM_STREAM_POLICY_V2_2_SHA256,
    ClaimSegment,
    build_source_statement_candidates,
    build_source_statement_stream_candidates,
)


def _segment(
    identity: str,
    index: int,
    text: str,
    *,
    start: float | None = None,
    end: float | None = None,
    status: str = "pending",
    effective_text: str | None = None,
    corrected: bool = False,
) -> ClaimSegment:
    return ClaimSegment(
        id=identity,
        segment_index=index,
        text=text,
        effective_text=text if effective_text is None else effective_text,
        review_status=status,
        start_seconds=start,
        end_seconds=end,
        page_number=None,
        frame_start=None,
        frame_end=None,
        correction_applied=corrected,
    )


def test_seam_stream_policy_sha_is_frozen() -> None:
    assert SEAM_STREAM_POLICY_V2_2_SHA256 == (
        "8a5d530298ff4b3134def7b194609b1524167df04223c4969443695bb7cb6fde"
    )


def test_forward_extension_consumes_following_source() -> None:
    segments = (
        _segment(
            "a",
            1,
            "The result remains incomplete",
            start=0.0,
            end=13.0,
        ),
        _segment(
            "b",
            2,
            "until this boundary.",
            start=13.1,
            end=18.0,
        ),
        _segment(
            "c",
            3,
            "Next statement.",
            start=18.1,
            end=20.0,
        ),
    )

    result = build_source_statement_stream_candidates(
        segments,
        representation_id="rep",
        limit=2,
        maximum_claim_characters=350,
        maximum_window_seconds=15.0,
    )

    assert [item.text for item in result.candidates] == [
        "The result remains incomplete until this boundary.",
        "Next statement.",
    ]
    assert result.candidates[0].metadata["seam_stream_action"] == (
        "extended_to_safe_boundary"
    )
    assert result.candidates[1].metadata["seam_stream_action"] == "safe"
    assert result.unresolved_regions == ()


def test_trim_requeues_exact_suffix_without_duplication() -> None:
    long_text = "First sentence. " + ("x" * 40)
    segments = (
        _segment("a", 1, long_text),
        _segment("b", 2, "y" * 200),
    )

    result = build_source_statement_stream_candidates(
        segments,
        representation_id="rep",
        limit=2,
        maximum_claim_characters=40,
        maximum_window_seconds=15.0,
    )

    assert result.candidates[0].text == "First sentence."
    assert result.candidates[0].metadata["seam_stream_action"] == (
        "trimmed_to_safe_boundary_with_carry"
    )
    assert len(result.unresolved_regions) == 1
    assert result.unresolved_regions[0].text.startswith("x")

    provider_evidence = result.candidates[0].evidence[0]
    unresolved_evidence = result.unresolved_regions[0].evidence[0]
    assert provider_evidence.segment_char_end <= unresolved_evidence.segment_char_start
    assert (
        provider_evidence.evidence_text
        + long_text[
            provider_evidence.segment_char_end:unresolved_evidence.segment_char_start
        ]
        + unresolved_evidence.evidence_text
    ).startswith(long_text)


def test_unresolved_region_is_not_returned_as_provider_claim() -> None:
    segments = (
        _segment("a", 1, "unfinished source material"),
        _segment("bad", 2, "rejected", status="rejected"),
        _segment("b", 3, "Safe statement."),
    )

    result = build_source_statement_stream_candidates(
        segments,
        representation_id="rep",
    )

    assert [item.text for item in result.candidates] == ["Safe statement."]
    assert len(result.unresolved_regions) == 1
    assert result.unresolved_regions[0].text == "unfinished source material"
    assert build_source_statement_candidates(
        segments,
        representation_id="rep",
    ) == result.candidates


def test_partial_segment_evidence_is_exact_source_slice() -> None:
    raw = "First sentence. trailing words that exceed the bounded window"
    segments = (_segment("a", 1, raw),)

    result = build_source_statement_stream_candidates(
        segments,
        representation_id="rep",
        maximum_claim_characters=40,
    )

    assert result.candidates[0].text == "First sentence."
    evidence = result.candidates[0].evidence[0]
    assert evidence.evidence_text == raw[
        evidence.segment_char_start:evidence.segment_char_end
    ]
    assert evidence.segment_char_end == len("First sentence.")


def test_review_corrected_segment_keeps_full_raw_evidence() -> None:
    segments = (
        _segment(
            "a",
            1,
            "parler de nos médica.",
            effective_text="parler de nos Medaka.",
            corrected=True,
        ),
    )

    candidates = build_source_statement_candidates(
        segments,
        representation_id="rep",
    )

    assert candidates[0].text == "parler de nos Medaka."
    evidence = candidates[0].evidence[0]
    assert evidence.evidence_text == "parler de nos médica."
    assert evidence.segment_char_start == 0
    assert evidence.segment_char_end == len("parler de nos médica.")
