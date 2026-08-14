from decimal import Decimal

import pytest

from ecobiome.knowledge_persistence.serialization import (
    canonical_assertion_payload,
    canonical_json_text,
    canonical_sha256,
    decimal_value,
    entity_ref,
    normalize_decimal,
)


def test_decimal_normalization_and_typed_decimal() -> None:
    assert normalize_decimal("37.000") == "37"
    assert normalize_decimal(Decimal("0.0100")) == "0.01"
    assert decimal_value("37.000") == {"type": "decimal", "value": "37"}
    with pytest.raises(TypeError):
        normalize_decimal(37.0)  # type: ignore[arg-type]


def test_native_float_and_decimal_are_forbidden_in_payload() -> None:
    with pytest.raises(TypeError):
        canonical_json_text({"x": 37.0})
    with pytest.raises(TypeError):
        canonical_json_text({"x": Decimal(37)})


def test_typed_decimal_is_normalized_but_numeric_string_is_distinct() -> None:
    typed_a = {"x": {"type": "decimal", "value": "37.000"}}
    typed_b = {"x": {"type": "decimal", "value": "37"}}
    categorical = {"x": "37"}
    assert canonical_sha256(typed_a) == canonical_sha256(typed_b)
    assert canonical_sha256(typed_a) != canonical_sha256(categorical)


def test_key_order_and_nfc_are_canonical() -> None:
    left = {"b": 2, "a": "e\u0301"}
    right = {"a": "é", "b": 2}
    assert canonical_json_text(left) == canonical_json_text(right)
    assert canonical_sha256(left) == canonical_sha256(right)


def test_structural_integer_entity_revision_remains_integer() -> None:
    ref = entity_ref("entity-1", 1)
    assert ref["entity_revision"] == 1
    assert isinstance(ref["entity_revision"], int)
    with pytest.raises(ValueError):
        entity_ref("entity-1", 0)


def test_assertion_participants_are_order_independent() -> None:
    a = entity_ref("entity-a", 1)
    b = entity_ref("entity-b", 2)
    left = canonical_assertion_payload(
        assertion_kind="relational",
        predicate="interacts_with",
        participants=[
            {"role": "patient", "entity": b},
            {"role": "agent", "entity": a},
        ],
        value={"kind": "none"},
        qualifiers={"context": "field"},
    )
    right = canonical_assertion_payload(
        assertion_kind="relational",
        predicate="interacts_with",
        participants=[
            {"role": "agent", "entity": a},
            {"role": "patient", "entity": b},
        ],
        value={"kind": "none"},
        qualifiers={"context": "field"},
    )
    assert canonical_sha256(left) == canonical_sha256(right)


def test_epistemic_status_is_not_assertion_kind() -> None:
    with pytest.raises(ValueError):
        canonical_assertion_payload(
            assertion_kind="interpretive_conclusion",
            predicate="spawning_initiation_time_pattern",
            participants=[{"role": "organism", "entity": entity_ref("population-gifu-bi", 1)}],
            value={"kind": "temporal_pattern", "pattern": "around_midnight", "details": {}},
            qualifiers={"generalization_ceiling": "study_sites"},
        )
