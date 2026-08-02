"""Centralized symbolic iconography for the desktop interface."""

from enum import StrEnum


class DesktopIcon(StrEnum):
    """Unicode icons used consistently across EcoBiome."""

    LOGO = "❧"
    DASHBOARD = "⌂"
    JOURNAL = "▤"
    GALLERY = "▣"
    PROJECTS = "◇"
    DIAGNOSTIC = "◉"
    ANALYSES = "⌁"
    EXPERIMENTS = "⚗"
    LEARNING = "↗"
    STATISTICS = "▥"
    COMMUNITY = "♧"
    DONATIONS = "♡"
    SHOP = "▱"
    SETTINGS = "⚙"
    OBSERVATION = "⌕"
    QUALITY = "◆"
    HYPOTHESIS = "✦"
    CONCLUSION = "◎"
    MEDIA = "▣"
    BIOLOGICAL = "❈"
    NOTE = "✎"
    MEASUREMENT = "∿"
    STATUS = "●"
    EXPORT = "⇩"
    ADD = "+"
    USER = "◉"
    SUN = "☼"
    MOON = "☾"
    MEMORY = "◈"
    ARROW = "→"


def icon_text(
    icon: DesktopIcon,
    label: str,
) -> str:
    """Combine one icon and one readable label."""
    normalized_label = label.strip()

    if not normalized_label:
        raise ValueError(
            "Icon label cannot be empty."
        )

    return f"{icon.value}  {normalized_label}"
