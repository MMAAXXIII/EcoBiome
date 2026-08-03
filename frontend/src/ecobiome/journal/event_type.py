"""Stable categories used by the EcoBiome scientific journal."""

from enum import StrEnum


class JournalEventType(StrEnum):
    """High-level categories displayed in scientific timelines."""

    NOTE = "note"
    MEDIA = "media"
    OBSERVATION = "observation"
    DIAGNOSTIC = "diagnostic"
    HYPOTHESIS = "hypothesis"
    EXPERIMENT = "experiment"
    LEARNING = "learning"
    BIOLOGICAL_EVENT = "biological_event"
    INTERVENTION = "intervention"
    MEASUREMENT = "measurement"
    SYSTEM = "system"
