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

__all__ = [
    "Event",
    "EventBus",
    "EventHandler",
    "EventStore",
    "InMemoryEventStore",
    "Subscription",
    "WaterRemovedEvent",
]
