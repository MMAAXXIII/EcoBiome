"""Tests for persistent JSON Lines event storage."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from ecobiome.core.events import (
    JsonLinesEventStore,
    WaterRemovedEvent,
    create_default_event_registry,
)


def make_event(
    *,
    event_id: str,
    occurred_at: datetime,
    removed_height_m: float,
    remaining_volume_liters: float,
) -> WaterRemovedEvent:
    """Create one deterministic event."""
    return WaterRemovedEvent(
        event_id=UUID(event_id),
        occurred_at=occurred_at,
        water_body_name="Aquarium principal",
        removed_height_m=removed_height_m,
        removed_volume_liters=(
            removed_height_m * 600.0
        ),
        remaining_volume_liters=remaining_volume_liters,
        cause="user_removal",
    )


def make_store(path: Path) -> JsonLinesEventStore:
    """Create one JSONL store with the default registry."""
    return JsonLinesEventStore(
        path=path,
        registry=create_default_event_registry(),
    )


def test_append_and_reload_event(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    store = make_store(path)

    event = make_event(
        event_id="11111111-1111-1111-1111-111111111111",
        occurred_at=datetime(
            2026,
            8,
            1,
            8,
            tzinfo=UTC,
        ),
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )

    store.append(event)

    restored_store = make_store(path)

    assert restored_store.count == 1
    assert restored_store.load() == (event,)
    assert restored_store.contains(event.event_id) is True


def test_store_preserves_insertion_order(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events.jsonl"
    store = make_store(path)
    first_time = datetime(
        2026,
        8,
        1,
        8,
        tzinfo=UTC,
    )

    first = make_event(
        event_id="11111111-1111-1111-1111-111111111111",
        occurred_at=first_time,
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )
    second = make_event(
        event_id="22222222-2222-2222-2222-222222222222",
        occurred_at=first_time + timedelta(hours=1),
        removed_height_m=0.05,
        remaining_volume_liters=270.0,
    )

    store.append(first)
    store.append(second)

    assert store.load() == (first, second)


def test_duplicate_identifier_is_rejected(
    tmp_path: Path,
) -> None:
    store = make_store(tmp_path / "events.jsonl")

    event = make_event(
        event_id="11111111-1111-1111-1111-111111111111",
        occurred_at=datetime(
            2026,
            8,
            1,
            8,
            tzinfo=UTC,
        ),
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )

    store.append(event)

    with pytest.raises(ValueError, match="already stored"):
        store.append(event)

    assert store.count == 1


def test_missing_file_behaves_as_empty_store(
    tmp_path: Path,
) -> None:
    store = make_store(tmp_path / "missing.jsonl")

    assert store.load() == ()
    assert store.count == 0


def test_clear_removes_all_events(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    store = make_store(path)

    event = make_event(
        event_id="11111111-1111-1111-1111-111111111111",
        occurred_at=datetime(
            2026,
            8,
            1,
            8,
            tzinfo=UTC,
        ),
        removed_height_m=0.10,
        remaining_volume_liters=300.0,
    )

    store.append(event)
    store.clear()

    assert path.is_file()
    assert store.load() == ()
    assert store.count == 0


def test_invalid_line_reports_its_number(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text(
        "\n{invalid json}\n",
        encoding="utf-8",
    )

    store = make_store(path)

    with pytest.raises(
        ValueError,
        match="line 2",
    ):
        store.load()
