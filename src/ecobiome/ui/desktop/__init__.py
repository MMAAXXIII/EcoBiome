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
from ecobiome.ui.desktop.design_tokens import (
    SpacingScale,
    TypographyRole,
    spacing_scale,
    typography_font,
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
    NavigationIdentifier,
    NavigationItem,
    NavigationStatus,
    bind_gallery_navigation,
    is_gallery_navigation_text,
    normalize_navigation_text,
)
from ecobiome.ui.desktop.responsive import (
    CanvasVerticalScrollbar,
    DashboardViewportMetrics,
    ResponsiveDashboardViewport,
    geometry_dimensions,
    responsive_content_width,
    responsive_sidebar_width,
    scrollbar_fraction_for_thumb,
    scrollbar_thumb_geometry,
)
from ecobiome.ui.desktop.surfaces import (
    SurfaceLevel,
    SurfaceProfile,
    surface_profile,
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
    "CanvasVerticalScrollbar",
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
    "NavigationIdentifier",
    "NavigationItem",
    "NavigationStatus",
    "PersistentDemoMediaStore",
    "ProbabilityBar",
    "ResponsiveDashboardViewport",
    "SpacingScale",
    "SurfaceLevel",
    "SurfaceProfile",
    "ThemeIdentifier",
    "TypographyRole",
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
    "geometry_dimensions",
    "get_desktop_theme",
    "icon_text",
    "identify_dashboard_layout_preset",
    "is_gallery_navigation_text",
    "is_supported_demo_image",
    "normalize_navigation_text",
    "readable_media_title",
    "resolve_project_title",
    "responsive_content_width",
    "responsive_sidebar_width",
    "run_desktop_dashboard",
    "scrollbar_fraction_for_thumb",
    "scrollbar_thumb_geometry",
    "select_hero_image_path",
    "spacing_scale",
    "surface_profile",
    "typography_font",
]
