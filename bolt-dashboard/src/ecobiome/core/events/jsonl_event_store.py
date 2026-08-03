"""Persistent JSON Lines storage for EcoBiome events."""

from pathlib import Path
from uuid import UUID

from ecobiome.core.events.event import Event
from ecobiome.core.events.event_factory import EventTypeRegistry
from ecobiome.core.events.serializer import event_to_json


class JsonLinesEventStore:
    """Persist events as one JSON object per line."""

    def __init__(
        self,
        path: Path,
        registry: EventTypeRegistry,
    ) -> None:
        self._path = path
        self._registry = registry

    @property
    def path(self) -> Path:
        """Return the JSONL storage path."""
        return self._path

    def append(self, event: Event) -> None:
        """Append one event while rejecting duplicate identifiers."""
        if self.contains(event.event_id):
            raise ValueError(
                f"Event {event.event_id} is already stored."
            )

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as event_file:
            event_file.write(event_to_json(event))
            event_file.write("\n")

    def load(self) -> tuple[Event, ...]:
        """Load every valid event in insertion order."""
        if not self._path.exists():
            return ()

        events: list[Event] = []

        for line_number, raw_line in enumerate(
            self._path.read_text(
                encoding="utf-8"
            ).splitlines(),
            start=1,
        ):
            serialized = raw_line.strip()

            if not serialized:
                continue

            try:
                event = self._registry.create_from_json(
                    serialized
                )
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"{self._path}: invalid event on "
                    f"line {line_number}."
                ) from error

            events.append(event)

        return tuple(events)

    def contains(self, event_id: UUID) -> bool:
        """Return whether an event identifier is already stored."""
        return any(
            event.event_id == event_id
            for event in self.load()
        )

    @property
    def count(self) -> int:
        """Return the number of stored events."""
        return len(self.load())

    def clear(self) -> None:
        """Remove every event while preserving the directory."""
        if self._path.exists():
            self._path.write_text(
                "",
                encoding="utf-8",
                newline="\n",
            )
