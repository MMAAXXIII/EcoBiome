"""Strict semantic-claim contract and validation for EcoBiome Collector."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_EXTRACTOR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_PROPOSALS = 200
_MAX_CLAIM_CHARACTERS = 500
_MAX_INPUT_BYTES = 2 * 1024 * 1024


class SemanticClaimValidationError(ValueError):
    """Raised when untrusted semantic-claim output violates the contract."""


@dataclass(frozen=True, slots=True)
class SemanticExtractor:
    """Identify the semantic extractor that produced a proposal batch."""

    name: str
    version: str


@dataclass(frozen=True, slots=True)
class AtomicClaimProposal:
    """One untrusted atomic proposition referencing existing Evidence only."""

    source_claim_id: str
    source_claim_effective_text_sha256: str
    text: str
    semantic_type: str
    evidence_ids: tuple[str, ...]
    qualifiers: dict[str, object]


@dataclass(frozen=True, slots=True)
class AtomicClaimBatch:
    """Validated semantic-extractor output ready for guarded persistence."""

    schema_version: int
    extractor: SemanticExtractor
    proposals: tuple[AtomicClaimProposal, ...]


def _reject_constant(value: str) -> object:
    raise SemanticClaimValidationError(
        f"Non-finite JSON number is not allowed: {value}"
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SemanticClaimValidationError(
                f"Duplicate JSON object key: {key}"
            )
        result[key] = value
    return result


def _expect_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticClaimValidationError(f"{label} must be an object.")
    return value


def _expect_exact_keys(
    payload: dict[str, Any],
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
    label: str,
) -> None:
    keys = set(payload)
    missing = sorted(required - keys)
    extra = sorted(keys - required - optional)
    if missing:
        raise SemanticClaimValidationError(
            f"{label} is missing required keys: {missing}"
        )
    if extra:
        raise SemanticClaimValidationError(
            f"{label} contains unsupported keys: {extra}"
        )


def _require_nonempty_string(
    value: object,
    *,
    label: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise SemanticClaimValidationError(f"{label} must be a string.")
    if value != value.strip() or not value:
        raise SemanticClaimValidationError(
            f"{label} must be non-empty and already trimmed."
        )
    if len(value) > maximum:
        raise SemanticClaimValidationError(
            f"{label} exceeds {maximum} characters."
        )
    if any(ord(character) < 32 for character in value):
        raise SemanticClaimValidationError(
            f"{label} contains a control character."
        )
    return value


def _validate_uuid(value: object, label: str) -> str:
    text = _require_nonempty_string(
        value,
        label=label,
        maximum=64,
    )
    try:
        parsed = UUID(text)
    except ValueError as exc:
        raise SemanticClaimValidationError(
            f"{label} must be a UUID."
        ) from exc
    if str(parsed) != text:
        raise SemanticClaimValidationError(
            f"{label} must use canonical lowercase UUID text."
        )
    return str(parsed)


def _validate_hash(value: object, label: str) -> str:
    text = _require_nonempty_string(
        value,
        label=label,
        maximum=64,
    )
    if _HASH_RE.fullmatch(text) is None:
        raise SemanticClaimValidationError(
            f"{label} must be a lowercase SHA-256 hex digest."
        )
    return text


def _validate_qualifiers(value: object) -> dict[str, object]:
    payload = _expect_object(value, "proposal.qualifiers")
    if len(payload) > 20:
        raise SemanticClaimValidationError(
            "proposal.qualifiers may contain at most 20 entries."
        )
    result: dict[str, object] = {}
    for key, item in payload.items():
        if _TOKEN_RE.fullmatch(key) is None:
            raise SemanticClaimValidationError(
                f"Invalid qualifier key: {key!r}"
            )
        if not (
            item is None
            or isinstance(item, (str, int, float, bool))
        ):
            raise SemanticClaimValidationError(
                f"Qualifier {key!r} must be a JSON scalar."
            )
        if isinstance(item, float) and not math.isfinite(item):
            raise SemanticClaimValidationError(
                f"Qualifier {key!r} must be finite."
            )
        if isinstance(item, str) and len(item) > 200:
            raise SemanticClaimValidationError(
                f"Qualifier {key!r} exceeds 200 characters."
            )
        result[key] = item
    return result


def parse_atomic_claim_batch(payload: object) -> AtomicClaimBatch:
    """Validate one untrusted semantic-extractor payload."""
    root = _expect_object(payload, "root")
    _expect_exact_keys(
        root,
        required=frozenset({"schema_version", "extractor", "proposals"}),
        label="root",
    )

    if root["schema_version"] != 1:
        raise SemanticClaimValidationError(
            "schema_version must equal 1."
        )

    extractor_payload = _expect_object(root["extractor"], "extractor")
    _expect_exact_keys(
        extractor_payload,
        required=frozenset({"name", "version"}),
        label="extractor",
    )
    extractor_name = _require_nonempty_string(
        extractor_payload["name"],
        label="extractor.name",
        maximum=64,
    )
    extractor_version = _require_nonempty_string(
        extractor_payload["version"],
        label="extractor.version",
        maximum=64,
    )
    if _EXTRACTOR_RE.fullmatch(extractor_name) is None:
        raise SemanticClaimValidationError(
            "extractor.name contains unsupported characters."
        )
    if _EXTRACTOR_RE.fullmatch(extractor_version) is None:
        raise SemanticClaimValidationError(
            "extractor.version contains unsupported characters."
        )

    raw_proposals = root["proposals"]
    if not isinstance(raw_proposals, list):
        raise SemanticClaimValidationError("proposals must be an array.")
    if len(raw_proposals) > _MAX_PROPOSALS:
        raise SemanticClaimValidationError(
            f"proposals may contain at most {_MAX_PROPOSALS} items."
        )

    proposals: list[AtomicClaimProposal] = []
    for index, raw_proposal in enumerate(raw_proposals, start=1):
        label = f"proposal[{index}]"
        proposal = _expect_object(raw_proposal, label)
        _expect_exact_keys(
            proposal,
            required=frozenset(
                {
                    "source_claim_id",
                    "source_claim_effective_text_sha256",
                    "text",
                    "semantic_type",
                    "evidence_ids",
                }
            ),
            optional=frozenset({"qualifiers"}),
            label=label,
        )

        source_claim_id = _validate_uuid(
            proposal["source_claim_id"],
            f"{label}.source_claim_id",
        )
        source_hash = _validate_hash(
            proposal["source_claim_effective_text_sha256"],
            f"{label}.source_claim_effective_text_sha256",
        )
        text = _require_nonempty_string(
            proposal["text"],
            label=f"{label}.text",
            maximum=_MAX_CLAIM_CHARACTERS,
        )
        if len(text) < 8:
            raise SemanticClaimValidationError(
                f"{label}.text must contain at least 8 characters."
            )

        semantic_type = _require_nonempty_string(
            proposal["semantic_type"],
            label=f"{label}.semantic_type",
            maximum=64,
        )
        if _TOKEN_RE.fullmatch(semantic_type) is None:
            raise SemanticClaimValidationError(
                f"{label}.semantic_type must be lower_snake_case."
            )

        raw_evidence_ids = proposal["evidence_ids"]
        if not isinstance(raw_evidence_ids, list) or not raw_evidence_ids:
            raise SemanticClaimValidationError(
                f"{label}.evidence_ids must be a non-empty array."
            )
        if len(raw_evidence_ids) > 50:
            raise SemanticClaimValidationError(
                f"{label}.evidence_ids may contain at most 50 IDs."
            )
        evidence_ids = tuple(
            _validate_uuid(item, f"{label}.evidence_ids")
            for item in raw_evidence_ids
        )
        if len(set(evidence_ids)) != len(evidence_ids):
            raise SemanticClaimValidationError(
                f"{label}.evidence_ids contains duplicates."
            )

        qualifiers = _validate_qualifiers(
            proposal.get("qualifiers", {})
        )

        proposals.append(
            AtomicClaimProposal(
                source_claim_id=source_claim_id,
                source_claim_effective_text_sha256=source_hash,
                text=text,
                semantic_type=semantic_type,
                evidence_ids=evidence_ids,
                qualifiers=qualifiers,
            )
        )

    return AtomicClaimBatch(
        schema_version=1,
        extractor=SemanticExtractor(
            name=extractor_name,
            version=extractor_version,
        ),
        proposals=tuple(proposals),
    )


def load_atomic_claim_batch(path: str | Path) -> AtomicClaimBatch:
    """Load strict JSON without duplicate keys or non-finite numbers."""
    source = Path(path).expanduser().resolve()
    if source.stat().st_size > _MAX_INPUT_BYTES:
        raise SemanticClaimValidationError(
            f"Semantic claim input exceeds {_MAX_INPUT_BYTES} bytes."
        )
    raw = source.read_text(encoding="utf-8")
    try:
        payload = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise SemanticClaimValidationError(
            f"Invalid JSON: {exc}"
        ) from exc
    return parse_atomic_claim_batch(payload)
