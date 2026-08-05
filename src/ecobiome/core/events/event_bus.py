"""Synchronous in-process event bus."""

from collections.abc import Callable
from dataclasses import dataclass

from ecobiome.core.events.event import Event

type EventHandler = Callable[[Event], None]


@dataclass(frozen=True, slots=True)
class Subscription:
    """Identify one event-handler registration."""

    event_type: type[Event]
    handler: EventHandler


class EventBus:
    """Publish events to independent synchronous subscribers."""

    def __init__(self) -> None:
        self._subscriptions: list[Subscription] = []

    def subscribe(
        self,
        event_type: type[Event],
        handler: EventHandler,
    ) -> Subscription:
        """Register a handler for an event class."""
        subscription = Subscription(
            event_type=event_type,
            handler=handler,
        )

        if subscription not in self._subscriptions:
            self._subscriptions.append(subscription)

        return subscription

    def unsubscribe(self, subscription: Subscription) -> bool:
        """Remove a subscription and report whether it existed."""
        try:
            self._subscriptions.remove(subscription)
        except ValueError:
            return False

        return True

    def publish(self, event: Event) -> int:
        """Synchronously dispatch an event to matching handlers."""
        matching_subscriptions = tuple(
            subscription
            for subscription in self._subscriptions
            if isinstance(event, subscription.event_type)
        )

        for subscription in matching_subscriptions:
            subscription.handler(event)

        return len(matching_subscriptions)

    def subscriber_count(
        self,
        event_type: type[Event] | None = None,
    ) -> int:
        """Count every subscriber or subscribers of one event type."""
        if event_type is None:
            return len(self._subscriptions)

        return sum(
            subscription.event_type is event_type
            for subscription in self._subscriptions
        )

    def clear(self) -> None:
        """Remove every registered subscription."""
        self._subscriptions.clear()
