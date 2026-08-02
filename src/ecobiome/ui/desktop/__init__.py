"""Desktop dashboard prototype for EcoBiome."""

from ecobiome.ui.desktop.app import (
    EcoBiomeDesktopApp,
    run_desktop_dashboard,
)
from ecobiome.ui.desktop.charts import (
    ProbabilityBar,
    draw_line_chart,
    draw_probability_bar,
    draw_progress_bar,
    draw_quality_donut,
)
from ecobiome.ui.desktop.gallery import (
    MediaGalleryItem,
    build_media_gallery,
)
from ecobiome.ui.desktop.icons import (
    DesktopIcon,
    icon_text,
)
from ecobiome.ui.desktop.theme import (
    DesktopTheme,
    ThemeIdentifier,
    available_desktop_themes,
    get_desktop_theme,
)
from ecobiome.ui.desktop.view_model import (
    DashboardActivityViewModel,
    DashboardMemoryViewModel,
    DashboardMetricViewModel,
    DesktopDashboardViewModel,
    UserProgressViewModel,
)

__all__ = [
    "DashboardActivityViewModel",
    "DashboardMemoryViewModel",
    "DashboardMetricViewModel",
    "DesktopDashboardViewModel",
    "DesktopIcon",
    "DesktopTheme",
    "EcoBiomeDesktopApp",
    "MediaGalleryItem",
    "ProbabilityBar",
    "ThemeIdentifier",
    "UserProgressViewModel",
    "available_desktop_themes",
    "build_media_gallery",
    "draw_line_chart",
    "draw_probability_bar",
    "draw_progress_bar",
    "draw_quality_donut",
    "get_desktop_theme",
    "icon_text",
    "run_desktop_dashboard",
]
