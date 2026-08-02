"""Desktop dashboard prototype for EcoBiome."""

from ecobiome.ui.desktop.app import (
    EcoBiomeDesktopApp,
    run_desktop_dashboard,
)
from ecobiome.ui.desktop.theme import (
    DesktopTheme,
    ThemeIdentifier,
    available_desktop_themes,
    get_desktop_theme,
)
from ecobiome.ui.desktop.view_model import (
    DashboardActivityViewModel,
    DashboardMetricViewModel,
    DesktopDashboardViewModel,
)

__all__ = [
    "DashboardActivityViewModel",
    "DashboardMetricViewModel",
    "DesktopDashboardViewModel",
    "DesktopTheme",
    "EcoBiomeDesktopApp",
    "ThemeIdentifier",
    "available_desktop_themes",
    "get_desktop_theme",
    "run_desktop_dashboard",
]
