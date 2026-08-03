"""Persistent and customizable dashboard-layout preferences."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import cast


class DashboardSection(StrEnum):
    """Identify one customizable dashboard section."""

    ANALYTICS = "analytics"
    ACTIVITY = "activity"
    GALLERY = "gallery"
    MEMORIES = "memories"

    @property
    def display_name(self) -> str:
        """Return the French interface label."""
        labels = {
            DashboardSection.ANALYTICS: (
                "Analyses et hypothèses"
            ),
            DashboardSection.ACTIVITY: (
                "Activité récente"
            ),
            DashboardSection.GALLERY: (
                "Galerie du projet"
            ),
            DashboardSection.MEMORIES: (
                "Mémoires scientifiques"
            ),
        }

        return labels[self]


class DashboardLayoutPreset(StrEnum):
    """Identify one ready-to-use dashboard profile."""

    COMPLETE = "complete"
    ANALYTICS_FIRST = "analytics_first"
    MEDIA_REVIEW = "media_review"
    FOCUS = "focus"

    @property
    def display_name(self) -> str:
        """Return the French profile label."""
        labels = {
            DashboardLayoutPreset.COMPLETE: (
                "Vue complète"
            ),
            DashboardLayoutPreset.ANALYTICS_FIRST: (
                "Analyse prioritaire"
            ),
            DashboardLayoutPreset.MEDIA_REVIEW: (
                "Revue visuelle"
            ),
            DashboardLayoutPreset.FOCUS: (
                "Concentration"
            ),
        }

        return labels[self]


DEFAULT_DASHBOARD_ORDER: tuple[
    DashboardSection,
    ...,
] = (
    DashboardSection.ANALYTICS,
    DashboardSection.ACTIVITY,
    DashboardSection.GALLERY,
    DashboardSection.MEMORIES,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardLayoutPreferences:
    """Describe section order and visibility."""

    order: tuple[DashboardSection, ...] = (
        DEFAULT_DASHBOARD_ORDER
    )

    hidden_sections: frozenset[DashboardSection] = (
        field(default_factory=frozenset)
    )

    def __post_init__(self) -> None:
        """Validate one complete dashboard layout."""
        order = tuple(self.order)

        hidden_sections = frozenset(
            self.hidden_sections
        )

        expected_sections = set(
            DashboardSection
        )

        if len(order) != len(set(order)):
            raise ValueError(
                "Dashboard sections cannot be duplicated."
            )

        if set(order) != expected_sections:
            raise ValueError(
                "Dashboard layout must contain every "
                "known section exactly once."
            )

        if not hidden_sections.issubset(
            expected_sections
        ):
            raise ValueError(
                "Hidden dashboard sections are invalid."
            )

        object.__setattr__(
            self,
            "order",
            order,
        )

        object.__setattr__(
            self,
            "hidden_sections",
            hidden_sections,
        )

    @property
    def visible_sections(
        self,
    ) -> tuple[DashboardSection, ...]:
        """Return ordered sections that remain visible."""
        return tuple(
            section
            for section in self.order
            if section not in self.hidden_sections
        )

    def move(
        self,
        section: DashboardSection,
        offset: int,
    ) -> DashboardLayoutPreferences:
        """Move one section by a relative offset."""
        current_index = self.order.index(
            section
        )

        return self.move_to(
            section,
            current_index + offset,
        )

    def move_to(
        self,
        section: DashboardSection,
        index: int,
    ) -> DashboardLayoutPreferences:
        """Move one section to an absolute position."""
        current_index = self.order.index(
            section
        )

        target_index = max(
            0,
            min(
                len(self.order) - 1,
                index,
            ),
        )

        if target_index == current_index:
            return self

        mutable_order = list(
            self.order
        )

        moved_section = mutable_order.pop(
            current_index
        )

        mutable_order.insert(
            target_index,
            moved_section,
        )

        return DashboardLayoutPreferences(
            order=tuple(mutable_order),
            hidden_sections=self.hidden_sections,
        )

    def with_visibility(
        self,
        section: DashboardSection,
        *,
        visible: bool,
    ) -> DashboardLayoutPreferences:
        """Return preferences with explicit visibility."""
        hidden_sections = set(
            self.hidden_sections
        )

        if visible:
            hidden_sections.discard(
                section
            )
        else:
            hidden_sections.add(
                section
            )

        updated_hidden_sections = frozenset(
            hidden_sections
        )

        if (
            updated_hidden_sections
            == self.hidden_sections
        ):
            return self

        return DashboardLayoutPreferences(
            order=self.order,
            hidden_sections=updated_hidden_sections,
        )

    def toggle_visibility(
        self,
        section: DashboardSection,
    ) -> DashboardLayoutPreferences:
        """Toggle visibility for one section."""
        return self.with_visibility(
            section,
            visible=(
                section
                in self.hidden_sections
            ),
        )


def dashboard_layout_for_preset(
    preset: DashboardLayoutPreset,
) -> DashboardLayoutPreferences:
    """Build preferences for one predefined profile."""
    profiles = {
        DashboardLayoutPreset.COMPLETE: (
            DashboardLayoutPreferences()
        ),
        DashboardLayoutPreset.ANALYTICS_FIRST: (
            DashboardLayoutPreferences(
                order=(
                    DashboardSection.ANALYTICS,
                    DashboardSection.MEMORIES,
                    DashboardSection.ACTIVITY,
                    DashboardSection.GALLERY,
                )
            )
        ),
        DashboardLayoutPreset.MEDIA_REVIEW: (
            DashboardLayoutPreferences(
                order=(
                    DashboardSection.GALLERY,
                    DashboardSection.ACTIVITY,
                    DashboardSection.ANALYTICS,
                    DashboardSection.MEMORIES,
                )
            )
        ),
        DashboardLayoutPreset.FOCUS: (
            DashboardLayoutPreferences(
                order=(
                    DashboardSection.ANALYTICS,
                    DashboardSection.ACTIVITY,
                    DashboardSection.MEMORIES,
                    DashboardSection.GALLERY,
                ),
                hidden_sections=frozenset(
                    {
                        DashboardSection.MEMORIES,
                        DashboardSection.GALLERY,
                    }
                ),
            )
        ),
    }

    return profiles[preset]


def identify_dashboard_layout_preset(
    preferences: DashboardLayoutPreferences,
) -> DashboardLayoutPreset | None:
    """Return the preset matching some preferences."""
    for preset in DashboardLayoutPreset:
        if (
            dashboard_layout_for_preset(
                preset
            )
            == preferences
        ):
            return preset

    return None


def dashboard_layout_to_dict(
    preferences: DashboardLayoutPreferences,
) -> dict[str, object]:
    """Serialize dashboard preferences."""
    return {
        "version": 1,
        "order": [
            section.value
            for section in preferences.order
        ],
        "hidden_sections": [
            section.value
            for section in preferences.order
            if (
                section
                in preferences.hidden_sections
            )
        ],
    }


def dashboard_layout_from_dict(
    payload: Mapping[str, object],
) -> DashboardLayoutPreferences:
    """Deserialize dashboard preferences."""
    version = payload.get("version")

    if version != 1:
        raise ValueError(
            "Unsupported dashboard-layout version."
        )

    raw_order = payload.get("order")

    raw_hidden = payload.get(
        "hidden_sections",
        [],
    )

    if not isinstance(raw_order, list):
        raise TypeError(
            "Dashboard layout order must be a list."
        )

    if not isinstance(raw_hidden, list):
        raise TypeError(
            "Hidden dashboard sections must be a list."
        )

    if not all(
        isinstance(value, str)
        for value in raw_order
    ):
        raise TypeError(
            "Dashboard section identifiers must be strings."
        )

    if not all(
        isinstance(value, str)
        for value in raw_hidden
    ):
        raise TypeError(
            "Hidden section identifiers must be strings."
        )

    order_values = cast(
        list[str],
        raw_order,
    )

    hidden_values = cast(
        list[str],
        raw_hidden,
    )

    try:
        order = tuple(
            DashboardSection(value)
            for value in order_values
        )

        hidden_sections = frozenset(
            DashboardSection(value)
            for value in hidden_values
        )

    except ValueError as error:
        raise ValueError(
            "Unknown dashboard section identifier."
        ) from error

    return DashboardLayoutPreferences(
        order=order,
        hidden_sections=hidden_sections,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardLayoutStore:
    """Persist dashboard preferences as JSON."""

    path: Path

    def __post_init__(self) -> None:
        """Normalize the storage path."""
        object.__setattr__(
            self,
            "path",
            Path(self.path),
        )

    @property
    def invalid_backup_path(self) -> Path:
        """Return the path used for invalid JSON backups."""
        suffix = self.path.suffix or ".json"

        return self.path.with_name(
            f"{self.path.stem}.invalid{suffix}"
        )

    def load(
        self,
    ) -> DashboardLayoutPreferences:
        """Load preferences or return defaults when absent."""
        if not self.path.exists():
            return DashboardLayoutPreferences()

        if not self.path.is_file():
            raise ValueError(
                "Dashboard-layout path is not a file."
            )

        try:
            parsed: object = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "Dashboard-layout JSON is malformed."
            ) from error

        if not isinstance(parsed, dict):
            raise TypeError(
                "Dashboard-layout JSON must contain an object."
            )

        payload = cast(
            Mapping[str, object],
            parsed,
        )

        return dashboard_layout_from_dict(
            payload
        )

    def load_or_default(
        self,
        *,
        backup_invalid: bool = True,
    ) -> DashboardLayoutPreferences:
        """Load preferences and recover safely from invalid data."""
        try:
            return self.load()

        except (OSError, TypeError, ValueError):
            if (
                backup_invalid
                and self.path.is_file()
            ):
                self._backup_invalid_file()

            return DashboardLayoutPreferences()

    def save(
        self,
        preferences: DashboardLayoutPreferences,
    ) -> None:
        """Persist preferences atomically."""
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self.path.with_name(
            f"{self.path.name}.tmp"
        )

        serialized = json.dumps(
            dashboard_layout_to_dict(
                preferences
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

        temporary_path.write_text(
            serialized + "\n",
            encoding="utf-8",
        )

        temporary_path.replace(
            self.path
        )

    def _backup_invalid_file(self) -> None:
        """Move an invalid layout file aside when possible."""
        backup_path = self.invalid_backup_path

        try:
            if backup_path.exists():
                backup_path.unlink()

            self.path.replace(
                backup_path
            )

        except OSError:
            return
