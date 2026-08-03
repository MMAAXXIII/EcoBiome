"""Persistent JSONLines storage for scientific-journal events."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ecobiome.journal.event import JournalEvent
from ecobiome.journal.event_type import JournalEventType
from ecobiome.journal.reference import JournalReference

_TYPE_KEY = "__ecobiome_type__"
_VALUE_KEY = "value"
_ITEMS_KEY = "items"


class JsonlJournalEventStore:
    """Persist immutable journal events in an append-only JSONL file."""

    def __init__(
        self,
        path: str | Path,
        events: Iterable[JournalEvent] = (),
    ) -> None:
        self._path = Path(path)

        if self._path.exists() and not self._path.is_file():
            raise ValueError(
                f"Journal-event store path is not a file: "
                f"{self._path}."
            )

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        for event in events:
            self.append(event)

    @property
    def path(self) -> Path:
        """Return the JSONL journal path."""
        return self._path

    def append(self, event: JournalEvent) -> None:
        """Append one event while rejecting duplicate identifiers."""
        existing_ids = {
            stored_event.event_id
            for stored_event in self.all()
        }

        if event.event_id in existing_ids:
            raise ValueError(
                f"Duplicate journal event identifier: "
                f"{event.event_id}."
            )

        serialized = json.dumps(
            self._serialize_event(event),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )

        with self._path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(serialized)
            stream.write("\n")

    def get(self, event_id: UUID) -> JournalEvent:
        """Return one persisted event by identifier."""
        for event in self.all():
            if event.event_id == event_id:
                return event

        raise KeyError(
            f"Unknown journal event identifier: {event_id}."
        )

    def all(self) -> tuple[JournalEvent, ...]:
        """Load every event in deterministic chronological order."""
        if not self._path.exists():
            return ()

        events: list[JournalEvent] = []
        event_ids: set[UUID] = set()

        with self._path.open(
            "r",
            encoding="utf-8",
        ) as stream:
            for line_number, raw_line in enumerate(
                stream,
                start=1,
            ):
                line = raw_line.strip()

                if not line:
                    continue

                try:
                    raw_payload = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        "Invalid JSON in journal-event store "
                        f"at line {line_number}: {error.msg}."
                    ) from error

                if not isinstance(raw_payload, dict):
                    raise TypeError(
                        "Journal-event store line "
                        f"{line_number} must contain a JSON object."
                    )

                try:
                    event = self._deserialize_event(
                        raw_payload
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as error:
                    raise ValueError(
                        "Invalid journal event at line "
                        f"{line_number}: {error}."
                    ) from error

                if event.event_id in event_ids:
                    raise ValueError(
                        "Duplicate journal event identifier "
                        f"{event.event_id} at line {line_number}."
                    )

                event_ids.add(event.event_id)
                events.append(event)

        return tuple(
            sorted(
                events,
                key=lambda event: (
                    event.occurred_at,
                    event.recorded_at,
                    str(event.event_id),
                ),
            )
        )

    def count(self) -> int:
        """Return the number of persisted journal events."""
        return len(self.all())

    @classmethod
    def _serialize_event(
        cls,
        event: JournalEvent,
    ) -> dict[str, Any]:
        """Convert one event to JSON-compatible structured data."""
        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type.value,
            "title": event.title,
            "description": event.description,
            "occurred_at": event.occurred_at.isoformat(),
            "recorded_at": event.recorded_at.isoformat(),
            "project_id": (
                str(event.project_id)
                if event.project_id is not None
                else None
            ),
            "tags": list(event.tags),
            "attributes": [
                [key, value]
                for key, value in event.attributes
            ],
            "payload": [
                [
                    key,
                    cls._encode_value(value),
                ]
                for key, value in event.payload
            ],
            "references": [
                {
                    "entity_type": reference.entity_type,
                    "entity_id": str(reference.entity_id),
                    "relation": reference.relation,
                }
                for reference in event.references
            ],
        }

    @classmethod
    def _deserialize_event(
        cls,
        payload: Mapping[str, Any],
    ) -> JournalEvent:
        """Rebuild one event from JSON-compatible structured data."""
        raw_tags = payload["tags"]
        raw_attributes = payload["attributes"]
        raw_event_payload = payload["payload"]
        raw_references = payload["references"]

        if not isinstance(raw_tags, list):
            raise TypeError(
                "tags must be a JSON array"
            )

        if not isinstance(raw_attributes, list):
            raise TypeError(
                "attributes must be a JSON array"
            )

        if not isinstance(raw_event_payload, list):
            raise TypeError(
                "payload must be a JSON array"
            )

        if not isinstance(raw_references, list):
            raise TypeError(
                "references must be a JSON array"
            )

        project_value = payload["project_id"]

        project_id = (
            UUID(str(project_value))
            if project_value is not None
            else None
        )

        return JournalEvent(
            event_id=UUID(str(payload["event_id"])),
            event_type=JournalEventType(
                str(payload["event_type"])
            ),
            title=str(payload["title"]),
            description=str(payload["description"]),
            occurred_at=datetime.fromisoformat(
                str(payload["occurred_at"])
            ),
            recorded_at=datetime.fromisoformat(
                str(payload["recorded_at"])
            ),
            project_id=project_id,
            tags=tuple(
                str(tag)
                for tag in raw_tags
            ),
            attributes=tuple(
                cls._decode_pair(
                    item,
                    label="attribute",
                    decode_value=False,
                )
                for item in raw_attributes
            ),
            payload=tuple(
                cls._decode_pair(
                    item,
                    label="payload",
                    decode_value=True,
                )
                for item in raw_event_payload
            ),
            references=tuple(
                cls._deserialize_reference(item)
                for item in raw_references
            ),
        )

    @classmethod
    def _decode_pair(
        cls,
        item: Any,
        *,
        label: str,
        decode_value: bool,
    ) -> tuple[str, Any]:
        """Decode one serialized key/value pair."""
        if (
            not isinstance(item, list)
            or len(item) != 2
        ):
            raise TypeError(
                f"{label} entries must be two-item arrays"
            )

        key = str(item[0])
        value = item[1]

        if decode_value:
            value = cls._decode_value(value)
        else:
            value = str(value)

        return key, value

    @staticmethod
    def _deserialize_reference(
        payload: Any,
    ) -> JournalReference:
        """Rebuild one journal reference."""
        if not isinstance(payload, dict):
            raise TypeError(
                "reference entries must be JSON objects"
            )

        return JournalReference(
            entity_type=str(payload["entity_type"]),
            entity_id=UUID(
                str(payload["entity_id"])
            ),
            relation=str(payload["relation"]),
        )

    @classmethod
    def _encode_value(
        cls,
        value: Any,
    ) -> Any:
        """Encode supported payload values without losing their type."""
        if value is None or isinstance(
            value,
            (bool, int, float, str),
        ):
            return value

        if isinstance(value, UUID):
            return {
                _TYPE_KEY: "uuid",
                _VALUE_KEY: str(value),
            }

        if isinstance(value, datetime):
            if value.tzinfo is None:
                raise ValueError(
                    "Journal payload datetimes must be "
                    "timezone-aware."
                )

            return {
                _TYPE_KEY: "datetime",
                _VALUE_KEY: value.isoformat(),
            }

        if isinstance(value, tuple):
            return {
                _TYPE_KEY: "tuple",
                _ITEMS_KEY: [
                    cls._encode_value(item)
                    for item in value
                ],
            }

        if isinstance(value, list):
            return {
                _TYPE_KEY: "list",
                _ITEMS_KEY: [
                    cls._encode_value(item)
                    for item in value
                ],
            }

        if isinstance(value, Mapping):
            return {
                _TYPE_KEY: "dict",
                _ITEMS_KEY: [
                    [
                        str(key),
                        cls._encode_value(item),
                    ]
                    for key, item in value.items()
                ],
            }

        raise TypeError(
            "Unsupported journal payload value type: "
            f"{type(value).__name__}."
        )

    @classmethod
    def _decode_value(
        cls,
        value: Any,
    ) -> Any:
        """Decode one previously encoded journal payload value."""
        if value is None or isinstance(
            value,
            (bool, int, float, str),
        ):
            return value

        if not isinstance(value, dict):
            raise TypeError(
                "Encoded payload values must be JSON primitives "
                "or typed JSON objects."
            )

        value_type = value.get(_TYPE_KEY)

        if value_type == "uuid":
            return UUID(str(value[_VALUE_KEY]))

        if value_type == "datetime":
            return datetime.fromisoformat(
                str(value[_VALUE_KEY])
            )

        if value_type in {"tuple", "list"}:
            items = value[_ITEMS_KEY]

            if not isinstance(items, list):
                raise TypeError(
                    "Encoded collection items must be an array."
                )

            decoded = [
                cls._decode_value(item)
                for item in items
            ]

            if value_type == "tuple":
                return tuple(decoded)

            return decoded

        if value_type == "dict":
            items = value[_ITEMS_KEY]

            if not isinstance(items, list):
                raise TypeError(
                    "Encoded dictionary items must be an array."
                )

            decoded_mapping: dict[str, Any] = {}

            for item in items:
                if (
                    not isinstance(item, list)
                    or len(item) != 2
                ):
                    raise TypeError(
                        "Encoded dictionary entries must be "
                        "two-item arrays."
                    )

                decoded_mapping[str(item[0])] = (
                    cls._decode_value(item[1])
                )

            return decoded_mapping

        raise ValueError(
            f"Unknown encoded payload type: {value_type!r}."
        )
