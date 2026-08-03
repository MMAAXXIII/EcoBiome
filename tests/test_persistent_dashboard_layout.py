"""Tests for persistent dashboard-layout preferences."""

import json
from pathlib import Path

import pytest

from ecobiome.ui.desktop import (
    DEFAULT_DASHBOARD_ORDER,
    DashboardLayoutPreferences,
    DashboardLayoutStore,
    DashboardSection,
    dashboard_layout_from_dict,
    dashboard_layout_to_dict,
)


def test_default_layout_order_is_stable() -> None:
    preferences = DashboardLayoutPreferences()

    assert preferences.order == (
        DEFAULT_DASHBOARD_ORDER
    )

    assert preferences.visible_sections == (
        DEFAULT_DASHBOARD_ORDER
    )


def test_visible_sections_exclude_hidden() -> None:
    preferences = DashboardLayoutPreferences(
        hidden_sections=frozenset(
            {
                DashboardSection.GALLERY,
                DashboardSection.MEMORIES,
            }
        )
    )

    assert preferences.visible_sections == (
        DashboardSection.ANALYTICS,
        DashboardSection.ACTIVITY,
    )


def test_section_can_move_up() -> None:
    preferences = DashboardLayoutPreferences()

    moved = preferences.move(
        DashboardSection.GALLERY,
        -1,
    )

    assert moved.order == (
        DashboardSection.ANALYTICS,
        DashboardSection.GALLERY,
        DashboardSection.ACTIVITY,
        DashboardSection.MEMORIES,
    )


def test_move_beyond_edge_is_noop() -> None:
    preferences = DashboardLayoutPreferences()

    moved = preferences.move(
        DashboardSection.ANALYTICS,
        -20,
    )

    assert moved is preferences


def test_section_visibility_can_toggle() -> None:
    preferences = DashboardLayoutPreferences()

    hidden = preferences.toggle_visibility(
        DashboardSection.ACTIVITY
    )

    restored = hidden.toggle_visibility(
        DashboardSection.ACTIVITY
    )

    assert (
        DashboardSection.ACTIVITY
        in hidden.hidden_sections
    )

    assert restored == preferences


def test_duplicate_sections_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be duplicated",
    ):
        DashboardLayoutPreferences(
            order=(
                DashboardSection.ANALYTICS,
                DashboardSection.ANALYTICS,
                DashboardSection.GALLERY,
                DashboardSection.MEMORIES,
            )
        )


def test_missing_section_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="every known section",
    ):
        DashboardLayoutPreferences(
            order=(
                DashboardSection.ANALYTICS,
                DashboardSection.ACTIVITY,
                DashboardSection.GALLERY,
            )
        )


def test_layout_survives_primitive_round_trip() -> None:
    original = DashboardLayoutPreferences(
        order=(
            DashboardSection.GALLERY,
            DashboardSection.ANALYTICS,
            DashboardSection.MEMORIES,
            DashboardSection.ACTIVITY,
        ),
        hidden_sections=frozenset(
            {
                DashboardSection.MEMORIES,
            }
        ),
    )

    payload = dashboard_layout_to_dict(
        original
    )

    restored = dashboard_layout_from_dict(
        payload
    )

    assert restored == original


def test_layout_store_persists_preferences(
    tmp_path: Path,
) -> None:
    store = DashboardLayoutStore(
        path=tmp_path / "dashboard-layout.json"
    )

    preferences = DashboardLayoutPreferences(
        order=(
            DashboardSection.ACTIVITY,
            DashboardSection.ANALYTICS,
            DashboardSection.GALLERY,
            DashboardSection.MEMORIES,
        ),
        hidden_sections=frozenset(
            {
                DashboardSection.GALLERY,
            }
        ),
    )

    store.save(preferences)

    assert store.load() == preferences

    payload = json.loads(
        store.path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["version"] == 1


def test_unknown_serialized_section_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown dashboard section",
    ):
        dashboard_layout_from_dict(
            {
                "version": 1,
                "order": [
                    "analytics",
                    "activity",
                    "gallery",
                    "unknown",
                ],
                "hidden_sections": [],
            }
        )
