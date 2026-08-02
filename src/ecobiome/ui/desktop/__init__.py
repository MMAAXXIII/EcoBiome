"""Desktop dashboard prototype for EcoBiome."""

from ecobiome.ui.desktop.analytics import (
    DiagnosticAnalyticsViewModel,
    HypothesisDetailViewModel,
)
from ecobiome.ui.desktop.analytics_panel import (
    DiagnosticAnalyticsPanel,
)
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
from ecobiome.ui.desktop.layout import (
    DEFAULT_DASHBOARD_ORDER,
    DashboardLayoutPreferences,
    DashboardLayoutPreset,
    DashboardLayoutStore,
    DashboardSection,
    dashboard_layout_for_preset,
    dashboard_layout_from_dict,
    dashboard_layout_to_dict,
    identify_dashboard_layout_preset,
)
from ecobiome.ui.desktop.layout_dialog import (
    DashboardLayoutDialog,
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
    "DEFAULT_DASHBOARD_ORDER",
    "DashboardActivityViewModel",
    "DashboardLayoutDialog",
    "DashboardLayoutPreferences",
    "DashboardLayoutPreset",
    "DashboardLayoutStore",
    "DashboardMemoryViewModel",
    "DashboardMetricViewModel",
    "DashboardSection",
    "DesktopDashboardViewModel",
    "DesktopIcon",
    "DesktopTheme",
    "DiagnosticAnalyticsPanel",
    "DiagnosticAnalyticsViewModel",
    "EcoBiomeDesktopApp",
    "HypothesisDetailViewModel",
    "MediaGalleryItem",
    "ProbabilityBar",
    "ThemeIdentifier",
    "UserProgressViewModel",
    "available_desktop_themes",
    "build_media_gallery",
    "dashboard_layout_for_preset",
    "dashboard_layout_from_dict",
    "dashboard_layout_to_dict",
    "draw_line_chart",
    "draw_probability_bar",
    "draw_progress_bar",
    "draw_quality_donut",
    "get_desktop_theme",
    "icon_text",
    "identify_dashboard_layout_preset",
    "run_desktop_dashboard",
]
