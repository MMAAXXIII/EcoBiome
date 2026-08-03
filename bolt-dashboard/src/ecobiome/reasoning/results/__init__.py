"""Public diagnostic-result API for EcoBiome interfaces."""

from ecobiome.reasoning.results.diagnostic_result import (
    DiagnosticResult,
)
from ecobiome.reasoning.results.serializers import (
    diagnostic_result_to_dict,
)
from ecobiome.reasoning.results.summary import (
    DiagnosticStatus,
    DiagnosticSummary,
)
from ecobiome.reasoning.results.timeline import (
    DiagnosticTimelineEntry,
    DiagnosticTimelineStage,
    build_diagnostic_timeline,
)

__all__ = [
    "DiagnosticResult",
    "DiagnosticStatus",
    "DiagnosticSummary",
    "DiagnosticTimelineEntry",
    "DiagnosticTimelineStage",
    "build_diagnostic_timeline",
    "diagnostic_result_to_dict",
]
