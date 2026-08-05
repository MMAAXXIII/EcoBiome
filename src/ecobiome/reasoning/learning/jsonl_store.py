"""JSONLines persistence for traceable scientific learning events."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from ecobiome.reasoning.learning.event import (
    LearningEvent,
    LearningOutcome,
)


class JsonlLearningEventStore:
    """Persist immutable learning events in an append-only JSONL file."""

    def __init__(
        self,
        path: str | Path,
        events: Iterable[LearningEvent] = (),
    ) -> None:
        self._path = Path(path)

        if self._path.exists() and not self._path.is_file():
            raise ValueError(
                f"Learning-event store path is not a file: "
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
        """Return the JSONL storage path."""
        return self._path

    def append(self, event: LearningEvent) -> None:
        """Append one event while rejecting duplicate identifiers."""
        existing_ids = {
            stored_event.event_id
            for stored_event in self.load()
        }

        if event.event_id in existing_ids:
            raise ValueError(
                f"Duplicate learning-event identifier: "
                f"{event.event_id}."
            )

        serialized = json.dumps(
            self._serialize(event),
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

    def load(self) -> tuple[LearningEvent, ...]:
        """Load all valid events in deterministic chronological order."""
        if not self._path.exists():
            return ()

        events: list[LearningEvent] = []
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
                    payload = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(
                        "Invalid JSON in learning-event store "
                        f"at line {line_number}: {error.msg}."
                    ) from error

                if not isinstance(payload, dict):
                    raise TypeError(
                        "Learning-event store line "
                        f"{line_number} must contain a JSON object."
                    )

                try:
                    event = self._deserialize(payload)
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as error:
                    raise ValueError(
                        "Invalid learning event at line "
                        f"{line_number}: {error}."
                    ) from error

                if event.event_id in event_ids:
                    raise ValueError(
                        "Duplicate learning-event identifier "
                        f"{event.event_id} at line {line_number}."
                    )

                event_ids.add(event.event_id)
                events.append(event)

        return tuple(
            sorted(
                events,
                key=lambda event: (
                    event.occurred_at,
                    str(event.event_id),
                ),
            )
        )

    def load_for_hypothesis(
        self,
        hypothesis_id: UUID,
    ) -> tuple[LearningEvent, ...]:
        """Load chronological events associated with one hypothesis."""
        return tuple(
            event
            for event in self.load()
            if event.hypothesis_id == hypothesis_id
        )

    @staticmethod
    def _serialize(
        event: LearningEvent,
    ) -> dict[str, object]:
        """Convert one event into JSON-compatible data."""
        return {
            "event_id": str(event.event_id),
            "hypothesis_id": str(event.hypothesis_id),
            "experiment_id": event.experiment_id,
            "outcome": event.outcome.value,
            "confidence_before": event.confidence_before,
            "confidence_after": event.confidence_after,
            "occurred_at": event.occurred_at.isoformat(),
            "evidence_ids": [
                str(evidence_id)
                for evidence_id in event.evidence_ids
            ],
            "notes": event.notes,
        }

    @staticmethod
    def _deserialize(
        payload: dict[str, Any],
    ) -> LearningEvent:
        """Rebuild one learning event from JSON-compatible data."""
        raw_evidence_ids = payload["evidence_ids"]

        if not isinstance(raw_evidence_ids, list):
            raise TypeError(
                "evidence_ids must be a JSON array"
            )

        occurred_at = datetime.fromisoformat(
            str(payload["occurred_at"])
        )

        return LearningEvent(
            event_id=UUID(str(payload["event_id"])),
            hypothesis_id=UUID(
                str(payload["hypothesis_id"])
            ),
            experiment_id=str(
                payload["experiment_id"]
            ),
            outcome=LearningOutcome(
                str(payload["outcome"])
            ),
            confidence_before=float(
                payload["confidence_before"]
            ),
            confidence_after=float(
                payload["confidence_after"]
            ),
            occurred_at=occurred_at,
            evidence_ids=tuple(
                UUID(str(evidence_id))
                for evidence_id in raw_evidence_ids
            ),
            notes=str(payload["notes"]),
        )
