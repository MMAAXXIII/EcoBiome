"""Global state of one simulated EcoBiome world."""

from ecobiome.core.events import Event, WaterRemovedEvent
from ecobiome.world.water_state import WaterBodyState


class WorldState:
    """Store and update the current state of simulated water bodies."""

    def __init__(self) -> None:
        self._water_bodies: dict[str, WaterBodyState] = {}
        self._processed_event_ids: set[str] = set()

    def add_water_body(self, water_body: WaterBodyState) -> None:
        """Register one water body under its unique name."""
        if water_body.name in self._water_bodies:
            raise ValueError(
                f"Water body {water_body.name!r} is already registered."
            )

        self._water_bodies[water_body.name] = water_body

    def get_water_body(self, name: str) -> WaterBodyState:
        """Return one registered water body."""
        normalized_name = name.strip()

        try:
            return self._water_bodies[normalized_name]
        except KeyError as error:
            raise KeyError(
                f"Unknown water body: {normalized_name!r}."
            ) from error

    def list_water_bodies(self) -> tuple[WaterBodyState, ...]:
        """Return every water body ordered by name."""
        return tuple(
            self._water_bodies[name]
            for name in sorted(self._water_bodies)
        )

    def handle_event(self, event: Event) -> None:
        """Apply one supported event to the current world state."""
        event_id = str(event.event_id)

        if event_id in self._processed_event_ids:
            return

        if isinstance(event, WaterRemovedEvent):
            self._apply_water_removed(event)

        self._processed_event_ids.add(event_id)

    def _apply_water_removed(
        self,
        event: WaterRemovedEvent,
    ) -> None:
        """Update one water body after a water-removal event."""
        current_state = self.get_water_body(event.water_body_name)

        updated_state, result = current_state.remove_height(
            event.removed_height_m
        )

        if abs(
            result.removed_volume_liters
            - event.removed_volume_liters
        ) > 0.01:
            raise ValueError(
                "WaterRemovedEvent removed volume is inconsistent "
                "with the registered water-body geometry."
            )

        if abs(
            result.remaining_volume_liters
            - event.remaining_volume_liters
        ) > 0.01:
            raise ValueError(
                "WaterRemovedEvent remaining volume is inconsistent "
                "with the registered water-body geometry."
            )

        self._water_bodies[event.water_body_name] = updated_state

    @property
    def water_body_count(self) -> int:
        """Return the number of registered water bodies."""
        return len(self._water_bodies)

    @property
    def processed_event_count(self) -> int:
        """Return the number of processed event identifiers."""
        return len(self._processed_event_ids)
