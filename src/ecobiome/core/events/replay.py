"""Generic replay of stored EcoBiome events."""

from dataclasses import dataclass

from ecobiome.core.events.event_bus import EventBus
from ecobiome.core.events.event_store import EventStore


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Summary of one event-store replay."""

    loaded_event_count: int
    published_event_count: int
    delivery_count: int

    @property
    def event_without_subscriber_count(self) -> int:
        """Return how many events reached no subscriber."""
        return self.published_event_count - min(
            self.published_event_count,
            self.delivery_count,
        )


def replay_event_store(
    store: EventStore,
    bus: EventBus,
) -> ReplayResult:
    """Publish every stored event in storage order."""
    events = store.load()
    delivery_count = 0

    for event in events:
        delivery_count += bus.publish(event)

    return ReplayResult(
        loaded_event_count=len(events),
        published_event_count=len(events),
        delivery_count=delivery_count,
    )
