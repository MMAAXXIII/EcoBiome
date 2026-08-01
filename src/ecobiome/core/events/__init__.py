"""Event-driven communication primitives for EcoBiome."""

from ecobiome.core.events.event import Event, WaterRemovedEvent
from ecobiome.core.events.event_bus import (
    EventBus,
    EventHandler,
    Subscription,
)
from ecobiome.core.events.event_factory import (
    EventDecoder,
    EventPayload,
    EventRecord,
    EventTypeRegistry,
    create_default_event_registry,
    decode_water_removed_event,
)
from ecobiome.core.events.event_store import (
    EventStore,
    InMemoryEventStore,
)
from ecobiome.core.events.serializer import (
    JsonValue,
    event_to_json,
    event_to_record,
    event_type_name,
)

__all__ = [
    "Event",
    "EventBus",
    "EventDecoder",
    "EventHandler",
    "EventPayload",
    "EventRecord",
    "EventStore",
    "EventTypeRegistry",
    "InMemoryEventStore",
    "JsonValue",
    "Subscription",
    "WaterRemovedEvent",
    "create_default_event_registry",
    "decode_water_removed_event",
    "event_to_json",
    "event_to_record",
    "event_type_name",
]
