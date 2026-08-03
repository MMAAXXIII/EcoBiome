"""Reusable Canvas-based charts for the EcoBiome desktop UI."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ProbabilityBar:
    """Describe one hypothesis probability row."""

    identifier: str
    label: str
    probability: int
    accent: str

    def __post_init__(self) -> None:
        """Validate one probability row."""
        if not self.identifier.strip():
            raise ValueError(
                "Probability-bar identifier cannot be empty."
            )

        if not self.label.strip():
            raise ValueError(
                "Probability-bar label cannot be empty."
            )

        if not 0 <= self.probability <= 100:
            raise ValueError(
                "Probability must be between zero and one hundred."
            )


def draw_progress_bar(
    canvas: tk.Canvas,
    *,
    width: int,
    height: int,
    ratio: float,
    background: str,
    foreground: str,
) -> None:
    """Draw a horizontal progress bar."""
    canvas.delete("all")

    normalized_ratio = max(
        0.0,
        min(1.0, ratio),
    )

    canvas.create_rectangle(
        0,
        0,
        width,
        height,
        fill=background,
        outline="",
    )

    canvas.create_rectangle(
        0,
        0,
        width * normalized_ratio,
        height,
        fill=foreground,
        outline="",
    )


def draw_probability_bar(
    canvas: tk.Canvas,
    *,
    width: int,
    probability: int,
    background: str,
    foreground: str,
) -> None:
    """Draw one hypothesis probability bar."""
    if not 0 <= probability <= 100:
        raise ValueError(
            "Probability must be between zero and one hundred."
        )

    draw_progress_bar(
        canvas,
        width=width,
        height=6,
        ratio=probability / 100,
        background=background,
        foreground=foreground,
    )


def draw_quality_donut(
    canvas: tk.Canvas,
    *,
    width: int,
    height: int,
    score: int | None,
    background: str,
    track: str,
    high_quality: str,
    medium_quality: str,
    low_quality: str,
    rejected: str,
    text_color: str,
    secondary_text_color: str,
) -> None:
    """Draw a segmented observation-quality donut."""
    canvas.delete("all")
    canvas.configure(background=background)

    size = min(width, height) - 20

    if size <= 20:
        return

    left = (width - size) / 2
    top = (height - size) / 2
    right = left + size
    bottom = top + size
    line_width = max(12, round(size * 0.12))

    canvas.create_oval(
        left,
        top,
        right,
        bottom,
        outline=track,
        width=line_width,
    )

    effective_score = score if score is not None else 0

    high_share = max(0, min(effective_score, 66))
    remaining = max(0, effective_score - high_share)
    medium_share = min(remaining, 24)
    remaining -= medium_share
    low_share = min(remaining, 8)
    rejected_share = max(
        0,
        min(100 - effective_score, 12),
    )

    segments = (
        (high_share, high_quality),
        (medium_share, medium_quality),
        (low_share, low_quality),
        (rejected_share, rejected),
    )

    start = 90.0

    for share, color in segments:
        if share <= 0:
            continue

        extent = -(share / 100) * 360

        canvas.create_arc(
            left,
            top,
            right,
            bottom,
            start=start,
            extent=extent,
            style=tk.ARC,
            outline=color,
            width=line_width,
        )

        start += extent

    score_text = (
        f"{effective_score}%"
        if score is not None
        else "—"
    )

    canvas.create_text(
        width / 2,
        height / 2 - 7,
        text=score_text,
        fill=text_color,
        font=("Segoe UI Semibold", 24),
    )

    canvas.create_text(
        width / 2,
        height / 2 + 22,
        text="Qualité globale",
        fill=secondary_text_color,
        font=("Segoe UI", 9),
    )


def draw_line_chart(
    canvas: tk.Canvas,
    *,
    width: int,
    height: int,
    values: Sequence[int],
    background: str,
    grid: str,
    line: str,
    point: str,
    text_color: str,
) -> None:
    """Draw one compact evolution line chart."""
    canvas.delete("all")
    canvas.configure(background=background)

    if width < 80 or height < 60:
        return

    left = 34
    right = width - 10
    top = 12
    bottom = height - 24

    for percentage in (0, 50, 100):
        y = bottom - (
            percentage / 100
        ) * (bottom - top)

        canvas.create_line(
            left,
            y,
            right,
            y,
            fill=grid,
            dash=(2, 4),
        )

        canvas.create_text(
            left - 6,
            y,
            text=f"{percentage}%",
            anchor="e",
            fill=text_color,
            font=("Segoe UI", 7),
        )

    if not values:
        return

    normalized = [
        max(0, min(100, value))
        for value in values
    ]

    if len(normalized) == 1:
        x_positions = [(left + right) / 2]
    else:
        step = (right - left) / (
            len(normalized) - 1
        )

        x_positions = [
            left + index * step
            for index in range(len(normalized))
        ]

    points: list[float] = []

    for x, value in zip(
        x_positions,
        normalized,
        strict=True,
    ):
        y = bottom - (
            value / 100
        ) * (bottom - top)

        points.extend((x, y))

    if len(points) >= 4:
        canvas.create_line(
            *points,
            fill=line,
            width=2,
            smooth=True,
        )

    for index in range(0, len(points), 2):
        canvas.create_oval(
            points[index] - 2,
            points[index + 1] - 2,
            points[index] + 2,
            points[index + 1] + 2,
            fill=point,
            outline="",
        )

    canvas.create_text(
        left,
        height - 9,
        text="13:30",
        anchor="w",
        fill=text_color,
        font=("Segoe UI", 7),
    )

    canvas.create_text(
        right,
        height - 9,
        text="14:30",
        anchor="e",
        fill=text_color,
        font=("Segoe UI", 7),
    )
