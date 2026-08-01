"""Event-driven communication primitives for EcoBiome."""

from ecobiome.core.events.event import Event, WaterRemovedEvent
from ecobiome.core.events.event_bus import (
    EventBus,
    EventHandler,
    Subscription,
)

__all__ = [
    "Event",
    "EventBus",
    "EventHandler",
    "Subscription",
    "WaterRemovedEvent",
]
