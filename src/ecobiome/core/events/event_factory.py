"""Secure reconstruction of explicitly authorized EcoBiome events."""

import json
from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from ecobiome.core.events.event import Event, WaterRemovedEvent
from ecobiome.core.events.serializer import JsonValue

type EventPayload = dict[str, JsonValue]
type EventRecord = dict[str, JsonValue]
type EventDecoder = Callable[[EventPayload], Event]


def event_type_name_from_class(
    event_type: type[Event],
) -> str:
    """Return the stable fully qualified name of an event class."""
    return (
        f"{event_type.__module__}."
        f"{event_type.__qualname__}"
    )


def _required_string(
    payload: EventPayload,
    field_name: str,
) -> str:
    """Read one required non-empty string."""
    value = payload.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise TypeError(
            f"Event field {field_name!r} must be a non-empty string."
        )

    return value.strip()


def _required_float(
    payload: EventPayload,
    field_name: str,
) -> float:
    """Read one required numerical value."""
    value = payload.get(field_name)

    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(
            f"Event field {field_name!r} must be numeric."
        )

    return float(value)


def _required_uuid(
    payload: EventPayload,
    field_name: str,
) -> UUID:
    """Read and validate one UUID."""
    raw_value = _required_string(payload, field_name)

    try:
        return UUID(raw_value)
    except ValueError as error:
        raise ValueError(
            f"Event field {field_name!r} must contain a valid UUID."
        ) from error


def _required_datetime(
    payload: EventPayload,
    field_name: str,
) -> datetime:
    """Read one timezone-aware ISO 8601 datetime."""
    raw_value = _required_string(payload, field_name)

    try:
        value = datetime.fromisoformat(raw_value)
    except ValueError as error:
        raise ValueError(
            f"Event field {field_name!r} must contain "
            "a valid ISO 8601 datetime."
        ) from error

    if value.tzinfo is None:
        raise ValueError(
            f"Event field {field_name!r} must include a timezone."
        )

    return value


def decode_water_removed_event(
    payload: EventPayload,
) -> WaterRemovedEvent:
    """Reconstruct one validated WaterRemovedEvent."""
    return WaterRemovedEvent(
        event_id=_required_uuid(payload, "event_id"),
        occurred_at=_required_datetime(payload, "occurred_at"),
        water_body_name=_required_string(
            payload,
            "water_body_name",
        ),
        removed_height_m=_required_float(
            payload,
            "removed_height_m",
        ),
        removed_volume_liters=_required_float(
            payload,
            "removed_volume_liters",
        ),
        remaining_volume_liters=_required_float(
            payload,
            "remaining_volume_liters",
        ),
        cause=_required_string(payload, "cause"),
    )


class EventTypeRegistry:
    """Map authorized event types to explicit safe decoders."""

    def __init__(self) -> None:
        self._decoders: dict[str, EventDecoder] = {}

    def register(
        self,
        event_type: type[Event],
        decoder: EventDecoder,
    ) -> str:
        """Authorize one event type and its decoder."""
        type_name = event_type_name_from_class(event_type)

        if type_name in self._decoders:
            raise ValueError(
                f"Event type {type_name!r} is already registered."
            )

        self._decoders[type_name] = decoder
        return type_name

    def create(self, record: EventRecord) -> Event:
        """Reconstruct one event from a validated record."""
        schema_version = record.get("schema_version")

        if schema_version != "0.1":
            raise ValueError(
                "Unsupported event schema version: "
                f"{schema_version!r}."
            )

        raw_event_type = record.get("event_type")

        if not isinstance(raw_event_type, str):
            raise TypeError(
                "Event record field 'event_type' must be a string."
            )

        raw_payload = record.get("payload")

        if not isinstance(raw_payload, dict):
            raise TypeError(
                "Event record field 'payload' must be an object."
            )

        decoder = self._decoders.get(raw_event_type)

        if decoder is None:
            raise ValueError(
                f"Unregistered event type: {raw_event_type!r}."
            )

        payload: EventPayload = {
            str(key): value
            for key, value in raw_payload.items()
        }

        return decoder(payload)

    def create_from_json(self, serialized: str) -> Event:
        """Reconstruct one authorized event from JSON text."""
        try:
            raw_record = json.loads(serialized)
        except json.JSONDecodeError as error:
            raise ValueError("Invalid event JSON.") from error

        if not isinstance(raw_record, dict):
            raise TypeError(
                "Serialized event must contain a JSON object."
            )

        record: EventRecord = {
            str(key): value
            for key, value in raw_record.items()
        }

        return self.create(record)

    def is_registered(
        self,
        event_type: type[Event],
    ) -> bool:
        """Return whether an event class is authorized."""
        return (
            event_type_name_from_class(event_type)
            in self._decoders
        )

    @property
    def registered_type_count(self) -> int:
        """Return the number of authorized event types."""
        return len(self._decoders)


def create_default_event_registry() -> EventTypeRegistry:
    """Create a registry containing current EcoBiome event types."""
    registry = EventTypeRegistry()

    registry.register(
        WaterRemovedEvent,
        decode_water_removed_event,
    )

    return registry
