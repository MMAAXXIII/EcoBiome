"""Deterministic source-statement candidates with seam-safe stream continuity."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

EXTRACTOR_NAME = "source-statement-window-v1"
SEAM_STREAM_POLICY_VERSION = "2.2"
SEAM_STREAM_POLICY_V2_2_SHA256 = (
    "8a5d530298ff4b3134def7b194609b1524167df04223c4969443695bb7cb6fde"
)

_TERMINAL_BOUNDARY_RE = re.compile(
    r"""[.!?…](?=(?:["'»”’)\]]|\s|$))""",
    flags=re.UNICODE,
)
_TERMINAL_END_RE = re.compile(
    r"""[.!?…](?:["'»”’)\]]*)$""",
    flags=re.UNICODE,
)

_FORWARD_MAX_SEGMENTS = 3
_FORWARD_MAX_SECONDS = 6.0
_FORWARD_MAX_CHARACTERS = 120
_RECOVERY_MAX_SEGMENTS = 30
_RECOVERY_MAX_SECONDS = 60.0
_RECOVERY_MAX_CHARACTERS = 2000


@dataclass(frozen=True, slots=True)
class ClaimSegment:
    id: str
    segment_index: int
    text: str
    effective_text: str
    review_status: str
    start_seconds: float | None
    end_seconds: float | None
    page_number: int | None
    frame_start: int | None
    frame_end: int | None
    correction_applied: bool = False


@dataclass(frozen=True, slots=True)
class EvidenceCandidate:
    segment_id: str
    evidence_text: str
    segment_char_start: int
    segment_char_end: int
    start_seconds: float | None
    end_seconds: float | None
    page_number: int | None
    frame_start: int | None
    frame_end: int | None


@dataclass(frozen=True, slots=True)
class ClaimCandidate:
    claim_kind: str
    text: str
    evidence: tuple[EvidenceCandidate, ...]
    metadata: dict[str, object]


@dataclass(frozen=True, slots=True)
class UnresolvedSourceRegion:
    reason: str
    text: str
    evidence: tuple[EvidenceCandidate, ...]


@dataclass(frozen=True, slots=True)
class ClaimStreamResult:
    candidates: tuple[ClaimCandidate, ...]
    unresolved_regions: tuple[UnresolvedSourceRegion, ...]
    diagnostics: dict[str, object]
    final_cursor: tuple[int, int] | None


@dataclass(frozen=True, slots=True)
class _SegmentView:
    segment: ClaimSegment
    claim_text: str
    evidence_left: int
    evidence_right: int
    partial_allowed: bool


@dataclass(frozen=True, slots=True)
class _Slice:
    view_position: int
    char_start: int
    char_end: int


def _fingerprint(
    *,
    claim_kind: str,
    text: str,
    evidence: tuple[EvidenceCandidate, ...],
) -> str:
    payload = {
        "claim_kind": claim_kind,
        "text": text,
        "evidence": [
            {
                "segment_id": item.segment_id,
                "char_start": item.segment_char_start,
                "char_end": item.segment_char_end,
                "start_seconds": item.start_seconds,
                "end_seconds": item.end_seconds,
                "page_number": item.page_number,
                "frame_start": item.frame_start,
                "frame_end": item.frame_end,
            }
            for item in evidence
        ],
    }
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_end(text: str) -> bool:
    return bool(_TERMINAL_END_RE.search(text.rstrip()))


def _first_boundary(text: str) -> int | None:
    match = _TERMINAL_BOUNDARY_RE.search(text)
    return match.end() if match is not None else None


def _last_boundary(text: str) -> int | None:
    matches = list(_TERMINAL_BOUNDARY_RE.finditer(text))
    return matches[-1].end() if matches else None


def _segment_view(segment: ClaimSegment) -> _SegmentView | None:
    effective = segment.effective_text
    stripped = effective.strip()
    if not stripped:
        return None

    if segment.correction_applied:
        return _SegmentView(
            segment=segment,
            claim_text=stripped,
            evidence_left=0,
            evidence_right=len(segment.text),
            partial_allowed=False,
        )

    left = len(effective) - len(effective.lstrip())
    right = len(effective.rstrip())
    return _SegmentView(
        segment=segment,
        claim_text=effective[left:right],
        evidence_left=left,
        evidence_right=right,
        partial_allowed=True,
    )


def _make_slice(
    views: tuple[_SegmentView, ...],
    position: int,
    char_start: int,
    char_end: int,
) -> _Slice:
    view = views[position]
    if char_start < 0 or char_end < char_start or char_end > len(view.claim_text):
        raise ValueError("invalid source-statement character slice")
    if not view.partial_allowed and (
        char_start != 0 or char_end != len(view.claim_text)
    ):
        raise ValueError(
            "review-corrected segments cannot be split without a "
            "character-level correction mapping"
        )
    return _Slice(
        view_position=position,
        char_start=char_start,
        char_end=char_end,
    )


def _slice_claim_text(
    views: tuple[_SegmentView, ...],
    item: _Slice,
) -> str:
    view = views[item.view_position]
    return view.claim_text[item.char_start:item.char_end]


def _slice_evidence(
    views: tuple[_SegmentView, ...],
    item: _Slice,
) -> EvidenceCandidate:
    view = views[item.view_position]
    segment = view.segment

    if view.partial_allowed:
        evidence_start = view.evidence_left + item.char_start
        evidence_end = view.evidence_left + item.char_end
    else:
        evidence_start = 0
        evidence_end = len(segment.text)

    evidence_text = segment.text[evidence_start:evidence_end]
    return EvidenceCandidate(
        segment_id=segment.id,
        evidence_text=evidence_text,
        segment_char_start=evidence_start,
        segment_char_end=evidence_end,
        start_seconds=segment.start_seconds,
        end_seconds=segment.end_seconds,
        page_number=segment.page_number,
        frame_start=segment.frame_start,
        frame_end=segment.frame_end,
    )


def _render_claim_text(
    views: tuple[_SegmentView, ...],
    slices: list[_Slice],
) -> str:
    return " ".join(
        _slice_claim_text(views, item)
        for item in slices
        if _slice_claim_text(views, item)
    ).strip()


def _evidence_tuple(
    views: tuple[_SegmentView, ...],
    slices: list[_Slice],
) -> tuple[EvidenceCandidate, ...]:
    return tuple(
        _slice_evidence(views, item)
        for item in slices
        if item.char_end > item.char_start
    )



def _normalize_cursor(
    views: tuple[_SegmentView, ...],
    position: int,
    char_start: int,
) -> tuple[int, int]:
    while position < len(views):
        text = views[position].claim_text
        while char_start < len(text) and text[char_start].isspace():
            char_start += 1
        if char_start < len(text):
            return position, char_start
        position += 1
        char_start = 0
    return position, 0


def _metadata_for_candidate(
    *,
    representation_id: str,
    views: tuple[_SegmentView, ...],
    slices: list[_Slice],
    evidence: tuple[EvidenceCandidate, ...],
    text: str,
    action: str,
    source_start: tuple[int, int],
    source_end: tuple[int, int],
) -> dict[str, object]:
    segments = [
        views[item.view_position].segment
        for item in slices
    ]
    unique_segments: list[ClaimSegment] = []
    seen_ids: set[str] = set()
    for segment in segments:
        if segment.id in seen_ids:
            continue
        seen_ids.add(segment.id)
        unique_segments.append(segment)

    return {
        "epistemic_status": "candidate_source_statement",
        "extractor": EXTRACTOR_NAME,
        "seam_stream_policy": SEAM_STREAM_POLICY_VERSION,
        "seam_stream_policy_sha256": SEAM_STREAM_POLICY_V2_2_SHA256,
        "seam_stream_action": action,
        "provider_eligible": True,
        "representation_id": representation_id,
        "segment_ids": [item.id for item in unique_segments],
        "segment_review_statuses": [
            item.review_status for item in unique_segments
        ],
        "uses_review_correction": any(
            item.correction_applied for item in unique_segments
        ),
        "partial_segment_evidence": any(
            evidence_item.segment_char_start != 0
            or evidence_item.segment_char_end
            != len(
                next(
                    segment.text
                    for segment in unique_segments
                    if segment.id == evidence_item.segment_id
                )
            )
            for evidence_item in evidence
        ),
        "source_cursor_start": {
            "segment_index": views[source_start[0]].segment.segment_index,
            "char_start": source_start[1],
        },
        "source_cursor_end": (
            {
                "segment_index": views[source_end[0]].segment.segment_index,
                "char_start": source_end[1],
            }
            if source_end[0] < len(views)
            else {
                "segment_index": None,
                "char_start": 0,
            }
        ),
        "candidate_fingerprint": _fingerprint(
            claim_kind="source_statement",
            text=text,
            evidence=evidence,
        ),
    }


def _append_candidate(
    *,
    candidates: list[ClaimCandidate],
    representation_id: str,
    views: tuple[_SegmentView, ...],
    slices: list[_Slice],
    action: str,
    source_start: tuple[int, int],
    source_end: tuple[int, int],
) -> None:
    text = _render_claim_text(views, slices)
    if not text:
        return
    evidence = _evidence_tuple(views, slices)
    metadata = _metadata_for_candidate(
        representation_id=representation_id,
        views=views,
        slices=slices,
        evidence=evidence,
        text=text,
        action=action,
        source_start=source_start,
        source_end=source_end,
    )
    candidates.append(
        ClaimCandidate(
            claim_kind="source_statement",
            text=text,
            evidence=evidence,
            metadata=metadata,
        )
    )


def _recovery_region(
    *,
    views: tuple[_SegmentView, ...],
    start_position: int,
    start_char: int,
) -> tuple[list[_Slice], tuple[int, int] | None]:
    position = start_position
    char_start = start_char
    first = views[position].segment
    start_seconds = first.start_seconds
    slices: list[_Slice] = []
    total_characters = 0
    segment_count = 0

    while position < len(views) and segment_count < _RECOVERY_MAX_SEGMENTS:
        view = views[position]
        if (
            start_seconds is not None
            and view.segment.end_seconds is not None
            and view.segment.end_seconds - start_seconds
            > _RECOVERY_MAX_SECONDS
        ):
            break

        text = view.claim_text[char_start:]
        remaining = _RECOVERY_MAX_CHARACTERS - total_characters
        if remaining <= 0:
            break

        searchable = text[:remaining]
        boundary = _first_boundary(searchable)

        if boundary is not None:
            char_end = char_start + boundary
            if not view.partial_allowed and char_end != len(view.claim_text):
                # A corrected segment has no char-level mapping. Continue only
                # if its full effective text is still within the recovery budget.
                if len(text) > remaining:
                    break
                slices.append(
                    _make_slice(
                        views,
                        position,
                        char_start,
                        len(view.claim_text),
                    )
                )
                total_characters += len(text)
                position += 1
                char_start = 0
                segment_count += 1
                continue

            slices.append(
                _make_slice(
                    views,
                    position,
                    char_start,
                    char_end,
                )
            )
            return slices, _normalize_cursor(
                views,
                position,
                char_end,
            )

        if len(text) > remaining:
            break

        slices.append(
            _make_slice(
                views,
                position,
                char_start,
                len(view.claim_text),
            )
        )
        total_characters += len(text)
        position += 1
        char_start = 0
        segment_count += 1

    return slices, None


def _process_run(
    views: tuple[_SegmentView, ...],
    *,
    representation_id: str,
    candidate_limit: int,
    maximum_claim_characters: int,
    maximum_window_seconds: float,
) -> ClaimStreamResult:
    candidates: list[ClaimCandidate] = []
    unresolved: list[UnresolvedSourceRegion] = []
    action_counts: dict[str, int] = {}
    position, char_start = _normalize_cursor(views, 0, 0)
    loop_guard = 0

    while position < len(views) and len(candidates) < candidate_limit:
        loop_guard += 1
        if loop_guard > max(1000, len(views) * 20):
            raise RuntimeError("source-statement stream cursor did not converge")

        source_start = (position, char_start)
        start_view = views[position]
        start_seconds = start_view.segment.start_seconds
        base: list[_Slice] = []
        total_characters = 0
        p = position
        c = char_start
        stop_reason = "end_of_stream"

        while p < len(views):
            view = views[p]
            text = view.claim_text[c:]
            separator = 1 if base else 0

            if (
                start_seconds is not None
                and view.segment.end_seconds is not None
                and base
                and view.segment.end_seconds - start_seconds
                > maximum_window_seconds
            ):
                stop_reason = "maximum_window_seconds"
                break

            if (
                base
                and total_characters + separator + len(text)
                > maximum_claim_characters
            ):
                stop_reason = "maximum_claim_characters"
                break

            if not base and len(text) > maximum_claim_characters:
                if not view.partial_allowed:
                    stop_reason = "corrected_segment_exceeds_claim_limit"
                    break
                allowed = maximum_claim_characters
                base.append(
                    _make_slice(
                        views,
                        p,
                        c,
                        c + allowed,
                    )
                )
                total_characters = allowed
                c = c + allowed
                stop_reason = "maximum_claim_characters_partial_segment"
                break

            base.append(
                _make_slice(
                    views,
                    p,
                    c,
                    len(view.claim_text),
                )
            )
            total_characters += separator + len(text)
            p += 1
            c = 0

            if _safe_end(text):
                stop_reason = "safe_boundary"
                break

        if stop_reason == "safe_boundary":
            next_cursor = _normalize_cursor(views, p, c)
            _append_candidate(
                candidates=candidates,
                representation_id=representation_id,
                views=views,
                slices=base,
                action="safe",
                source_start=source_start,
                source_end=next_cursor,
            )
            action_counts["safe"] = action_counts.get("safe", 0) + 1
            position, char_start = next_cursor
            continue

        # If the run ended naturally, there is no following source to extend.
        # A terminally incomplete fragment is preserved as unresolved source.
        if not base:
            region, recovered = _recovery_region(
                views=views,
                start_position=position,
                start_char=char_start,
            )
            region_text = _render_claim_text(views, region)
            unresolved.append(
                UnresolvedSourceRegion(
                    reason=(
                        "unresolved_region_to_safe_boundary"
                        if recovered is not None
                        else "stream_stopped_unresolved"
                    ),
                    text=region_text,
                    evidence=_evidence_tuple(views, region),
                )
            )
            action_counts["unresolved_region"] = (
                action_counts.get("unresolved_region", 0) + 1
            )
            if recovered is None:
                break
            position, char_start = recovered
            continue

        # Try a bounded forward extension into at most three following segments.
        last_base_view = views[base[-1].view_position]
        current_end_seconds = last_base_view.segment.end_seconds
        extension: list[_Slice] = []
        added_characters = 0
        ep = p
        ec = c
        found_extension: tuple[int, int] | None = None

        for _ in range(_FORWARD_MAX_SEGMENTS):
            if ep >= len(views):
                break

            view = views[ep]
            if (
                current_end_seconds is not None
                and view.segment.end_seconds is not None
                and view.segment.end_seconds - current_end_seconds
                > _FORWARD_MAX_SECONDS
            ):
                break

            text = view.claim_text[ec:]
            remaining = _FORWARD_MAX_CHARACTERS - added_characters
            if remaining <= 0:
                break

            searchable = text[:remaining]
            boundary = _first_boundary(searchable)

            if boundary is not None:
                char_end = ec + boundary
                if (
                    not view.partial_allowed
                    and char_end != len(view.claim_text)
                ):
                    # No exact mapping for a partial reviewed correction.
                    break
                extension.append(
                    _make_slice(
                        views,
                        ep,
                        ec,
                        char_end,
                    )
                )
                found_extension = _normalize_cursor(
                    views,
                    ep,
                    char_end,
                )
                break

            if len(text) > remaining:
                break

            extension.append(
                _make_slice(
                    views,
                    ep,
                    ec,
                    len(view.claim_text),
                )
            )
            added_characters += len(text)
            ep += 1
            ec = 0

        if found_extension is not None:
            _append_candidate(
                candidates=candidates,
                representation_id=representation_id,
                views=views,
                slices=base + extension,
                action="extended_to_safe_boundary",
                source_start=source_start,
                source_end=found_extension,
            )
            action_counts["extended_to_safe_boundary"] = (
                action_counts.get("extended_to_safe_boundary", 0) + 1
            )
            position, char_start = found_extension
            continue

        # Forward repair failed. Emit the latest safe prefix already present in
        # the base and requeue every trailing character as the next cursor.
        trim_index: int | None = None
        trim_char_end: int | None = None

        for index in range(len(base) - 1, -1, -1):
            slice_item = base[index]
            slice_text = _slice_claim_text(views, slice_item)
            boundary = _last_boundary(slice_text)
            if boundary is None:
                continue
            candidate_end = slice_item.char_start + boundary
            view = views[slice_item.view_position]
            if (
                not view.partial_allowed
                and candidate_end != len(view.claim_text)
            ):
                continue
            trim_index = index
            trim_char_end = candidate_end
            break

        if trim_index is not None and trim_char_end is not None:
            prefix = [
                *base[:trim_index],
                _make_slice(
                    views,
                    base[trim_index].view_position,
                    base[trim_index].char_start,
                    trim_char_end,
                ),
            ]
            next_cursor = _normalize_cursor(
                views,
                base[trim_index].view_position,
                trim_char_end,
            )
            _append_candidate(
                candidates=candidates,
                representation_id=representation_id,
                views=views,
                slices=prefix,
                action="trimmed_to_safe_boundary_with_carry",
                source_start=source_start,
                source_end=next_cursor,
            )
            action_counts["trimmed_to_safe_boundary_with_carry"] = (
                action_counts.get(
                    "trimmed_to_safe_boundary_with_carry",
                    0,
                )
                + 1
            )
            position, char_start = next_cursor
            continue

        # No provider-safe prefix exists. Preserve the exact source as an
        # unresolved region until the next safe boundary, then resume after it.
        region, recovered = _recovery_region(
            views=views,
            start_position=position,
            start_char=char_start,
        )
        unresolved.append(
            UnresolvedSourceRegion(
                reason=(
                    "unresolved_region_to_safe_boundary"
                    if recovered is not None
                    else "stream_stopped_unresolved"
                ),
                text=_render_claim_text(views, region),
                evidence=_evidence_tuple(views, region),
            )
        )
        action_counts["unresolved_region"] = (
            action_counts.get("unresolved_region", 0) + 1
        )
        if recovered is None:
            break
        position, char_start = recovered

    diagnostics: dict[str, object] = {
        "extractor": EXTRACTOR_NAME,
        "seam_stream_policy": SEAM_STREAM_POLICY_VERSION,
        "provider_eligible_candidate_count": len(candidates),
        "unresolved_region_count": len(unresolved),
        "action_counts": dict(sorted(action_counts.items())),
    }
    return ClaimStreamResult(
        candidates=tuple(candidates),
        unresolved_regions=tuple(unresolved),
        diagnostics=diagnostics,
        final_cursor=(position, char_start),
    )


def build_source_statement_stream_candidates(
    segments: tuple[ClaimSegment, ...],
    *,
    representation_id: str,
    limit: int = 50,
    maximum_claim_characters: int = 350,
    maximum_window_seconds: float = 15.0,
) -> ClaimStreamResult:
    """Build seam-safe source statements while preserving stream continuity."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero")
    if maximum_claim_characters < 40:
        raise ValueError("maximum_claim_characters must be at least 40")
    if maximum_window_seconds <= 0:
        raise ValueError("maximum_window_seconds must be greater than zero")

    all_candidates: list[ClaimCandidate] = []
    all_unresolved: list[UnresolvedSourceRegion] = []
    merged_actions: dict[str, int] = {}

    run: list[_SegmentView] = []

    def flush_run() -> None:
        if not run or len(all_candidates) >= limit:
            run.clear()
            return
        result = _process_run(
            tuple(run),
            representation_id=representation_id,
            candidate_limit=limit - len(all_candidates),
            maximum_claim_characters=maximum_claim_characters,
            maximum_window_seconds=maximum_window_seconds,
        )
        all_candidates.extend(result.candidates)
        all_unresolved.extend(result.unresolved_regions)
        actions = result.diagnostics.get("action_counts", {})
        if isinstance(actions, dict):
            for key, value in actions.items():
                if isinstance(key, str) and isinstance(value, int):
                    merged_actions[key] = merged_actions.get(key, 0) + value
        run.clear()

    for segment in segments:
        if len(all_candidates) >= limit:
            break
        if segment.review_status == "rejected":
            flush_run()
            continue
        view = _segment_view(segment)
        if view is None:
            flush_run()
            continue
        run.append(view)

    flush_run()

    return ClaimStreamResult(
        candidates=tuple(all_candidates),
        unresolved_regions=tuple(all_unresolved),
        diagnostics={
            "extractor": EXTRACTOR_NAME,
            "seam_stream_policy": SEAM_STREAM_POLICY_VERSION,
            "seam_stream_policy_sha256": SEAM_STREAM_POLICY_V2_2_SHA256,
            "provider_eligible_candidate_count": len(all_candidates),
            "unresolved_region_count": len(all_unresolved),
            "action_counts": dict(sorted(merged_actions.items())),
        },
        final_cursor=None,
    )


def build_source_statement_candidates(
    segments: tuple[ClaimSegment, ...],
    *,
    representation_id: str,
    limit: int = 50,
    maximum_claim_characters: int = 350,
    maximum_window_seconds: float = 15.0,
) -> tuple[ClaimCandidate, ...]:
    """Return provider-eligible seam-safe source-statement candidates."""
    return build_source_statement_stream_candidates(
        segments,
        representation_id=representation_id,
        limit=limit,
        maximum_claim_characters=maximum_claim_characters,
        maximum_window_seconds=maximum_window_seconds,
    ).candidates
