"""Canonical scientific serialization — Scientific Foundation V1.1."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Iterable, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

ASSERTION_KINDS = frozenset({
    "relational",
    "measurement",
    "event",
    "process",
    "classification",
    "temporal_pattern",
})


def normalize_decimal(value: str | int | Decimal) -> str:
    if isinstance(value, (bool, float)):
        raise TypeError(
            "Scientific decimals must originate from str/int/Decimal, never native float/bool"
        )
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid decimal: {value!r}") from exc
    if not number.is_finite():
        raise ValueError("NaN/Infinity forbidden")
    if number == 0:
        return "0"
    normalized = number.normalize()
    if normalized == normalized.to_integral():
        return format(normalized.quantize(Decimal(1)), "f")
    return format(normalized, "f").rstrip("0").rstrip(".")


def decimal_value(value: str | int | Decimal) -> dict[str, str]:
    return {"type": "decimal", "value": normalize_decimal(value)}


def _normalize_mapping(value: Mapping[object, Any]) -> dict[str, Any]:
    if value.get("type") == "decimal":
        if set(value) != {"type", "value"}:
            raise ValueError("Typed decimal object must contain exactly type/value")
        return decimal_value(value["value"])
    normalized = {
        unicodedata.normalize("NFC", str(key)): normalize_json_value(item)
        for key, item in value.items()
    }
    return {key: normalized[key] for key in sorted(normalized)}


def normalize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, int):
        return value
    if isinstance(value, (float, Decimal)):
        raise TypeError(
            "Native scientific numeric values are forbidden in canonical payload; "
            "use decimal_value() / typed decimal JSON"
        )
    if isinstance(value, (list, tuple)):
        return [normalize_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return _normalize_mapping(value)
    raise TypeError(f"Unsupported canonical JSON value: {type(value)!r}")


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        normalize_json_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_json_text(payload: object) -> str:
    return canonical_json_bytes(payload).decode("utf-8")


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def entity_ref(entity_id: str, revision: int) -> dict[str, object]:
    if not isinstance(entity_id, str) or not entity_id:
        raise ValueError("entity_id must be a non-empty string")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ValueError("entity revision must be an integer >= 1")
    return {
        "type": "entity_ref",
        "entity_id": entity_id,
        "entity_revision": revision,
    }


def _validated_participant(item: Mapping[str, Any]) -> dict[str, Any]:
    role = item.get("role")
    entity = item.get("entity")
    if not isinstance(role, str) or not role.strip():
        raise ValueError("participant role must be a non-empty string")
    if not isinstance(entity, Mapping):
        raise TypeError("participant entity must be an entity_ref mapping")
    if entity.get("type") != "entity_ref":
        raise ValueError("participant entity type must be entity_ref")
    revision: Any = entity.get("entity_revision")
    normalized_entity = entity_ref(
        str(entity.get("entity_id", "")),
        revision,
    )
    result: dict[str, Any] = {
        "role": unicodedata.normalize("NFC", role),
        "entity": normalized_entity,
    }
    if "occurrence" in item:
        occurrence = item["occurrence"]
        if isinstance(occurrence, bool) or not isinstance(occurrence, (int, str)):
            raise ValueError("participant occurrence must be int or str")
        result["occurrence"] = normalize_json_value(occurrence)
    extra = set(item) - {"role", "entity", "occurrence"}
    if extra:
        raise ValueError(f"unsupported participant fields: {sorted(extra)}")
    return result


def canonicalize_participants(
    participants: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    normalized = [_validated_participant(item) for item in participants]
    return sorted(
        normalized,
        key=lambda item: (
            item["role"],
            item["entity"]["entity_id"],
            item["entity"]["entity_revision"],
            canonical_json_text(item.get("occurrence")),
        ),
    )


def canonical_assertion_payload(
    *,
    assertion_kind: str,
    predicate: str,
    participants: Iterable[Mapping[str, Any]],
    value: Mapping[str, Any],
    qualifiers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if assertion_kind not in ASSERTION_KINDS:
        raise ValueError(f"unsupported assertion_kind: {assertion_kind!r}")
    if not isinstance(predicate, str) or not predicate:
        raise ValueError("predicate must be a non-empty string")
    if not isinstance(value, Mapping) or "kind" not in value:
        raise ValueError("assertion value must be a typed mapping with kind")
    payload = {
        "schema_version": "scientific-assertion-v1.1",
        "assertion_kind": assertion_kind,
        "predicate": unicodedata.normalize("NFC", predicate),
        "participants": canonicalize_participants(participants),
        "value": normalize_json_value(value),
        "qualifiers": normalize_json_value(qualifiers or {}),
    }
    return normalize_json_value(payload)
