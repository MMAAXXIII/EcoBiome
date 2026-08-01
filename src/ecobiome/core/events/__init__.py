"""Event-driven communication primitives for EcoBiome."""

from ecobiome.core.events.event import Event, WaterRemovedEvent
from ecobiome.core.events.event_bus import (
    EventBus,
    EventHandler,
    Subscription,
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
    "EventHandler",
    "EventStore",
    "InMemoryEventStore",
    "JsonValue",
    "Subscription",
    "WaterRemovedEvent",
    "event_to_json",
    "event_to_record",
    "event_type_name",
]
