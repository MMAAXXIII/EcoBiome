"""Shared spacing and typography tokens for the desktop interface."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class SpacingScale:
    """Resolved six-step spacing rhythm for one display scale."""

    micro: int
    compact: int
    gutter: int
    padding: int
    group: int
    major: int


class TypographyRole(StrEnum):
    """Semantic font roles used across desktop dashboard modules."""

    PROJECT_TITLE = "project-title"
    SECTION_TITLE = "section-title"
    KPI_VALUE = "kpi-value"
    PRIMARY_LABEL = "primary-label"
    BODY = "body"
    METADATA = "metadata"


def spacing_scale(
    visual_scale: float = 1.0,
) -> SpacingScale:
    """Return the shared 4/8/12/16/24/32 pixel spacing rhythm."""
    if visual_scale <= 0:
        raise ValueError(
            "Spacing visual scale must be positive."
        )

    def scaled(value: int) -> int:
        return max(1, round(value * visual_scale))

    return SpacingScale(
        micro=scaled(4),
        compact=scaled(8),
        gutter=scaled(12),
        padding=scaled(16),
        group=scaled(24),
        major=scaled(32),
    )


def typography_font(
    role: TypographyRole | str,
    *,
    visual_scale: float = 1.0,
) -> tuple[str, int]:
    """Resolve one semantic desktop font without global Tk scaling."""
    if visual_scale <= 0:
        raise ValueError(
            "Typography visual scale must be positive."
        )

    resolved_role = TypographyRole(role)
    specifications = {
        TypographyRole.PROJECT_TITLE: (
            "Segoe UI Semibold",
            25,
        ),
        # Slightly larger section titles for clearer hierarchy
        TypographyRole.SECTION_TITLE: (
            "Segoe UI Semibold",
            15,
        ),
        # Emphasize KPI values a bit more for readability on dashboards
        TypographyRole.KPI_VALUE: (
            "Segoe UI Semibold",
            26,
        ),
        TypographyRole.PRIMARY_LABEL: (
            "Segoe UI Semibold",
            11,
        ),
        TypographyRole.BODY: (
            "Segoe UI",
            9,
        ),
        TypographyRole.METADATA: (
            "Segoe UI",
            8,
        ),
    }
    family, size = specifications[resolved_role]

    return (
        family,
        max(1, round(size * visual_scale)),
    )


def surface_geometry(
    visual_scale: float = 1.0,
) -> dict[str, tuple[int, int]]:
    """Return canonical (unscaled) surface geometry (radius, shadow_offset).

    The visual scaling is applied by the consumer (surfaces.surface_profile),
    so keep these tokens as the single source of truth for base values.
    """
    # Keep the base tokens unscaled; surfaces.surface_profile applies visual_scale
    return {
        "panel": (14, 3),
        "analytic": (12, 2),
        "compact": (9, 1),
    }
