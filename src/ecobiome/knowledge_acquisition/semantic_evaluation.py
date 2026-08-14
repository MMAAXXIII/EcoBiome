"""Deterministic evaluation of semantic batches against a reference fixture."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ecobiome.knowledge_acquisition.semantic_claims import AtomicClaimBatch

_WORD_RE = re.compile(r"[0-9A-Za-z]+")
_SCORE_DECIMALS = 6


@dataclass(frozen=True, slots=True)
class ProposalAlignment:
    """One candidate/reference alignment used for diagnostic scoring."""

    candidate_index: int
    reference_index: int
    source_claim_id: str
    semantic_type: str
    evidence_jaccard: float
    text_token_jaccard: float
    exact_evidence_match: bool


def _normalise_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_WORD_RE.findall(_normalise_text(text)))


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _evidence_jaccard(
    candidate: frozenset[str],
    reference: frozenset[str],
) -> float:
    if not candidate and not reference:
        return 1.0
    union = candidate | reference
    if not union:
        return 0.0
    return len(candidate & reference) / len(union)


def _round(value: float) -> float:
    return round(value, _SCORE_DECIMALS)


def evaluate_semantic_batch(
    candidate: AtomicClaimBatch,
    reference: AtomicClaimBatch,
) -> dict[str, object]:
    """Compare one validated candidate batch with a validated reference."""
    candidate_items = list(candidate.proposals)
    reference_items = list(reference.proposals)

    possible: list[
        tuple[float, float, int, int]
    ] = []
    for candidate_index, candidate_item in enumerate(candidate_items):
        for reference_index, reference_item in enumerate(reference_items):
            if candidate_item.source_claim_id != reference_item.source_claim_id:
                continue
            if candidate_item.semantic_type != reference_item.semantic_type:
                continue
            evidence_score = _evidence_jaccard(
                frozenset(candidate_item.evidence_ids),
                frozenset(reference_item.evidence_ids),
            )
            text_score = _jaccard(
                _tokens(candidate_item.text),
                _tokens(reference_item.text),
            )
            possible.append(
                (
                    evidence_score,
                    text_score,
                    candidate_index,
                    reference_index,
                )
            )

    possible.sort(
        key=lambda item: (
            item[0],
            item[1],
            -item[2],
            -item[3],
        ),
        reverse=True,
    )

    used_candidates: set[int] = set()
    used_references: set[int] = set()
    alignments: list[ProposalAlignment] = []
    for (
        evidence_score,
        text_score,
        candidate_index,
        reference_index,
    ) in possible:
        if candidate_index in used_candidates:
            continue
        if reference_index in used_references:
            continue
        candidate_item = candidate_items[candidate_index]
        reference_item = reference_items[reference_index]
        used_candidates.add(candidate_index)
        used_references.add(reference_index)
        alignments.append(
            ProposalAlignment(
                candidate_index=candidate_index,
                reference_index=reference_index,
                source_claim_id=candidate_item.source_claim_id,
                semantic_type=candidate_item.semantic_type,
                evidence_jaccard=evidence_score,
                text_token_jaccard=text_score,
                exact_evidence_match=(
                    frozenset(candidate_item.evidence_ids)
                    == frozenset(reference_item.evidence_ids)
                ),
            )
        )

    exact_matches = sum(
        1 for item in alignments if item.exact_evidence_match
    )
    candidate_count = len(candidate_items)
    reference_count = len(reference_items)

    precision = (
        exact_matches / candidate_count
        if candidate_count
        else 0.0
    )
    recall = (
        exact_matches / reference_count
        if reference_count
        else 0.0
    )
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    mean_evidence = (
        sum(item.evidence_jaccard for item in alignments)
        / len(alignments)
        if alignments
        else 0.0
    )
    mean_text = (
        sum(item.text_token_jaccard for item in alignments)
        / len(alignments)
        if alignments
        else 0.0
    )

    unmatched_candidates = sorted(
        set(range(candidate_count)) - used_candidates
    )
    unmatched_references = sorted(
        set(range(reference_count)) - used_references
    )

    return {
        "schema_version": 1,
        "metric_definition": {
            "exact_match": (
                "same source_claim_id, semantic_type, and exact Evidence ID set"
            ),
            "alignment": (
                "greedy one-to-one within source_claim_id + semantic_type; "
                "Evidence Jaccard first, token Jaccard second"
            ),
            "scientific_correctness_measured": False,
        },
        "candidate_extractor": {
            "name": candidate.extractor.name,
            "version": candidate.extractor.version,
        },
        "reference_extractor": {
            "name": reference.extractor.name,
            "version": reference.extractor.version,
        },
        "candidate_count": candidate_count,
        "reference_count": reference_count,
        "aligned_count": len(alignments),
        "exact_evidence_matches": exact_matches,
        "exact_precision": _round(precision),
        "exact_recall": _round(recall),
        "exact_f1": _round(f1),
        "mean_aligned_evidence_jaccard": _round(mean_evidence),
        "mean_aligned_text_token_jaccard": _round(mean_text),
        "unmatched_candidate_indices": [
            index + 1 for index in unmatched_candidates
        ],
        "unmatched_reference_indices": [
            index + 1 for index in unmatched_references
        ],
        "alignments": [
            {
                "candidate_index": item.candidate_index + 1,
                "reference_index": item.reference_index + 1,
                "source_claim_id": item.source_claim_id,
                "semantic_type": item.semantic_type,
                "evidence_jaccard": _round(item.evidence_jaccard),
                "text_token_jaccard": _round(
                    item.text_token_jaccard
                ),
                "exact_evidence_match": item.exact_evidence_match,
            }
            for item in alignments
        ],
    }
