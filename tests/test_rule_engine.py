"""Tests for the extensible scientific rule framework."""

from uuid import UUID

import pytest

from ecobiome.core.observation import (
    AcquisitionMethod,
    Observation,
)
from ecobiome.knowledge.variable import ScientificVariable
from ecobiome.reasoning import (
    Evidence,
    EvidenceRelation,
    RuleDomain,
    RuleEngine,
    ScientificRule,
)

HYPOTHESIS_ID = UUID(
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
)


def make_observation() -> Observation:
    """Create one generic quantitative observation."""
    variable = ScientificVariable(
        identifier="chemistry.nitrite_concentration",
        name="Nitrite concentration",
        description="Concentration of nitrite in water.",
        unit="milligram / liter",
        display_unit="mg/L",
        category="chemistry",
    )

    return Observation(
        source="test-sensor",
        variable=variable,
        value=0.5,
        acquisition_method=AcquisitionMethod.SENSOR,
        confidence=0.95,
    )


class EvidenceRule(ScientificRule):
    """Generate one evidence record."""

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        return (
            Evidence(
                observation_id=observation.observation_id,
                hypothesis_id=HYPOTHESIS_ID,
                relation=EvidenceRelation.SUPPORTS,
                weight=0.50,
                explanation="The observation supports the hypothesis.",
                source_rule=self.identifier,
            ),
        )


class EmptyRule(ScientificRule):
    """Generate no evidence."""

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        return ()


class FailingRule(ScientificRule):
    """Raise an error to verify engine isolation."""

    def evaluate(
        self,
        observation: Observation,
    ) -> tuple[Evidence, ...]:
        raise RuntimeError("Simulated rule failure.")


def make_rule(
    rule_type: type[ScientificRule] = EvidenceRule,
    *,
    identifier: str = "chemistry.test_rule",
    priority: int = 0,
    enabled: bool = True,
    domain: RuleDomain = RuleDomain.CHEMISTRY,
) -> ScientificRule:
    """Create one test rule."""
    return rule_type(
        identifier=identifier,
        name="Test rule",
        description="Rule used by the test suite.",
        domain=domain,
        priority=priority,
        enabled=enabled,
    )


def test_empty_engine_generates_empty_report() -> None:
    report = RuleEngine().evaluate(make_observation())

    assert report.executed_rule_count == 0
    assert report.skipped_rule_count == 0
    assert report.evidence_count == 0
    assert report.succeeded is True


def test_rule_generates_evidence() -> None:
    engine = RuleEngine([make_rule()])

    report = engine.evaluate(make_observation())

    assert report.executed_rule_ids == (
        "chemistry.test_rule",
    )
    assert report.evidence_count == 1
    assert report.evidence[0].source_rule == (
        "chemistry.test_rule"
    )


def test_multiple_rules_preserve_priority_order() -> None:
    low_priority = make_rule(
        identifier="chemistry.low_priority",
        priority=10,
    )
    high_priority = make_rule(
        identifier="hardware.high_priority",
        priority=100,
        domain=RuleDomain.HARDWARE,
    )

    report = RuleEngine(
        [low_priority, high_priority]
    ).evaluate(make_observation())

    assert report.executed_rule_ids == (
        "hardware.high_priority",
        "chemistry.low_priority",
    )


def test_disabled_rule_is_skipped() -> None:
    rule = make_rule(
        identifier="chemistry.disabled",
        enabled=False,
    )

    report = RuleEngine([rule]).evaluate(make_observation())

    assert report.executed_rule_count == 0
    assert report.skipped_rule_ids == (
        "chemistry.disabled",
    )


def test_domain_filter_skips_unselected_rules() -> None:
    chemistry_rule = make_rule(
        identifier="chemistry.selected",
    )
    vision_rule = make_rule(
        identifier="vision.skipped",
        domain=RuleDomain.VISION,
    )

    engine = RuleEngine(
        [chemistry_rule, vision_rule],
        enabled_domains={RuleDomain.CHEMISTRY},
    )

    report = engine.evaluate(make_observation())

    assert report.executed_rule_ids == (
        "chemistry.selected",
    )
    assert report.skipped_rule_ids == (
        "vision.skipped",
    )


def test_failed_rule_does_not_stop_following_rules() -> None:
    failing_rule = make_rule(
        FailingRule,
        identifier="hardware.failure",
        priority=100,
        domain=RuleDomain.HARDWARE,
    )
    successful_rule = make_rule(
        identifier="chemistry.success",
        priority=10,
    )

    report = RuleEngine(
        [successful_rule, failing_rule]
    ).evaluate(make_observation())

    assert report.executed_rule_count == 2
    assert report.failed_rule_count == 1
    assert report.evidence_count == 1
    assert report.succeeded is False

    failure = report.failures[0]

    assert failure.rule_identifier == "hardware.failure"
    assert failure.exception_type == "RuntimeError"
    assert failure.message == "Simulated rule failure."


def test_duplicate_rule_identifier_is_rejected() -> None:
    first = make_rule()
    second = make_rule()

    with pytest.raises(
        ValueError,
        match="Duplicate rule identifier",
    ):
        RuleEngine([first, second])


def test_rule_metadata_is_normalized() -> None:
    rule = EvidenceRule(
        identifier="  chemistry.test_rule  ",
        name="  Test rule  ",
        description="  Test description.  ",
        domain=RuleDomain.CHEMISTRY,
    )

    assert rule.identifier == "chemistry.test_rule"
    assert rule.name == "Test rule"
    assert rule.description == "Test description."


def test_rule_identifier_requires_domain_prefix() -> None:
    with pytest.raises(ValueError, match="domain prefix"):
        make_rule(identifier="invalid_rule")
