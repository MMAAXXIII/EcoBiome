"""Project categories supported by EcoBiome workspaces."""

from enum import StrEnum


class ProjectType(StrEnum):
    """High-level kinds of living-environment projects."""

    AQUARIUM = "aquarium"
    AQUAPONICS = "aquaponics"
    POND = "pond"
    GARDEN = "garden"
    GREENHOUSE = "greenhouse"
    ORCHARD = "orchard"
    HYDROPONICS = "hydroponics"
    TERRARIUM = "terrarium"
    APIARY = "apiary"
    OTHER = "other"
