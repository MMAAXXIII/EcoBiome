from __future__ import annotations

from ecobiome.knowledge_acquisition.semantic_grounding import (
    GROUNDING_POLICY_V1_1,
    GROUNDING_POLICY_V1_1_SHA256,
    audit_arguments,
    canonical_json_sha256,
    numeric_role_grounding,
    opaque_text_resolution,
    resolve_value_unit_pair,
    temperature_scope_domain_check,
    unit_role_resolution,
)


def test_frozen_policy_hash() -> None:
    assert canonical_json_sha256(GROUNDING_POLICY_V1_1) == (
        GROUNDING_POLICY_V1_1_SHA256
    )


def test_day_numeric_and_word_surfaces() -> None:
    assert numeric_role_grounding(
        "day",
        7,
        "Ammonia peaked on day 7.",
    )["state"] == "resolved"
    assert numeric_role_grounding(
        "day",
        7,
        "Ammonia peaked on day seven.",
    )["state"] == "resolved"
    assert numeric_role_grounding(
        "day",
        7,
        "Seven fish were sampled.",
    )["state"] == "ungrounded"


def test_temperature_requires_local_celsius_context() -> None:
    assert numeric_role_grounding(
        "temperature_c",
        28,
        "Fish were maintained at 28 °C.",
    )["state"] == "resolved"
    assert numeric_role_grounding(
        "temperature_c",
        28,
        "Fish were maintained at 28 degrees Celsius.",
    )["state"] == "resolved"
    assert numeric_role_grounding(
        "temperature_c",
        28,
        "The experiment lasted 28 days.",
    )["state"] == "ungrounded"


def test_single_letter_unit_does_not_match_possessive() -> None:
    assert unit_role_resolution(
        "s",
        "The system's response was measured.",
    )["state"] == "ungrounded"
    assert unit_role_resolution(
        "s",
        "The response was measured for 4 s.",
    )["state"] == "resolved"


def test_value_unit_pair_must_be_local() -> None:
    assert resolve_value_unit_pair(
        4,
        "years",
        "A four-year field experiment was conducted.",
    )["state"] == "resolved"
    assert resolve_value_unit_pair(
        4,
        "years",
        "The first phase lasted 4 days and the second 7 years.",
    )["state"] == "ungrounded_pair"
    assert resolve_value_unit_pair(
        7,
        "years",
        "The first phase lasted 4 days and the second 7 years.",
    )["state"] == "resolved"
    assert resolve_value_unit_pair(
        4,
        "years",
        "There were 4 years in phase A and 4 years in phase B.",
    )["state"] == "ambiguous"


def test_temperature_scope_domain_validation_is_conservative() -> None:
    assert temperature_scope_domain_check(
        "scant rainfall periods",
        "Responses changed during scant rainfall periods.",
    )["state"] == "domain_mismatch"
    assert temperature_scope_domain_check(
        "both experimental temperatures",
        "Responses differed at both experimental temperatures.",
    )["state"] == "domain_valid_unresolved"
    assert temperature_scope_domain_check(
        "both conditions",
        "Responses changed in both conditions.",
    )["state"] == "domain_unknown"


def test_opaque_text_is_grounded_but_never_resolved() -> None:
    grounded = opaque_text_resolution(
        "topic",
        "microbial communities",
        "The functioning of microbial communities was studied.",
    )
    assert grounded["state"] == "grounded_opaque_unresolved"
    assert grounded["scientifically_scoreable"] is False
    assert opaque_text_resolution(
        "topic",
        "invented concept",
        "The functioning of microbial communities was studied.",
    )["state"] == "ungrounded"


def test_joint_argument_audit_marks_value_and_unit_scoreable() -> None:
    audit = audit_arguments(
        {"value": 4, "unit": "years"},
        "A four-year field experiment was conducted.",
    )
    assert audit["records"]["value"]["state"] == "resolved"
    assert audit["records"]["unit"]["state"] == "resolved"
    assert audit["all_scientifically_scoreable"] is True


def test_joint_argument_audit_rejects_cross_pairing() -> None:
    audit = audit_arguments(
        {"value": 4, "unit": "years"},
        "The first phase lasted 4 days and the second 7 years.",
    )
    assert audit["records"]["value"]["state"] == "ungrounded_pair"
    assert audit["records"]["unit"]["state"] == "ungrounded_pair"
    assert audit["blocking"] is True
