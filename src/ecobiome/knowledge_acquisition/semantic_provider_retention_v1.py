"""Transactional retention bridge for provider runs and Semantic Candidates.

G4 closes the provider-run/origin/CAS integration seam without changing the
Scientific Foundation V6 physical schema. The bridge is provider-neutral and
never grants automatic scientific acceptance.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ecobiome.knowledge_acquisition.persistence import CollectorStore
from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    admit_provider_candidates_v2_9,
)
from ecobiome.knowledge_acquisition.provider_provenance_v2_9 import (
    canonical_json_sha256 as provider_canonical_json_sha256,
)
from ecobiome.knowledge_acquisition.provider_schema_v2_10 import (
    PROVIDER_WIRE_CONTRACT_V2_10,
    build_provider_schema_v2_10,
)
from ecobiome.knowledge_acquisition.semantic_candidate_v2_11 import (
    build_semantic_candidate_v2_11,
    build_semantic_candidates_v2_11,
)
from ecobiome.knowledge_acquisition.semantic_extraction import (
    build_semantic_extraction_request,
)
from ecobiome.knowledge_persistence import (
    SemanticCandidateEvidenceLinksRow,
    SemanticCandidatesRow,
    SemanticProviderCandidateOriginsRow,
    SemanticProviderRunClaimInputsRow,
    SemanticProviderRunEventsRow,
    SemanticProviderRunEvidenceInputsRow,
    SemanticProviderRunsRow,
)
from ecobiome.knowledge_persistence.contracts import (
    ScientificFoundationUnitOfWork,
)
from ecobiome.knowledge_persistence.serialization import canonical_json_text

PROVIDER_RETENTION_V1 = "ecobiome-provider-retention-v1"
_PROVIDER_CONTRACT_VERSION = "2.10"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_REVIEW_STATUS_BY_DECISION = {
    "accept": "accepted",
    "correct": "corrected",
    "reject": "rejected",
}


class ProviderRetentionError(ValueError):
    """Raised when a provider retention request violates G4 invariants."""


@dataclass(frozen=True, slots=True)
class ProviderRetentionReceipt:
    """Audit receipt for one retained provider run."""

    run_id: str
    run_inserted: bool
    claim_input_inserted_count: int
    evidence_input_inserted_count: int
    provider_event_inserted_count: int
    candidate_inserted_count: int
    candidate_count: int
    origin_inserted_count: int
    origin_count: int
    candidate_ids: tuple[str, ...]
    request_artifact_store_key: str
    response_artifact_store_key: str
    validated_output_artifact_store_key: str
    automatic_scientific_acceptance: bool = False


def _require_nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderRetentionError(f"{label} must be non-empty text")
    return unicodedata.normalize("NFC", value)


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _HASH_RE.fullmatch(value) is None:
        raise ProviderRetentionError(f"{label} must be lowercase SHA-256")
    return value


def _json_safe_value(value: object, path: str = "payload") -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ProviderRetentionError(f"non-finite provider number: {path}")
        return value
    if isinstance(value, list):
        return [
            _json_safe_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, tuple):
        return [
            _json_safe_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProviderRetentionError(
                    f"provider JSON key must be text: {path}"
                )
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ProviderRetentionError(
                    f"duplicate provider JSON key after NFC normalization: "
                    f"{path}.{key}"
                )
            normalized[normalized_key] = _json_safe_value(
                item,
                f"{path}.{key}",
            )
        return {key: normalized[key] for key in sorted(normalized)}
    raise ProviderRetentionError(
        f"unsupported provider JSON value at {path}: {type(value)!r}"
    )


def provider_json_bytes_v1(payload: object) -> bytes:
    """Return deterministic provider-domain JSON bytes.

    Unlike scientific canonical JSON, provider wire JSON may contain finite
    native floats. NaN and Infinity remain forbidden.
    """
    return json.dumps(
        _json_safe_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _provider_json_text(payload: object) -> str:
    return provider_json_bytes_v1(payload).decode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _candidate_id(candidate_sha256: str) -> str:
    value = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"urn:ecobiome:semantic-candidate:v2.11:{candidate_sha256}",
    )
    return str(value)


def _event_id(run_id: str, event_index: int) -> str:
    value = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"urn:ecobiome:provider-run:{run_id}:event:{event_index}",
    )
    return str(value)


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProviderRetentionError(f"{label} must be an object")
    return value


def _collector_source_claims(
    source_request: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    if source_request.get("schema_version") != 1:
        raise ProviderRetentionError(
            "Collector source request schema_version must be 1"
        )
    if source_request.get("task") != "extract_atomic_source_propositions":
        raise ProviderRetentionError("unexpected Collector semantic task")

    rules = _mapping(source_request.get("rules"), "source_request.rules")
    if rules.get("automatic_scientific_acceptance") is not False:
        raise ProviderRetentionError(
            "Collector source request must deny automatic scientific acceptance"
        )

    claims = source_request.get("source_claims")
    if not isinstance(claims, list) or not claims:
        raise ProviderRetentionError(
            "Collector source request must contain source_claims"
        )
    if len(claims) > 50:
        raise ProviderRetentionError(
            "Collector source request exceeds the 50-Claim bound"
        )
    if not all(isinstance(item, Mapping) for item in claims):
        raise ProviderRetentionError("Collector source Claim must be an object")
    return list(claims)


def _effective_claim_snapshot(
    uow: ScientificFoundationUnitOfWork,
    claim_id: str,
) -> tuple[str, str, str]:
    row = uow.provenance.get_source_claim(claim_id)
    if row is None:
        raise ProviderRetentionError(
            f"Scientific Foundation source Claim missing: {claim_id}"
        )

    original_sha = _sha256_bytes(row.claim_text.encode("utf-8"))
    if original_sha != row.claim_text_sha256:
        raise ProviderRetentionError(
            f"Scientific Foundation Claim text SHA mismatch: {claim_id}"
        )

    events = tuple(uow.provenance.get_claim_review_events(claim_id))
    if not events:
        raise ProviderRetentionError(
            f"Source Claim requires human review before provider retention: "
            f"{claim_id}"
        )

    effective_text = row.claim_text
    effective_sha = row.claim_text_sha256
    for event in events:
        if event.decision == "correct":
            corrected_text = event.corrected_text
            corrected_sha = event.corrected_text_sha256
            if corrected_text is None or corrected_sha is None:
                raise ProviderRetentionError(
                    f"Malformed Claim correction history: {claim_id}"
                )
            actual = _sha256_bytes(corrected_text.encode("utf-8"))
            if actual != corrected_sha:
                raise ProviderRetentionError(
                    f"Claim correction SHA mismatch: {claim_id}"
                )
            effective_text = corrected_text
            effective_sha = corrected_sha

    latest = events[-1]
    status = _REVIEW_STATUS_BY_DECISION.get(latest.decision)
    if status is None:
        raise ProviderRetentionError(
            f"Unsupported Claim review decision: {latest.decision}"
        )
    if status == "rejected":
        raise ProviderRetentionError(
            f"Rejected Claim cannot enter provider retention: {claim_id}"
        )
    return effective_text, effective_sha, status


def _source_input_rows(
    uow: ScientificFoundationUnitOfWork,
    *,
    run_id: str,
    source_request: Mapping[str, Any],
    created_at: str,
) -> tuple[
    tuple[SemanticProviderRunClaimInputsRow, ...],
    tuple[SemanticProviderRunEvidenceInputsRow, ...],
]:
    claims = _collector_source_claims(source_request)

    claim_rows: list[SemanticProviderRunClaimInputsRow] = []
    evidence_rows: list[SemanticProviderRunEvidenceInputsRow] = []
    seen_claim_ids: set[str] = set()
    seen_evidence_ids: set[str] = set()

    for claim_order, claim in enumerate(claims):
        claim_id = _require_nonempty_text(
            claim.get("claim_id"),
            "source Claim ID",
        )
        if claim_id in seen_claim_ids:
            raise ProviderRetentionError(
                f"duplicate source Claim ID: {claim_id}"
            )
        seen_claim_ids.add(claim_id)

        request_text = _require_nonempty_text(
            claim.get("effective_text"),
            f"{claim_id}.effective_text",
        )
        request_sha = _require_sha256(
            claim.get("effective_text_sha256"),
            f"{claim_id}.effective_text_sha256",
        )
        if _sha256_bytes(request_text.encode("utf-8")) != request_sha:
            raise ProviderRetentionError(
                f"Collector effective Claim SHA mismatch: {claim_id}"
            )

        current_text, current_sha, current_status = _effective_claim_snapshot(
            uow,
            claim_id,
        )
        if current_text != request_text or current_sha != request_sha:
            raise ProviderRetentionError(
                f"Collector/V6 Claim snapshot drift: {claim_id}"
            )

        request_status = _require_nonempty_text(
            claim.get("review_status"),
            f"{claim_id}.review_status",
        )
        if request_status != current_status:
            raise ProviderRetentionError(
                f"Collector/V6 Claim review status drift: {claim_id}"
            )
        if request_status not in {"accepted", "corrected"}:
            raise ProviderRetentionError(
                f"Provider retention requires reviewed Claim: {claim_id}"
            )

        claim_rows.append(
            SemanticProviderRunClaimInputsRow(
                run_id=run_id,
                claim_id=claim_id,
                input_order=claim_order,
                claim_effective_text_sha256=request_sha,
                claim_review_status_at_run=request_status,
                created_at=created_at,
            )
        )

        evidence_items = claim.get("evidence")
        if not isinstance(evidence_items, list) or not evidence_items:
            raise ProviderRetentionError(
                f"Source Claim has no usable Evidence: {claim_id}"
            )

        for evidence_order, raw_evidence in enumerate(evidence_items):
            evidence = _mapping(
                raw_evidence,
                f"{claim_id}.evidence[{evidence_order}]",
            )
            evidence_id = _require_nonempty_text(
                evidence.get("evidence_id"),
                "Evidence ID",
            )
            if evidence_id in seen_evidence_ids:
                raise ProviderRetentionError(
                    f"duplicate Evidence ID: {evidence_id}"
                )
            seen_evidence_ids.add(evidence_id)

            segment_id = _require_nonempty_text(
                evidence.get("segment_id"),
                f"{evidence_id}.segment_id",
            )
            evidence_text = _require_nonempty_text(
                evidence.get("text"),
                f"{evidence_id}.text",
            )
            evidence_sha = _require_sha256(
                evidence.get("sha256"),
                f"{evidence_id}.sha256",
            )
            if _sha256_bytes(evidence_text.encode("utf-8")) != evidence_sha:
                raise ProviderRetentionError(
                    f"Collector Evidence SHA mismatch: {evidence_id}"
                )

            persisted = uow.provenance.get_source_evidence(evidence_id)
            if persisted is None:
                raise ProviderRetentionError(
                    f"Scientific Foundation Evidence missing: {evidence_id}"
                )
            if persisted.segment_id != segment_id:
                raise ProviderRetentionError(
                    f"Collector/V6 Evidence segment drift: {evidence_id}"
                )
            if persisted.evidence_text_sha256 != evidence_sha:
                raise ProviderRetentionError(
                    f"Collector/V6 Evidence SHA drift: {evidence_id}"
                )

            segment = uow.provenance.get_segment(segment_id)
            if segment is None or segment.text_inline is None:
                raise ProviderRetentionError(
                    f"Scientific Foundation segment text missing: {segment_id}"
                )
            if (
                _sha256_bytes(segment.text_inline.encode("utf-8"))
                != segment.text_sha256
            ):
                raise ProviderRetentionError(
                    f"Scientific Foundation segment SHA mismatch: {segment_id}"
                )

            start = persisted.segment_char_start
            end = persisted.segment_char_end
            if start < 0 or end <= start or end > len(segment.text_inline):
                raise ProviderRetentionError(
                    f"Scientific Foundation Evidence offsets invalid: "
                    f"{evidence_id}"
                )
            if segment.text_inline[start:end] != evidence_text:
                raise ProviderRetentionError(
                    f"Collector/V6 Evidence text drift: {evidence_id}"
                )

            segment_status = segment.review_status or "pending"
            if segment_status == "rejected":
                raise ProviderRetentionError(
                    f"Rejected Evidence segment cannot enter provider run: "
                    f"{segment_id}"
                )

            evidence_rows.append(
                SemanticProviderRunEvidenceInputsRow(
                    run_id=run_id,
                    claim_id=claim_id,
                    evidence_id=evidence_id,
                    evidence_order=evidence_order,
                    evidence_text_sha256=evidence_sha,
                    segment_review_status_at_run=segment_status,
                    created_at=created_at,
                )
            )

    return tuple(claim_rows), tuple(evidence_rows)


def _candidate_row(
    candidate: Mapping[str, Any],
    *,
    created_at: str,
) -> tuple[SemanticCandidatesRow, tuple[SemanticCandidateEvidenceLinksRow, ...]]:
    candidate_sha = _require_sha256(
        candidate.get("canonical_candidate_sha256"),
        "candidate canonical SHA",
    )
    candidate_id = _candidate_id(candidate_sha)
    candidate_json = canonical_json_text(candidate)
    document_sha = _sha256_bytes(candidate_json.encode("utf-8"))

    contract = _mapping(candidate.get("contract"), "candidate.contract")
    source = _mapping(candidate.get("source"), "candidate.source")
    semantic = _mapping(candidate.get("semantic"), "candidate.semantic")

    evidence_ids = source.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not all(
        isinstance(item, str) and item for item in evidence_ids
    ):
        raise ProviderRetentionError("candidate Evidence IDs are malformed")

    row = SemanticCandidatesRow(
        id=candidate_id,
        schema_version=_require_nonempty_text(
            candidate.get("schema_version"),
            "candidate.schema_version",
        ),
        semantic_contract_name=_require_nonempty_text(
            contract.get("name"),
            "candidate.contract.name",
        ),
        semantic_contract_version=_require_nonempty_text(
            contract.get("version"),
            "candidate.contract.version",
        ),
        semantic_contract_sha256=_require_sha256(
            contract.get("canonical_sha256"),
            "candidate.contract.canonical_sha256",
        ),
        relation_type_basis_version=_require_nonempty_text(
            contract.get("relation_type_basis_version"),
            "candidate.contract.relation_type_basis_version",
        ),
        relation_type_registry_sha256=_require_sha256(
            contract.get("relation_type_registry_sha256"),
            "candidate.contract.relation_type_registry_sha256",
        ),
        grounding_policy_sha256=_require_sha256(
            contract.get("grounding_policy_sha256"),
            "candidate.contract.grounding_policy_sha256",
        ),
        claim_scoped_provenance_policy_sha256=_require_sha256(
            contract.get("claim_scoped_provenance_policy_sha256"),
            "candidate.contract.claim_scoped_provenance_policy_sha256",
        ),
        source_statement_claim_id=_require_nonempty_text(
            source.get("source_statement_claim_id"),
            "candidate.source.source_statement_claim_id",
        ),
        source_claim_effective_text_sha256=_require_sha256(
            source.get("source_claim_effective_text_sha256"),
            "candidate.source.source_claim_effective_text_sha256",
        ),
        semantic_type=_require_nonempty_text(
            semantic.get("semantic_type"),
            "candidate.semantic.semantic_type",
        ),
        relation=_require_nonempty_text(
            semantic.get("relation"),
            "candidate.semantic.relation",
        ),
        epistemic_class=_require_nonempty_text(
            semantic.get("epistemic_class"),
            "candidate.semantic.epistemic_class",
        ),
        promotion_readiness=_require_nonempty_text(
            candidate.get("promotion_readiness"),
            "candidate.promotion_readiness",
        ),
        automatic_scientific_acceptance=0,
        canonical_candidate_sha256=candidate_sha,
        canonical_candidate_document_sha256=document_sha,
        canonical_candidate_json=candidate_json,
        created_at=created_at,
    )

    links = tuple(
        SemanticCandidateEvidenceLinksRow(
            semantic_candidate_id=candidate_id,
            source_statement_claim_id=row.source_statement_claim_id,
            evidence_id=evidence_id,
            evidence_order=index,
            created_at=created_at,
        )
        for index, evidence_id in enumerate(evidence_ids)
    )
    return row, links


def _candidate_plan(
    *,
    compact_output: dict[str, Any],
    source_request: dict[str, Any],
    registry_v2_10: dict[str, Any],
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[tuple[int, str, str]],
]:
    admission = admit_provider_candidates_v2_9(
        compact_output,
        source_request,
        registry_v2_10,
    )
    batch = build_semantic_candidates_v2_11(
        admission,
        source_request,
        registry_v2_10,
    )

    raw_proposals = compact_output.get("p")
    if not isinstance(raw_proposals, list):
        raise ProviderRetentionError("provider compact output p must be an array")

    unique_candidates: dict[str, dict[str, Any]] = {}
    origins: list[tuple[int, str, str]] = []

    for proposal_index, raw_proposal in enumerate(raw_proposals):
        single = admit_provider_candidates_v2_9(
            {"p": [raw_proposal]},
            source_request,
            registry_v2_10,
            max_proposals=1,
        )
        if single["survivor_count"] == 0:
            continue

        survivor = single["survivors"][0]
        candidate = build_semantic_candidate_v2_11(
            survivor,
            source_request,
            registry_v2_10,
        )
        candidate_sha = str(candidate["canonical_candidate_sha256"])
        unique_candidates.setdefault(candidate_sha, candidate)
        origins.append(
            (
                proposal_index,
                provider_canonical_json_sha256(raw_proposal),
                candidate_sha,
            )
        )

    batch_candidates = batch.get("candidates")
    if not isinstance(batch_candidates, list):
        raise ProviderRetentionError("V2.11 candidate batch is malformed")
    expected_hashes = [
        str(item["canonical_candidate_sha256"])
        for item in batch_candidates
        if isinstance(item, Mapping)
    ]
    if expected_hashes != list(unique_candidates):
        raise ProviderRetentionError(
            "provider proposal-origin mapping diverged from V2.11 batch"
        )

    return admission, list(unique_candidates.values()), origins


def retain_validated_provider_run_v1(
    uow: ScientificFoundationUnitOfWork,
    *,
    source_request: dict[str, Any],
    compact_output: dict[str, Any],
    registry_v2_10: dict[str, Any],
    run_id: str,
    provider_name: str,
    provider_adapter_name: str,
    provider_adapter_version: str,
    endpoint: str | None,
    model_requested: str,
    instruction_sha256: str,
    request_body: bytes,
    response_body: bytes,
    safe_configuration: Mapping[str, Any],
    created_at: str,
    started_at: str | None = None,
    model_returned: str | None = None,
    provider_request_id: str | None = None,
    provider_response_id: str | None = None,
    http_status_code: int | None = None,
    response_status: str | None = None,
    content_type: str | None = None,
    usage: Mapping[str, Any] | None = None,
    diagnostics: Mapping[str, Any] | None = None,
) -> ProviderRetentionReceipt:
    """Retain one already-returned provider result inside an active V6 UoW.

    The function performs no network call and does not commit the UoW. CAS puts
    are immutable and may remain as unreferenced blobs if the surrounding
    SQLite transaction later rolls back.
    """
    run_id = _require_nonempty_text(run_id, "run_id")
    provider_name = _require_nonempty_text(provider_name, "provider_name")
    provider_adapter_name = _require_nonempty_text(
        provider_adapter_name,
        "provider_adapter_name",
    )
    provider_adapter_version = _require_nonempty_text(
        provider_adapter_version,
        "provider_adapter_version",
    )
    model_requested = _require_nonempty_text(
        model_requested,
        "model_requested",
    )
    instruction_sha256 = _require_sha256(
        instruction_sha256,
        "instruction_sha256",
    )
    created_at = _require_nonempty_text(created_at, "created_at")
    if not isinstance(request_body, bytes) or not request_body:
        raise ProviderRetentionError("request_body must be non-empty bytes")
    if not isinstance(response_body, bytes) or not response_body:
        raise ProviderRetentionError("response_body must be non-empty bytes")

    claim_rows, evidence_rows = _source_input_rows(
        uow,
        run_id=run_id,
        source_request=source_request,
        created_at=created_at,
    )

    provider_schema, _ = build_provider_schema_v2_10(
        source_request,
        registry_v2_10,
    )
    semantic_contract_sha = provider_canonical_json_sha256(registry_v2_10)
    output_schema_sha = provider_canonical_json_sha256(provider_schema)
    source_request_sha = provider_canonical_json_sha256(source_request)

    admission, candidates, origin_plan = _candidate_plan(
        compact_output=compact_output,
        source_request=source_request,
        registry_v2_10=registry_v2_10,
    )
    if admission.get("automatic_scientific_acceptance") is not False:
        raise ProviderRetentionError(
            "provider admission must deny automatic scientific acceptance"
        )

    safe_configuration_json = _provider_json_text(dict(safe_configuration))
    usage_json = _provider_json_text(dict(usage or {}))
    diagnostics_json = _provider_json_text(dict(diagnostics or {}))

    request_artifact = uow.artifact_store.put(request_body)
    response_artifact = uow.artifact_store.put(response_body)
    validated_output_bytes = provider_json_bytes_v1(compact_output)
    validated_artifact = uow.artifact_store.put(validated_output_bytes)

    fingerprint = provider_canonical_json_sha256(
        {
            "retention_contract": PROVIDER_RETENTION_V1,
            "run_kind": "semantic_extraction",
            "provider_name": provider_name,
            "provider_adapter_name": provider_adapter_name,
            "provider_adapter_version": provider_adapter_version,
            "endpoint": endpoint,
            "model_requested": model_requested,
            "semantic_contract_name": PROVIDER_WIRE_CONTRACT_V2_10,
            "semantic_contract_version": _PROVIDER_CONTRACT_VERSION,
            "semantic_contract_sha256": semantic_contract_sha,
            "instruction_sha256": instruction_sha256,
            "output_schema_sha256": output_schema_sha,
            "source_request_sha256": source_request_sha,
            "request_body_sha256": request_artifact.sha256,
            "safe_configuration": dict(safe_configuration),
        }
    )

    run = SemanticProviderRunsRow(
        id=run_id,
        run_kind="semantic_extraction",
        provider_name=provider_name,
        provider_adapter_name=provider_adapter_name,
        provider_adapter_version=provider_adapter_version,
        endpoint=endpoint,
        model_requested=model_requested,
        semantic_contract_name=PROVIDER_WIRE_CONTRACT_V2_10,
        semantic_contract_version=_PROVIDER_CONTRACT_VERSION,
        semantic_contract_sha256=semantic_contract_sha,
        instruction_sha256=instruction_sha256,
        output_schema_sha256=output_schema_sha,
        source_request_sha256=source_request_sha,
        request_body_sha256=request_artifact.sha256,
        request_artifact_store_key=request_artifact.key,
        request_fingerprint_sha256=fingerprint,
        safe_configuration_json=safe_configuration_json,
        started_at=started_at,
        created_at=created_at,
    )

    run_inserted = uow.provider_audit.add_provider_run(run)
    claim_inserted = uow.provider_audit.add_provider_run_claim_inputs(
        claim_rows
    )
    evidence_inserted = uow.provider_audit.add_provider_run_evidence_inputs(
        evidence_rows
    )

    proposal_count = len(compact_output.get("p", []))
    received = SemanticProviderRunEventsRow(
        id=_event_id(run_id, 0),
        run_id=run_id,
        event_index=0,
        event_type="provider_response_received",
        model_returned=model_returned,
        provider_request_id=provider_request_id,
        provider_response_id=provider_response_id,
        http_status_code=http_status_code,
        response_status=response_status,
        content_type=content_type,
        response_body_sha256=response_artifact.sha256,
        response_artifact_store_key=response_artifact.key,
        validated_output_sha256=None,
        validated_output_artifact_store_key=None,
        usage_json=usage_json,
        diagnostics_json=diagnostics_json,
        proposal_count=proposal_count,
        created_at=created_at,
    )
    validated = SemanticProviderRunEventsRow(
        id=_event_id(run_id, 1),
        run_id=run_id,
        event_index=1,
        event_type="validated",
        model_returned=model_returned,
        provider_request_id=provider_request_id,
        provider_response_id=provider_response_id,
        http_status_code=http_status_code,
        response_status=response_status,
        content_type=content_type,
        response_body_sha256=None,
        response_artifact_store_key=None,
        validated_output_sha256=validated_artifact.sha256,
        validated_output_artifact_store_key=validated_artifact.key,
        usage_json=usage_json,
        diagnostics_json=diagnostics_json,
        proposal_count=proposal_count,
        created_at=created_at,
    )
    event_inserted = uow.provider_audit.add_provider_run_events(
        [received, validated]
    )

    persisted_candidate_ids: dict[str, str] = {}
    candidate_inserted = 0
    for candidate in candidates:
        candidate_row, links = _candidate_row(
            candidate,
            created_at=created_at,
        )
        persisted, inserted = uow.semantic_candidates.add_candidate(
            candidate_row,
            links,
        )
        candidate_inserted += int(inserted)
        persisted_candidate_ids[
            candidate_row.canonical_candidate_sha256
        ] = persisted.id

    origin_rows = [
        SemanticProviderCandidateOriginsRow(
            run_id=run_id,
            proposal_index=proposal_index,
            semantic_candidate_id=persisted_candidate_ids[candidate_sha],
            proposal_sha256=proposal_sha,
            created_at=created_at,
        )
        for proposal_index, proposal_sha, candidate_sha in origin_plan
    ]
    origin_inserted = uow.provider_audit.add_provider_candidate_origins(
        origin_rows
    )

    completed = SemanticProviderRunEventsRow(
        id=_event_id(run_id, 2),
        run_id=run_id,
        event_index=2,
        event_type="completed",
        model_returned=model_returned,
        provider_request_id=provider_request_id,
        provider_response_id=provider_response_id,
        http_status_code=http_status_code,
        response_status=response_status,
        content_type=content_type,
        response_body_sha256=None,
        response_artifact_store_key=None,
        validated_output_sha256=None,
        validated_output_artifact_store_key=None,
        usage_json="{}",
        diagnostics_json="{}",
        proposal_count=proposal_count,
        created_at=created_at,
    )
    event_inserted += uow.provider_audit.add_provider_run_events([completed])

    ordered_candidate_ids = tuple(
        persisted_candidate_ids[
            str(candidate["canonical_candidate_sha256"])
        ]
        for candidate in candidates
    )
    return ProviderRetentionReceipt(
        run_id=run_id,
        run_inserted=run_inserted,
        claim_input_inserted_count=claim_inserted,
        evidence_input_inserted_count=evidence_inserted,
        provider_event_inserted_count=event_inserted,
        candidate_inserted_count=candidate_inserted,
        candidate_count=len(candidates),
        origin_inserted_count=origin_inserted,
        origin_count=len(origin_rows),
        candidate_ids=ordered_candidate_ids,
        request_artifact_store_key=request_artifact.key,
        response_artifact_store_key=response_artifact.key,
        validated_output_artifact_store_key=validated_artifact.key,
        automatic_scientific_acceptance=False,
    )


def retain_collector_provider_run_v1(
    collector_store: CollectorStore,
    claim_ids: Sequence[str],
    uow: ScientificFoundationUnitOfWork,
    **kwargs: Any,
) -> ProviderRetentionReceipt:
    """Build the canonical Collector source request, then retain provider output."""
    source_request = build_semantic_extraction_request(
        collector_store,
        tuple(claim_ids),
    )
    return retain_validated_provider_run_v1(
        uow,
        source_request=source_request,
        **kwargs,
    )
