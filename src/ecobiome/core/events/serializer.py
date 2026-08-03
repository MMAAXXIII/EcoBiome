"""Generic serialization of EcoBiome events."""

import json
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from ecobiome.core.events.event import Event

type JsonValue = (
    str
    | int
    | float
    | bool
    | None
    | list["JsonValue"]
    | dict[str, "JsonValue"]
)


def _to_json_value(value: object) -> JsonValue:
    """Convert one supported Python value into a JSON-compatible value."""
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Enum):
        return _to_json_value(value.value)

    if isinstance(value, tuple | list):
        return [
            _to_json_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        converted: dict[str, JsonValue] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    "Only string dictionary keys can be serialized."
                )

            converted[key] = _to_json_value(item)

        return converted

    raise TypeError(
        f"Unsupported event value type: {type(value).__name__}."
    )


def event_type_name(event: Event) -> str:
    """Return the stable fully qualified type name of an event."""
    event_class = type(event)

    return (
        f"{event_class.__module__}."
        f"{event_class.__qualname__}"
    )


def event_to_record(event: Event) -> dict[str, JsonValue]:
    """Convert one dataclass event into a versioned record."""
    if not is_dataclass(event):
        raise TypeError("EcoBiome events must be dataclass instances.")

    payload: dict[str, JsonValue] = {}

    for event_field in fields(event):
        payload[event_field.name] = _to_json_value(
            getattr(event, event_field.name)
        )

    return {
        "schema_version": "0.1",
        "event_type": event_type_name(event),
        "payload": payload,
    }


def event_to_json(
    event: Event,
    *,
    indent: int | None = None,
) -> str:
    """Serialize one event as UTF-8-compatible JSON text."""
    return json.dumps(
        event_to_record(event),
        ensure_ascii=False,
        indent=indent,
        sort_keys=True,
    )
