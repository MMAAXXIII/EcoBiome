"""Serialization helpers for public diagnostic results."""

from __future__ import annotations

from typing import Any

from ecobiome.reasoning.results.diagnostic_result import (
    DiagnosticResult,
)


def diagnostic_result_to_dict(
    result: DiagnosticResult,
) -> dict[str, Any]:
    """Convert a public diagnostic result to primitive data."""
    best_experiment = result.best_experiment

    return {
        "session_id": str(result.session_id),
        "profile_id": result.profile_id,
        "ecobiome_version": result.ecobiome_version,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
        "duration_seconds": result.duration_seconds,
        "status": result.status.value,
        "succeeded": result.succeeded,
        "has_inconsistency": result.has_inconsistency,
        "counts": {
            "observations": result.observation_count,
            "usable_observations": (
                result.usable_observation_count
            ),
            "rejected_observations": (
                result.rejected_observation_count
            ),
            "proposals": result.proposal_count,
            "experiments": result.experiment_count,
        },
        "warnings": list(result.warnings),
        "best_experiment": (
            {
                "identifier": best_experiment.identifier,
            }
            if best_experiment is not None
            else None
        ),
        "timeline": [
            {
                "sequence": entry.sequence,
                "stage": entry.stage.value,
                "title": entry.title,
                "description": entry.description,
                "occurred_at": (
                    entry.occurred_at.isoformat()
                    if entry.occurred_at is not None
                    else None
                ),
                "item_count": entry.item_count,
            }
            for entry in result.timeline
        ],
    }
