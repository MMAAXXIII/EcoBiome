"""Primitive serialization for project-dashboard snapshots."""

from typing import Any

from ecobiome.dashboard.models import (
    ProjectDashboardSnapshot,
)


def project_dashboard_to_dict(
    dashboard: ProjectDashboardSnapshot,
) -> dict[str, Any]:
    """Convert one dashboard snapshot to primitive data."""
    return {
        "project": {
            "project_id": str(dashboard.project_id),
            "name": dashboard.project_name,
            "project_type": dashboard.project_type.value,
            "description": dashboard.description,
            "updated_at": dashboard.updated_at.isoformat(),
            "tags": list(dashboard.tags),
        },
        "summary": {
            "journal_event_count": (
                dashboard.journal_event_count
            ),
            "media_file_count": dashboard.media_file_count,
            "diagnostic_count": dashboard.diagnostic_count,
            "learning_count": dashboard.learning_count,
            "biological_event_count": (
                dashboard.biological_event_count
            ),
            "has_activity": dashboard.has_activity,
            "has_media": dashboard.has_media,
        },
        "event_counts": [
            {
                "event_type": counter.event_type.value,
                "count": counter.count,
            }
            for counter in dashboard.event_counts
        ],
        "latest_activity": [
            {
                "event_id": str(item.event_id),
                "event_type": item.event_type.value,
                "title": item.title,
                "description": item.description,
                "occurred_at": item.occurred_at.isoformat(),
                "tags": list(item.tags),
            }
            for item in dashboard.latest_activity
        ],
    }
