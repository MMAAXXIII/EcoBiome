"""Semantic visual themes for the EcoBiome desktop interface."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ThemeIdentifier(StrEnum):
    """Stable identifiers exposed by the user interface."""

    ECOBIOME_NIGHT = "ecobiome-night"
    LABORATORY_LIGHT = "laboratory-light"
    FOREST = "forest"
    HIGH_CONTRAST = "high-contrast"


@dataclass(frozen=True, slots=True, kw_only=True)
class DesktopTheme:
    """Contain semantic colors used by the desktop dashboard."""

    identifier: ThemeIdentifier
    display_name: str
    background: str
    surface: str
    surface_elevated: str
    text_primary: str
    text_secondary: str
    border: str
    accent: str
    success: str
    warning: str
    danger: str
    hypothesis: str

    def __post_init__(self) -> None:
        """Validate one complete desktop theme."""
        display_name = self.display_name.strip()

        if not display_name:
            raise ValueError(
                "Desktop theme display name cannot be empty."
            )

        color_values = (
            self.background,
            self.surface,
            self.surface_elevated,
            self.text_primary,
            self.text_secondary,
            self.border,
            self.accent,
            self.success,
            self.warning,
            self.danger,
            self.hypothesis,
        )

        if any(
            not _is_hex_color(color)
            for color in color_values
        ):
            raise ValueError(
                "Desktop theme colors must use six-digit "
                "hexadecimal notation."
            )

        object.__setattr__(
            self,
            "display_name",
            display_name,
        )


def _is_hex_color(value: str) -> bool:
    """Return whether a string is a six-digit hexadecimal color."""
    if len(value) != 7 or not value.startswith("#"):
        return False

    try:
        int(value[1:], 16)
    except ValueError:
        return False

    return True


_THEMES: dict[ThemeIdentifier, DesktopTheme] = {
    ThemeIdentifier.ECOBIOME_NIGHT: DesktopTheme(
        identifier=ThemeIdentifier.ECOBIOME_NIGHT,
        display_name="EcoBiome Night",
        background="#020C12",
        surface="#071A22",
        surface_elevated="#0D2831",
        text_primary="#F3F7F4",
        text_secondary="#9AAEA8",
        border="#1D3B42",
        accent="#75D65A",
        success="#7BDC5C",
        warning="#F2A65A",
        danger="#EC6B72",
        hypothesis="#A78BFA",
    ),
    ThemeIdentifier.LABORATORY_LIGHT: DesktopTheme(
        identifier=ThemeIdentifier.LABORATORY_LIGHT,
        display_name="Laboratory Light",
        background="#EEF3F1",
        surface="#FFFFFF",
        surface_elevated="#F8FAF9",
        text_primary="#14231C",
        text_secondary="#53665D",
        border="#CEDBD4",
        accent="#247A57",
        success="#287A49",
        warning="#A96519",
        danger="#B8464D",
        hypothesis="#6654A3",
    ),
    ThemeIdentifier.FOREST: DesktopTheme(
        identifier=ThemeIdentifier.FOREST,
        display_name="Forest",
        background="#142017",
        surface="#203326",
        surface_elevated="#2B4431",
        text_primary="#F3F0DE",
        text_secondary="#BBC6A8",
        border="#4B634D",
        accent="#9BC36A",
        success="#83C87A",
        warning="#D79B55",
        danger="#E78478",
        hypothesis="#C39A74",
    ),
    ThemeIdentifier.HIGH_CONTRAST: DesktopTheme(
        identifier=ThemeIdentifier.HIGH_CONTRAST,
        display_name="High Contrast",
        background="#000000",
        surface="#111111",
        surface_elevated="#1C1C1C",
        text_primary="#FFFFFF",
        text_secondary="#E4E4E4",
        border="#FFFFFF",
        accent="#00E5FF",
        success="#60FF60",
        warning="#FFD800",
        danger="#FF5A5A",
        hypothesis="#D99CFF",
    ),
}


def get_desktop_theme(
    identifier: ThemeIdentifier | str,
) -> DesktopTheme:
    """Return one registered desktop theme."""
    try:
        theme_identifier = ThemeIdentifier(identifier)
    except ValueError as error:
        raise KeyError(
            f"Unknown desktop theme identifier: {identifier}."
        ) from error

    return _THEMES[theme_identifier]


def available_desktop_themes() -> tuple[DesktopTheme, ...]:
    """Return every desktop theme in stable display order."""
    return tuple(
        _THEMES[identifier]
        for identifier in ThemeIdentifier
    )
