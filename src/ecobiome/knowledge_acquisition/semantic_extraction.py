"""Bounded semantic-extraction harness and conservative benchmark baseline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.semantic_claims import (
    AtomicClaimBatch,
    parse_atomic_claim_batch,
)

_WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_MAX_SOURCE_CLAIMS = 50


class SemanticExtractionError(RuntimeError):
    """Raised when bounded semantic extraction cannot proceed safely."""


@runtime_checkable
class SemanticExtractor(Protocol):
    """Untrusted semantic extractor contract used by the harness."""

    name: str
    version: str

    def extract(self, request: dict[str, object]) -> object:
        """Return one untrusted semantic-claim contract payload."""


@dataclass(frozen=True, slots=True)
class SemanticExtractionRun:
    """One validated non-persisted extraction run."""

    request: dict[str, object]
    batch: AtomicClaimBatch


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalise_words(text: str) -> tuple[str, ...]:
    return tuple(
        word.casefold()
        for word in _WORD_RE.findall(text)
        if word.strip()
    )


def _require_source_statement(payload: dict[str, Any]) -> None:
    if payload["claim_kind"] != "source_statement":
        raise SemanticExtractionError(
            "Semantic extraction only accepts source_statement Claims."
        )
    if payload["review_status"] == "rejected":
        raise SemanticExtractionError(
            "Rejected source_statement Claims cannot be extracted."
        )


def build_semantic_extraction_request(
    store: CollectorStore,
    claim_ids: list[str] | tuple[str, ...],
) -> dict[str, object]:
    """Build a bounded immutable-view request from persisted Claims."""
    if not claim_ids:
        raise SemanticExtractionError(
            "At least one source Claim ID is required."
        )
    if len(claim_ids) > _MAX_SOURCE_CLAIMS:
        raise SemanticExtractionError(
            f"At most {_MAX_SOURCE_CLAIMS} source Claims may be exported."
        )
    if len(set(claim_ids)) != len(claim_ids):
        raise SemanticExtractionError(
            "Source Claim IDs must not contain duplicates."
        )

    source_claims: list[dict[str, object]] = []
    for claim_id in claim_ids:
        payload = store.get_claim_with_evidence(claim_id)
        _require_source_statement(payload)

        effective_text = str(payload["effective_text"])
        evidence_items: list[dict[str, object]] = []
        for evidence in payload["evidence"]:
            if evidence["segment_review_status"] == "rejected":
                continue
            text = str(evidence["evidence_text"])
            expected_sha = str(evidence["evidence_sha256"])
            if _sha256_text(text) != expected_sha:
                raise SemanticExtractionError(
                    "Persisted Evidence SHA-256 is inconsistent."
                )
            evidence_items.append(
                {
                    "evidence_id": str(evidence["id"]),
                    "segment_id": str(evidence["segment_id"]),
                    "segment_index": int(evidence["segment_index"]),
                    "text": text,
                    "sha256": expected_sha,
                    "start_seconds": evidence["start_seconds"],
                    "end_seconds": evidence["end_seconds"],
                    "page_number": evidence["page_number"],
                    "frame_start": evidence["frame_start"],
                    "frame_end": evidence["frame_end"],
                    "source": {
                        "source_id": str(evidence["source_id"]),
                        "source_type": str(evidence["source_type"]),
                        "canonical_locator": str(
                            evidence["canonical_locator"]
                        ),
                        "title": evidence["source_title"],
                        "author": evidence["source_author"],
                    },
                }
            )

        if not evidence_items:
            raise SemanticExtractionError(
                f"Source Claim {claim_id} has no usable Evidence."
            )

        source_claims.append(
            {
                "claim_id": str(payload["id"]),
                "review_status": str(payload["review_status"]),
                "effective_text": effective_text,
                "effective_text_sha256": _sha256_text(effective_text),
                "text_was_corrected": bool(
                    payload["text_was_corrected"]
                ),
                "evidence": evidence_items,
            }
        )

    return {
        "schema_version": 1,
        "task": "extract_atomic_source_propositions",
        "rules": {
            "output_contract": "semantic-claim-contract-v1",
            "atomic_propositions_only": True,
            "evidence_ids_must_come_from_parent_claim": True,
            "do_not_invent_evidence": True,
            "skip_ambiguous_or_incomplete_statements": True,
            "automatic_scientific_acceptance": False,
        },
        "source_claims": source_claims,
    }


def run_semantic_extractor(
    store: CollectorStore,
    extractor: SemanticExtractor,
    claim_ids: list[str] | tuple[str, ...],
) -> SemanticExtractionRun:
    """Run one untrusted extractor and validate its output contract."""
    request = build_semantic_extraction_request(store, claim_ids)
    raw = extractor.extract(request)
    batch = parse_atomic_claim_batch(raw)
    if batch.extractor.name != extractor.name:
        raise SemanticExtractionError(
            "Extractor output name does not match the invoked extractor."
        )
    if batch.extractor.version != extractor.version:
        raise SemanticExtractionError(
            "Extractor output version does not match the invoked extractor."
        )
    return SemanticExtractionRun(request=request, batch=batch)


def atomic_batch_to_payload(batch: AtomicClaimBatch) -> dict[str, object]:
    """Serialize one validated batch without persistence."""
    return {
        "schema_version": batch.schema_version,
        "extractor": {
            "name": batch.extractor.name,
            "version": batch.extractor.version,
        },
        "proposals": [
            {
                "source_claim_id": proposal.source_claim_id,
                "source_claim_effective_text_sha256": (
                    proposal.source_claim_effective_text_sha256
                ),
                "text": proposal.text,
                "semantic_type": proposal.semantic_type,
                "evidence_ids": list(proposal.evidence_ids),
                "qualifiers": proposal.qualifiers,
            }
            for proposal in batch.proposals
        ],
    }


@dataclass(frozen=True, slots=True)
class _PatternRule:
    """One deliberately simple benchmark-only lexical extraction rule."""

    semantic_type: str
    trigger_groups: tuple[tuple[str, ...], ...]
    output_text: str
    evidence_terms: tuple[str, ...]


class ConservativeFrenchLexicalExtractorV1:
    """Benchmark-only French lexical baseline; never a truth engine."""

    name = "conservative-french-lexical-baseline"
    version = "1.0"

    _RULES = (
        _PatternRule(
            semantic_type="geographic_origin",
            trigger_groups=(("asie",), ("japon",)),
            output_text=(
                "La source présente le poisson évoqué comme originaire "
                "d'Asie, principalement du Japon."
            ),
            evidence_terms=("asie", "japon"),
        ),
        _PatternRule(
            semantic_type="habitat",
            trigger_groups=(("rizi", "rési"),),
            output_text=(
                "La source indique que ce poisson vit dans les rizières."
            ),
            evidence_terms=("rizi", "rési"),
        ),
        _PatternRule(
            semantic_type="habitat",
            trigger_groups=(("estua",), ("mer",)),
            output_text=(
                "La source indique que ce poisson est présent jusque dans "
                "des estuaires marins."
            ),
            evidence_terms=("estua", "mer"),
        ),
        _PatternRule(
            semantic_type="robustness",
            trigger_groups=(("robust", "costaud"),),
            output_text="La source présente ce poisson comme robuste.",
            evidence_terms=("robust", "costaud"),
        ),
        _PatternRule(
            semantic_type="ph_tolerance",
            trigger_groups=(("ph",), ("variation",)),
            output_text=(
                "La source associe ce poisson à une tolérance aux "
                "variations de pH."
            ),
            evidence_terms=("ph", "variation"),
        ),
        _PatternRule(
            semantic_type="husbandry",
            trigger_groups=(("facile",),),
            output_text=(
                "La source présente ce poisson comme facile à maintenir."
            ),
            evidence_terms=("facile",),
        ),
        _PatternRule(
            semantic_type="mosquito_control",
            trigger_groups=(("moustiqu",),),
            output_text=(
                "La source affirme que ce poisson est efficace contre "
                "les moustiques."
            ),
            evidence_terms=("moustiqu",),
        ),
        _PatternRule(
            semantic_type="temperature_tolerance",
            trigger_groups=(("chaud",),),
            output_text=(
                "La source affirme que ce poisson supporte le chaud."
            ),
            evidence_terms=("chaud",),
        ),
        _PatternRule(
            semantic_type="temperature_tolerance",
            trigger_groups=(("froid",),),
            output_text=(
                "La source affirme que ce poisson supporte le froid."
            ),
            evidence_terms=("froid",),
        ),
        _PatternRule(
            semantic_type="volume_tolerance",
            trigger_groups=(("petit",), ("volume",)),
            output_text=(
                "La source affirme que ce poisson peut vivre dans de "
                "petits volumes."
            ),
            evidence_terms=("petit", "volume"),
        ),
        _PatternRule(
            semantic_type="volume_tolerance",
            trigger_groups=(("grand",), ("volume",)),
            output_text=(
                "La source affirme que ce poisson peut vivre dans de "
                "grands volumes."
            ),
            evidence_terms=("grand", "volume"),
        ),
    )

    @staticmethod
    def _contains_group(
        words: tuple[str, ...],
        alternatives: tuple[str, ...],
    ) -> bool:
        return any(
            any(word.startswith(prefix) for word in words)
            for prefix in alternatives
        )

    @classmethod
    def _rule_matches(
        cls,
        words: tuple[str, ...],
        rule: _PatternRule,
    ) -> bool:
        return all(
            cls._contains_group(words, group)
            for group in rule.trigger_groups
        )

    @staticmethod
    def _select_evidence_ids(
        claim: dict[str, object],
        terms: tuple[str, ...],
    ) -> list[str]:
        evidence = claim["evidence"]
        assert isinstance(evidence, list)
        selected: list[str] = []
        for item in evidence:
            assert isinstance(item, dict)
            words = _normalise_words(str(item["text"]))
            if any(
                any(word.startswith(term) for word in words)
                for term in terms
            ):
                selected.append(str(item["evidence_id"]))
        return selected

    def extract(self, request: dict[str, object]) -> object:
        """Produce conservative lexical candidates for benchmark purposes."""
        raw_claims = request.get("source_claims")
        if not isinstance(raw_claims, list):
            raise SemanticExtractionError(
                "Extraction request source_claims must be an array."
            )

        proposals: list[dict[str, object]] = []
        for raw_claim in raw_claims:
            if not isinstance(raw_claim, dict):
                raise SemanticExtractionError(
                    "Extraction request Claim must be an object."
                )
            effective_text = str(raw_claim["effective_text"])
            words = _normalise_words(effective_text)

            for rule in self._RULES:
                if not self._rule_matches(words, rule):
                    continue
                evidence_ids = self._select_evidence_ids(
                    raw_claim,
                    rule.evidence_terms,
                )
                if not evidence_ids:
                    continue
                proposals.append(
                    {
                        "source_claim_id": str(raw_claim["claim_id"]),
                        "source_claim_effective_text_sha256": str(
                            raw_claim["effective_text_sha256"]
                        ),
                        "text": rule.output_text,
                        "semantic_type": rule.semantic_type,
                        "evidence_ids": evidence_ids,
                        "qualifiers": {
                            "benchmark_only": True,
                            "automatic_scientific_acceptance": False,
                            "method": "conservative_lexical_rules",
                        },
                    }
                )

        if not proposals:
            raise SemanticExtractionError(
                "Benchmark extractor produced no atomic proposals."
            )

        return {
            "schema_version": 1,
            "extractor": {
                "name": self.name,
                "version": self.version,
            },
            "proposals": proposals,
        }
