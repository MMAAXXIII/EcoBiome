"""Tests for EcoBiome architecture diagnostics."""

from ecobiome.reasoning.architecture_doctor import (
    DiagnosticStatus,
    EcoBiomeDoctor,
)
from ecobiome.reasoning.component_registry import (
    ReasoningComponentRegistry,
)
from ecobiome.reasoning.profiles import (
    build_camera_lux_registry,
)


def test_camera_lux_profile_registers_four_components() -> None:
    registry = build_camera_lux_registry()
    summary = registry.summary

    assert summary.quality_rule_count == 1
    assert summary.consistency_rule_count == 1
    assert summary.hypothesis_rule_count == 1
    assert summary.experiment_rule_count == 1
    assert summary.total_count == 4


def test_doctor_accepts_complete_camera_lux_profile() -> None:
    report = EcoBiomeDoctor(
        build_camera_lux_registry()
    ).inspect()

    assert report.succeeded is True
    assert report.failed_count == 0
    assert report.passed_count == len(report.diagnostics)
    assert report.component_summary.total_count == 4
    assert report.failure_messages == ()


def test_doctor_accepts_empty_registry() -> None:
    report = EcoBiomeDoctor(
        ReasoningComponentRegistry()
    ).inspect()

    assert report.succeeded is True
    assert report.component_summary.total_count == 0


def test_every_diagnostic_has_traceable_identifier() -> None:
    report = EcoBiomeDoctor(
        build_camera_lux_registry()
    ).inspect()

    assert all(
        diagnostic.identifier.startswith("architecture.")
        for diagnostic in report.diagnostics
    )

    assert all(
        "." in diagnostic.identifier
        for diagnostic in report.diagnostics
    )


def test_successful_diagnostics_have_passed_status() -> None:
    report = EcoBiomeDoctor(
        build_camera_lux_registry()
    ).inspect()

    assert all(
        diagnostic.status is DiagnosticStatus.PASSED
        for diagnostic in report.diagnostics
    )
