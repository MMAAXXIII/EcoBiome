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
from ecobiome.ui.desktop.demo_media import (
    SUPPORTED_DEMO_IMAGE_SUFFIXES,
    PersistentDemoMediaStore,
    is_supported_demo_image,
)
from ecobiome.ui.desktop.gallery import (
    MediaGalleryItem,
    build_media_gallery,
    readable_media_title,
)
from ecobiome.ui.desktop.gallery_viewer import (
    GalleryNavigator,
    GalleryViewerDialog,
)
from ecobiome.ui.desktop.hero import (
    DashboardHeroBanner,
    cover_dimensions,
    resolve_project_title,
    select_hero_image_path,
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
from ecobiome.ui.desktop.navigation import (
    bind_gallery_navigation,
    is_gallery_navigation_text,
    normalize_navigation_text,
)
from ecobiome.ui.desktop.responsive import (
    DashboardViewportMetrics,
    ResponsiveDashboardViewport,
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
    "SUPPORTED_DEMO_IMAGE_SUFFIXES",
    "DashboardActivityViewModel",
    "DashboardHeroBanner",
    "DashboardLayoutDialog",
    "DashboardLayoutPreferences",
    "DashboardLayoutPreset",
    "DashboardLayoutStore",
    "DashboardMemoryViewModel",
    "DashboardMetricViewModel",
    "DashboardSection",
    "DashboardViewportMetrics",
    "DesktopDashboardViewModel",
    "DesktopIcon",
    "DesktopTheme",
    "DiagnosticAnalyticsPanel",
    "DiagnosticAnalyticsViewModel",
    "EcoBiomeDesktopApp",
    "GalleryNavigator",
    "GalleryViewerDialog",
    "HypothesisDetailViewModel",
    "MediaGalleryItem",
    "PersistentDemoMediaStore",
    "ProbabilityBar",
    "ResponsiveDashboardViewport",
    "ThemeIdentifier",
    "UserProgressViewModel",
    "available_desktop_themes",
    "bind_gallery_navigation",
    "build_media_gallery",
    "cover_dimensions",
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
    "is_gallery_navigation_text",
    "is_supported_demo_image",
    "normalize_navigation_text",
    "readable_media_title",
    "resolve_project_title",
    "run_desktop_dashboard",
    "select_hero_image_path",
]
