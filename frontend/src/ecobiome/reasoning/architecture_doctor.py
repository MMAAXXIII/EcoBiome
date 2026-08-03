"""Runtime diagnostics for EcoBiome reasoning architecture."""

from dataclasses import dataclass
from enum import StrEnum
from importlib import import_module

from ecobiome.reasoning.component_registry import (
    ReasoningComponentRegistry,
    ReasoningComponentSummary,
)
from ecobiome.reasoning.pipeline_factory import (
    DiagnosticPipelineFactory,
)


class DiagnosticStatus(StrEnum):
    """Possible status of one architecture diagnostic."""

    PASSED = "passed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ArchitectureDiagnostic:
    """Describe one architecture verification."""

    identifier: str
    status: DiagnosticStatus
    message: str

    @property
    def succeeded(self) -> bool:
        """Return whether this diagnostic passed."""
        return self.status is DiagnosticStatus.PASSED


@dataclass(frozen=True, slots=True)
class ArchitectureDoctorReport:
    """Summarize all architecture diagnostics."""

    diagnostics: tuple[ArchitectureDiagnostic, ...]
    component_summary: ReasoningComponentSummary

    @property
    def succeeded(self) -> bool:
        """Return whether every diagnostic passed."""
        return all(
            diagnostic.succeeded
            for diagnostic in self.diagnostics
        )

    @property
    def passed_count(self) -> int:
        """Return the number of successful diagnostics."""
        return sum(
            diagnostic.succeeded
            for diagnostic in self.diagnostics
        )

    @property
    def failed_count(self) -> int:
        """Return the number of failed diagnostics."""
        return len(self.diagnostics) - self.passed_count

    @property
    def failure_messages(self) -> tuple[str, ...]:
        """Return messages from failed diagnostics."""
        return tuple(
            diagnostic.message
            for diagnostic in self.diagnostics
            if not diagnostic.succeeded
        )


class EcoBiomeDoctor:
    """Inspect reasoning architecture without running observations."""

    _CRITICAL_MODULES = (
        "ecobiome.core.observation",
        "ecobiome.contracts",
        "ecobiome.reasoning.component_registry",
        "ecobiome.reasoning.diagnostic_pipeline",
        "ecobiome.reasoning.pipeline_factory",
    )

    def __init__(
        self,
        registry: ReasoningComponentRegistry,
    ) -> None:
        self._registry = registry

    def inspect(self) -> ArchitectureDoctorReport:
        """Run all architecture diagnostics."""
        diagnostics = (
            *self._inspect_critical_imports(),
            self._inspect_pipeline_construction(),
            self._inspect_component_identifiers(),
        )

        return ArchitectureDoctorReport(
            diagnostics=diagnostics,
            component_summary=self._registry.summary,
        )

    def _inspect_critical_imports(
        self,
    ) -> tuple[ArchitectureDiagnostic, ...]:
        """Verify that critical modules can be imported."""
        diagnostics: list[ArchitectureDiagnostic] = []

        for module_name in self._CRITICAL_MODULES:
            identifier = (
                "architecture.import."
                f"{module_name.replace('.', '_')}"
            )

            try:
                import_module(module_name)
            except Exception as error:  # noqa: BLE001
                diagnostics.append(
                    ArchitectureDiagnostic(
                        identifier=identifier,
                        status=DiagnosticStatus.FAILED,
                        message=(
                            f"Unable to import {module_name!r}: "
                            f"{type(error).__name__}: {error}"
                        ),
                    )
                )
            else:
                diagnostics.append(
                    ArchitectureDiagnostic(
                        identifier=identifier,
                        status=DiagnosticStatus.PASSED,
                        message=(
                            f"Module {module_name!r} imported "
                            "successfully."
                        ),
                    )
                )

        return tuple(diagnostics)

    def _inspect_pipeline_construction(
        self,
    ) -> ArchitectureDiagnostic:
        """Verify that the registry can build a pipeline."""
        identifier = "architecture.pipeline.construction"

        try:
            DiagnosticPipelineFactory(
                self._registry
            ).build()
        except Exception as error:  # noqa: BLE001
            return ArchitectureDiagnostic(
                identifier=identifier,
                status=DiagnosticStatus.FAILED,
                message=(
                    "Diagnostic pipeline construction failed: "
                    f"{type(error).__name__}: {error}"
                ),
            )

        return ArchitectureDiagnostic(
            identifier=identifier,
            status=DiagnosticStatus.PASSED,
            message="Diagnostic pipeline construction succeeded.",
        )

    def _inspect_component_identifiers(
        self,
    ) -> ArchitectureDiagnostic:
        """Verify identifiers across every component family."""
        identifiers = (
            *(
                rule.identifier
                for rule in self._registry.quality_rules
            ),
            *(
                rule.identifier
                for rule in self._registry.consistency_rules
            ),
            *(
                rule.identifier
                for rule in self._registry.hypothesis_rules
            ),
            *(
                rule.identifier
                for rule in self._registry.experiment_rules
            ),
        )

        invalid = tuple(
            identifier
            for identifier in identifiers
            if not identifier.strip() or "." not in identifier
        )

        if invalid:
            return ArchitectureDiagnostic(
                identifier="architecture.components.identifiers",
                status=DiagnosticStatus.FAILED,
                message=(
                    "Invalid component identifiers: "
                    f"{', '.join(repr(item) for item in invalid)}."
                ),
            )

        return ArchitectureDiagnostic(
            identifier="architecture.components.identifiers",
            status=DiagnosticStatus.PASSED,
            message=(
                f"Validated {len(identifiers)} component identifiers."
            ),
        )
