"""Tkinter implementation of the EcoBiome visual dashboard."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import UTC, datetime
from functools import partial
from html import escape
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

from ecobiome.ui.desktop.analytics import (
    DiagnosticAnalyticsViewModel,
)
from ecobiome.ui.desktop.analytics_panel import (
    DiagnosticAnalyticsPanel,
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
)
from ecobiome.ui.desktop.gallery_viewer import (
    GalleryViewerDialog,
)
from ecobiome.ui.desktop.hero import (
    DashboardHeroBanner,
    resolve_project_title,
    select_hero_image_path,
)
from ecobiome.ui.desktop.icons import (
    DesktopIcon,
    icon_text,
)
from ecobiome.ui.desktop.layout import (
    DashboardLayoutPreferences,
    DashboardLayoutStore,
    DashboardSection,
)
from ecobiome.ui.desktop.layout_dialog import (
    DashboardLayoutDialog,
)
from ecobiome.ui.desktop.navigation import (
    NavigationIdentifier,
    NavigationItem,
    NavigationStatus,
    bind_gallery_navigation,
)
from ecobiome.ui.desktop.responsive import (
    DashboardViewportMetrics,
    ResponsiveDashboardViewport,
    geometry_dimensions,
    responsive_sidebar_width,
)
from ecobiome.ui.desktop.surfaces import (
    RoundedSurfaceCard,
    SurfaceLevel,
    draw_diagnostic_icon,
)
from ecobiome.ui.desktop.theme import (
    ThemeIdentifier,
    available_desktop_themes,
    get_desktop_theme,
)
from ecobiome.ui.desktop.view_model import (
    DashboardActivityViewModel,
    DashboardMemoryViewModel,
    DashboardMetricViewModel,
    DesktopDashboardViewModel,
)


class EcoBiomeDesktopApp:
    """Display one rich EcoBiome project dashboard."""

    def __init__(
        self,
        view_model: DesktopDashboardViewModel,
        *,
        gallery_items: tuple[MediaGalleryItem, ...] = (),
        gallery_directory: Path | None = None,
        on_import_gallery_files: (
            Callable[[tuple[Path, ...]], None] | None
        ) = None,
        analytics_view_model: (
            DiagnosticAnalyticsViewModel | None
        ) = None,
        layout_preferences: (
            DashboardLayoutPreferences | None
        ) = None,
        layout_store: DashboardLayoutStore | None = None,
        initial_theme: ThemeIdentifier = (
            ThemeIdentifier.ECOBIOME_NIGHT
        ),
        on_theme_changed: (
            Callable[[ThemeIdentifier], None] | None
        ) = None,
        initial_geometry: str = "1500x900",
        start_maximized: bool = True,
    ) -> None:
        if not initial_geometry.strip():
            raise ValueError(
                "Initial desktop geometry cannot be empty."
            )

        self._view_model = view_model
        self._gallery_items = gallery_items
        self._gallery_directory = (
            Path(gallery_directory)
            if gallery_directory is not None
            else None
        )
        self._on_import_gallery_files = (
            on_import_gallery_files
        )
        self._analytics_view_model = analytics_view_model
        self._layout_store = layout_store
        self._layout_preferences = (
            layout_preferences
            if layout_preferences is not None
            else (
                layout_store.load_or_default()
                if layout_store is not None
                else DashboardLayoutPreferences()
            )
        )
        self._section_frames: dict[
            DashboardSection,
            tk.Frame,
        ] = {}
        self._layout_summary_label: tk.Label | None = None
        self._footer_container: tk.Frame | None = None
        self._gallery_images: list[ImageTk.PhotoImage] = []
        self._theme = get_desktop_theme(initial_theme)
        self._on_theme_changed = on_theme_changed
        self._viewport: ResponsiveDashboardViewport | None = None
        self._hero_banner: DashboardHeroBanner | None = None
        self._layout_region: tk.Frame | None = None
        self._sidebar: tk.Frame | None = None
        self._sidebar_navigation_canvas: tk.Canvas | None = None
        self._sidebar_navigation_content: tk.Frame | None = None
        self._sidebar_navigation_scrollbar: tk.Canvas | None = None
        self._pending_theme_identifier: ThemeIdentifier | None = None
        self._theme_change_after_id: str | None = None
        self._window_is_maximized = False
        self._window_restore_geometry = initial_geometry
        self._window_drag_offset: tuple[int, int] | None = None
        self._start_maximized = start_maximized

        self._root = tk.Tk()
        self._root.withdraw()
        display_width = self._root.winfo_screenwidth()
        display_height = self._root.winfo_screenheight()

        if not start_maximized:
            display_width, display_height = geometry_dimensions(
                initial_geometry
            )

        self._visual_scale = DashboardViewportMetrics(
            screen_width=display_width,
            screen_height=display_height,
            maximum_ratio=1.2,
        ).fit_ratio
        self._spacing: SpacingScale = spacing_scale(
            self._visual_scale
        )
        self._root.title(
            f"EcoBiome — {view_model.project_name}"
        )
        self._root.geometry(initial_geometry)
        self._root.minsize(1180, 720)

        self._theme_name_by_display = {
            theme.display_name: theme.identifier
            for theme in available_desktop_themes()
        }
        self._root_binding_ids: dict[str, str] = {}
        self._navigation_items = (
            self._create_navigation_items()
        )

        self._install_root_bindings()
        self._build_interface()
        self._wire_gallery_entries()
        self._root.bind(
            "<Configure>",
            self._on_root_configure,
            add="+",
        )
        self._root.bind(
            "<Map>",
            self._on_root_map,
            add="+",
        )


    def run(self) -> None:
        """Start the desktop event loop."""
        self._show_window()
        self._root.mainloop()

    def _install_root_bindings(self) -> None:
        """Install application-owned global bindings exactly once."""
        if self._root_binding_ids:
            return

        handlers: tuple[
            tuple[str, Callable[[tk.Event], str | None]],
            ...,
        ] = (
            ("<MouseWheel>", self._on_root_mousewheel),
            ("<Button-4>", self._on_root_scroll_up),
            ("<Button-5>", self._on_root_scroll_down),
            ("<Home>", self._on_root_home),
            ("<End>", self._on_root_end),
        )

        for sequence, handler in handlers:
            binding_id = self._root.bind(
                sequence,
                handler,
                add="+",
            )

            if binding_id is None:
                raise RuntimeError(
                    f"Unable to install root binding {sequence}."
                )

            self._root_binding_ids[sequence] = binding_id

    def _active_viewport(
        self,
    ) -> ResponsiveDashboardViewport | None:
        """Return the live viewport targeted by application bindings."""
        viewport = self._viewport

        if viewport is None or not viewport.is_alive:
            return None

        return viewport

    def _on_root_mousewheel(
        self,
        event: tk.Event,
    ) -> str | None:
        """Delegate one wheel event to the current viewport."""
        viewport = self._active_viewport()
        return (
            viewport.handle_mousewheel(event)
            if viewport is not None
            else None
        )

    def _on_root_scroll_up(
        self,
        event: tk.Event,
    ) -> str | None:
        """Delegate one X11 upward-scroll event."""
        viewport = self._active_viewport()
        return (
            viewport.handle_scroll_up(event)
            if viewport is not None
            else None
        )

    def _on_root_scroll_down(
        self,
        event: tk.Event,
    ) -> str | None:
        """Delegate one X11 downward-scroll event."""
        viewport = self._active_viewport()
        return (
            viewport.handle_scroll_down(event)
            if viewport is not None
            else None
        )

    def _on_root_home(
        self,
        event: tk.Event,
    ) -> str | None:
        """Delegate one Home key event."""
        if self._event_targets_editable_widget(event):
            return None

        viewport = self._active_viewport()
        return (
            viewport.handle_home(event)
            if viewport is not None
            else None
        )

    def _on_root_end(
        self,
        event: tk.Event,
    ) -> str | None:
        """Delegate one End key event."""
        if self._event_targets_editable_widget(event):
            return None

        viewport = self._active_viewport()
        return (
            viewport.handle_end(event)
            if viewport is not None
            else None
        )

    @staticmethod
    def _event_targets_editable_widget(
        event: tk.Event,
    ) -> bool:
        """Return whether navigation keys belong to a text-editing widget."""
        widget = event.widget

        if not isinstance(widget, tk.Misc):
            return False

        try:
            widget_class = str(widget.winfo_class())
        except tk.TclError:
            return False

        return widget_class in {
            "Entry",
            "Spinbox",
            "TCombobox",
            "TEntry",
            "TSpinbox",
            "Text",
        }

    def _build_interface(self) -> None:
        """Build a fixed sidebar and an independent main viewport."""
        self._root.configure(
            background=self._theme.background
        )
        self._root.grid_columnconfigure(
            0,
            weight=1,
        )
        self._root.grid_rowconfigure(
            0,
            weight=1,
        )

        shell = tk.Frame(
            self._root,
            background=self._theme.background,
        )
        shell.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        shell.grid_columnconfigure(
            0,
            minsize=130,
        )
        shell.grid_columnconfigure(
            1,
            weight=1,
        )
        shell.grid_rowconfigure(
            0,
            weight=1,
        )

        self._build_sidebar(shell)
        self._build_main_area(shell)

    def _create_navigation_items(
        self,
    ) -> tuple[NavigationItem, ...]:
        """Create the single explicit primary-navigation table."""
        coming_soon = self._show_coming_soon

        return (
            NavigationItem(
                identifier=NavigationIdentifier.DASHBOARD,
                icon=DesktopIcon.DASHBOARD,
                label="Tableau de bord",
                status=NavigationStatus.AVAILABLE,
                command=self._show_dashboard,
                selected=True,
            ),
            NavigationItem(
                identifier=NavigationIdentifier.JOURNAL,
                icon=DesktopIcon.JOURNAL,
                label="Journal scientifique",
                status=NavigationStatus.COMING_SOON,
                command=partial(
                    coming_soon,
                    "Journal scientifique",
                ),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.GALLERY,
                icon=DesktopIcon.GALLERY,
                label="Galerie",
                status=NavigationStatus.AVAILABLE,
                command=self._open_gallery_dialog,
            ),
            NavigationItem(
                identifier=NavigationIdentifier.PROJECTS,
                icon=DesktopIcon.PROJECTS,
                label="Projets",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Projets"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.DIAGNOSTIC,
                icon=DesktopIcon.DIAGNOSTIC,
                label="IA & Diagnostic",
                status=NavigationStatus.COMING_SOON,
                command=partial(
                    coming_soon,
                    "IA & Diagnostic",
                ),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.ANALYSES,
                icon=DesktopIcon.ANALYSES,
                label="Analyses",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Analyses"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.EXPERIMENTS,
                icon=DesktopIcon.EXPERIMENTS,
                label="Expériences",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Expériences"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.LEARNING,
                icon=DesktopIcon.LEARNING,
                label="Apprentissage",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Apprentissage"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.STATISTICS,
                icon=DesktopIcon.STATISTICS,
                label="Statistiques",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Statistiques"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.COMMUNITY,
                icon=DesktopIcon.COMMUNITY,
                label="Communauté",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Communauté"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.DONATIONS,
                icon=DesktopIcon.DONATIONS,
                label="Dons",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Dons"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.SHOP,
                icon=DesktopIcon.SHOP,
                label="Boutique",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Boutique"),
            ),
            NavigationItem(
                identifier=NavigationIdentifier.SETTINGS,
                icon=DesktopIcon.SETTINGS,
                label="Paramètres",
                status=NavigationStatus.COMING_SOON,
                command=partial(coming_soon, "Paramètres"),
            ),
        )

    def _show_dashboard(self) -> None:
        """Return the current dashboard viewport to its beginning."""
        viewport = self._active_viewport()

        if viewport is not None:
            viewport.scroll_to_top()

    def _show_coming_soon(
        self,
        label: str,
    ) -> None:
        """Explain an intentionally visible unavailable destination."""
        messagebox.showinfo(
            "Fonction à venir",
            (
                f"{label} sera disponible dans une prochaine version "
                "d’EcoBiome."
            ),
            parent=self._root,
        )

    def _build_sidebar(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the permanent left navigation."""
        sidebar = tk.Frame(
            parent,
            background=self._darken(
                self._theme.background,
                0.18,
            ),
            width=responsive_sidebar_width(
                1500
            ),
            highlightthickness=1,
            highlightbackground=self._theme.border,
        )
        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        sidebar.grid_propagate(False)
        sidebar.pack_propagate(False)
        self._sidebar = sidebar

        logo = tk.Frame(
            sidebar,
            background=sidebar["background"],
        )
        logo.pack(
            fill=tk.X,
            padx=10,
            pady=(12, 10),
        )

        tk.Label(
            logo,
            text=DesktopIcon.LOGO.value,
            background=logo["background"],
            foreground=self._theme.success,
            font=self._font("Segoe UI Symbol", 28),
        ).pack(side=tk.LEFT)

        logo_text = tk.Frame(
            logo,
            background=logo["background"],
        )
        logo_text.pack(
            side=tk.LEFT,
            padx=(10, 0),
        )

        tk.Label(
            logo_text,
            text="EcoBiome",
            background=logo_text["background"],
            foreground=self._theme.text_primary,
            font=self._font("Segoe UI Semibold", 19),
        ).pack(anchor="w")

        tk.Label(
            logo_text,
            text="Diagnostic intelligent",
            background=logo_text["background"],
            foreground=self._theme.text_secondary,
            font=self._font("Segoe UI", 9),
        ).pack(anchor="w")

        navigation_shell = tk.Frame(
            sidebar,
            background=sidebar["background"],
        )
        navigation_shell.pack(
            fill=tk.BOTH,
            expand=True,
            padx=(10, 4),
        )
        navigation_shell.grid_columnconfigure(0, weight=1)
        navigation_shell.grid_rowconfigure(0, weight=1)

        navigation_canvas = tk.Canvas(
            navigation_shell,
            background=navigation_shell["background"],
            borderwidth=0,
            highlightthickness=0,
            yscrollincrement=self._px(24),
        )
        navigation_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        self._sidebar_navigation_canvas = navigation_canvas

        scrollbar_width = self._px(7)
        navigation_scrollbar = tk.Canvas(
            navigation_shell,
            width=scrollbar_width,
            background=sidebar["background"],
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )
        navigation_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        self._sidebar_navigation_scrollbar = navigation_scrollbar
        scrollbar_thumb = navigation_scrollbar.create_rectangle(
            1,
            0,
            max(2, scrollbar_width - 1),
            1,
            fill=self._blend(
                self._theme.border,
                self._theme.text_secondary,
                0.42,
            ),
            activefill=self._theme.accent,
            outline="",
        )
        scrollbar_drag_offset: int | None = None

        def update_navigation_scrollbar(
            first: float | str,
            last: float | str,
        ) -> None:
            first_fraction = float(first)
            last_fraction = float(last)

            if first_fraction <= 0.0 and last_fraction >= 1.0:
                navigation_scrollbar.grid_remove()
                return

            navigation_scrollbar.grid()
            track_height = max(
                1,
                navigation_scrollbar.winfo_height(),
            )
            thumb_top = round(track_height * first_fraction)
            thumb_bottom = round(track_height * last_fraction)
            minimum_thumb_height = min(
                track_height,
                self._px(28),
            )

            if thumb_bottom - thumb_top < minimum_thumb_height:
                thumb_bottom = min(
                    track_height,
                    thumb_top + minimum_thumb_height,
                )
                thumb_top = max(
                    0,
                    thumb_bottom - minimum_thumb_height,
                )

            navigation_scrollbar.coords(
                scrollbar_thumb,
                1,
                thumb_top,
                max(2, scrollbar_width - 1),
                thumb_bottom,
            )

        def refresh_navigation_scrollbar(
            _event: tk.Event,
        ) -> None:
            first, last = navigation_canvas.yview()
            update_navigation_scrollbar(first, last)

        def move_navigation_from_scrollbar(
            event: tk.Event,
        ) -> str:
            track_height = max(
                1,
                navigation_scrollbar.winfo_height(),
            )
            coordinates = navigation_scrollbar.coords(
                scrollbar_thumb
            )
            thumb_height = max(
                1,
                round(coordinates[3] - coordinates[1]),
            )
            thumb_top = max(
                0,
                min(
                    track_height - thumb_height,
                    event.y - thumb_height // 2,
                ),
            )
            navigation_canvas.yview_moveto(
                thumb_top / track_height
            )
            return "break"

        def begin_scrollbar_drag(
            event: tk.Event,
        ) -> str:
            nonlocal scrollbar_drag_offset
            coordinates = navigation_scrollbar.coords(
                scrollbar_thumb
            )

            if coordinates[1] <= event.y <= coordinates[3]:
                scrollbar_drag_offset = round(
                    event.y - coordinates[1]
                )
                return "break"

            move_navigation_from_scrollbar(event)
            updated_coordinates = navigation_scrollbar.coords(
                scrollbar_thumb
            )
            scrollbar_drag_offset = round(
                event.y - updated_coordinates[1]
            )
            return "break"

        def drag_navigation_scrollbar(
            event: tk.Event,
        ) -> str:
            if scrollbar_drag_offset is None:
                return "break"

            track_height = max(
                1,
                navigation_scrollbar.winfo_height(),
            )
            coordinates = navigation_scrollbar.coords(
                scrollbar_thumb
            )
            thumb_height = max(
                1,
                round(coordinates[3] - coordinates[1]),
            )
            thumb_top = max(
                0,
                min(
                    track_height - thumb_height,
                    event.y - scrollbar_drag_offset,
                ),
            )
            navigation_canvas.yview_moveto(
                thumb_top / track_height
            )
            return "break"

        def end_scrollbar_drag(
            _event: tk.Event,
        ) -> str:
            nonlocal scrollbar_drag_offset
            scrollbar_drag_offset = None
            return "break"

        navigation_canvas.configure(
            yscrollcommand=update_navigation_scrollbar,
        )
        navigation_scrollbar.bind(
            "<Configure>",
            refresh_navigation_scrollbar,
        )
        navigation_scrollbar.bind(
            "<ButtonPress-1>",
            begin_scrollbar_drag,
        )
        navigation_scrollbar.bind(
            "<B1-Motion>",
            drag_navigation_scrollbar,
        )
        navigation_scrollbar.bind(
            "<ButtonRelease-1>",
            end_scrollbar_drag,
        )

        for widget in (navigation_canvas, navigation_scrollbar):
            widget.bind(
                "<MouseWheel>",
                self._scroll_sidebar_navigation,
                add="+",
            )
            widget.bind(
                "<Button-4>",
                self._scroll_sidebar_navigation,
                add="+",
            )
            widget.bind(
                "<Button-5>",
                self._scroll_sidebar_navigation,
                add="+",
            )

        navigation_frame = tk.Frame(
            navigation_canvas,
            background=navigation_canvas["background"],
        )
        self._sidebar_navigation_content = navigation_frame
        navigation_window = navigation_canvas.create_window(
            (0, 0),
            window=navigation_frame,
            anchor="nw",
        )
        navigation_frame.bind(
            "<Configure>",
            lambda _event: navigation_canvas.configure(
                scrollregion=navigation_canvas.bbox("all"),
            ),
        )
        navigation_canvas.bind(
            "<Configure>",
            lambda event: navigation_canvas.itemconfigure(
                navigation_window,
                width=max(1, event.width),
            ),
        )

        self._build_navigation_group(
            navigation_frame,
            label="Espace scientifique",
            items=self._navigation_items[:8],
        )

        separator = tk.Frame(
            navigation_frame,
            background=self._theme.border,
            height=self._px(1),
        )
        separator.pack(
            fill=tk.X,
            padx=self._px(8),
            pady=(self._px(5), self._px(4)),
        )

        self._build_navigation_group(
            navigation_frame,
            label="Communauté et compte",
            items=self._navigation_items[8:],
        )

        self._build_progress_card(sidebar)
        self._build_engine_card(sidebar)

        theme_row = tk.Frame(
            sidebar,
            background=sidebar["background"],
        )
        theme_row.pack(
            fill=tk.X,
            padx=16,
            pady=(12, 18),
        )

        for icon in (
            DesktopIcon.SUN,
            DesktopIcon.MOON,
            DesktopIcon.LOGO,
        ):
            tk.Label(
                theme_row,
                text=icon.value,
                background=theme_row["background"],
                foreground=self._theme.text_secondary,
                font=self._font("Segoe UI Symbol", 16),
                padx=9,
            ).pack(side=tk.LEFT)

    def _build_navigation_group(
        self,
        parent: tk.Widget,
        *,
        label: str,
        items: tuple[NavigationItem, ...],
    ) -> None:
        """Build one clearly labelled navigation group."""
        tk.Label(
            parent,
            text=label.upper(),
            anchor="w",
            background=parent["background"],
            foreground=self._blend(
                self._theme.text_secondary,
                self._theme.background,
                0.22,
            ),
            font=self._font("Segoe UI Semibold", 7),
            padx=self._px(9),
            pady=self._px(2),
        ).pack(fill=tk.X)

        for item in items:
            self._navigation_button(
                parent,
                item=item,
            )

    def _navigation_button(
        self,
        parent: tk.Widget,
        *,
        item: NavigationItem,
    ) -> tk.Button:
        """Build one sidebar navigation item."""
        parent_background = str(
            parent.cget("background")
        )
        selected_background = (
            self._blend(
                self._theme.success,
                self._theme.background,
                0.28,
            )
        )
        hover_background = self._blend(
            self._theme.surface_elevated,
            self._theme.background,
            0.54,
        )
        selected = item.selected
        available = (
            item.status is NavigationStatus.AVAILABLE
        )
        button = tk.Button(
            parent,
            text=icon_text(item.icon, item.label),
            command=item.command,
            anchor="w",
            takefocus=True,
            background=(
                selected_background
                if selected
                else parent_background
            ),
            foreground=(
                self._theme.text_primary
                if selected or available
                else self._theme.text_secondary
            ),
            activebackground=hover_background,
            activeforeground=self._theme.text_primary,
            font=self._font(
                "Segoe UI Semibold"
                if selected or available
                else "Segoe UI",
                9,
            ),
            relief=(
                tk.SUNKEN
                if selected
                else tk.FLAT
            ),
            borderwidth=(2 if selected else 1),
            highlightthickness=2,
            highlightbackground=parent_background,
            highlightcolor=self._theme.accent,
            padx=self._px(10),
            pady=self._px(3),
            cursor="hand2",
        )
        button.pack(
            fill=tk.X,
            pady=self._px(1),
        )

        invoke = partial(
            self._invoke_navigation_button,
            button,
        )
        button.bind("<Return>", invoke)
        button.bind("<KP_Enter>", invoke)
        button.bind("<space>", invoke)
        button.bind(
            "<FocusIn>",
            self._reveal_sidebar_navigation_item,
            add="+",
        )
        button.bind(
            "<MouseWheel>",
            self._scroll_sidebar_navigation,
            add="+",
        )
        button.bind(
            "<Button-4>",
            self._scroll_sidebar_navigation,
            add="+",
        )
        button.bind(
            "<Button-5>",
            self._scroll_sidebar_navigation,
            add="+",
        )

        return button

    def _scroll_sidebar_navigation(
        self,
        event: tk.Event,
    ) -> str | None:
        """Scroll the navigation group under the pointer."""
        canvas = self._sidebar_navigation_canvas

        if canvas is None:
            return None

        if getattr(event, "num", None) == 4:
            direction = -1
        elif getattr(event, "num", None) == 5:
            direction = 1
        elif event.delta:
            direction = -1 if event.delta > 0 else 1
        else:
            return None

        canvas.yview_scroll(direction, "units")
        return "break"

    def _reveal_sidebar_navigation_item(
        self,
        event: tk.Event,
    ) -> None:
        """Keep a keyboard-focused navigation item inside the viewport."""
        canvas = self._sidebar_navigation_canvas
        content = self._sidebar_navigation_content
        widget = event.widget

        if (
            canvas is None
            or content is None
            or not isinstance(widget, tk.Widget)
        ):
            return

        content.update_idletasks()
        content_height = max(1, content.winfo_reqheight())
        viewport_height = max(1, canvas.winfo_height())
        item_top = widget.winfo_y()
        item_bottom = item_top + widget.winfo_height()
        viewport_top = round(canvas.canvasy(0))
        viewport_bottom = viewport_top + viewport_height

        if item_top < viewport_top:
            canvas.yview_moveto(item_top / content_height)
        elif item_bottom > viewport_bottom:
            canvas.yview_moveto(
                max(
                    0.0,
                    (item_bottom - viewport_height)
                    / content_height,
                )
            )

    @staticmethod
    def _invoke_navigation_button(
        button: tk.Button,
        _event: tk.Event,
    ) -> str:
        """Invoke one navigation command and stop the class binding."""
        button.invoke()
        return "break"

    def _build_progress_card(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the progression card."""
        progress = self._view_model.progress

        card = self._card(
            parent,
            padding=11,
            level=SurfaceLevel.ANALYTIC,
        )
        card.pack(
            fill=tk.X,
            padx=10,
            pady=(0, 10),
        )

        header = tk.Frame(
            card,
            background=card["background"],
        )
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=DesktopIcon.LOGO.value,
            background=header["background"],
            foreground=self._theme.success,
            font=self._font("Segoe UI Symbol", 25),
        ).pack(side=tk.LEFT)

        text = tk.Frame(
            header,
            background=header["background"],
        )
        text.pack(
            side=tk.LEFT,
            padx=(10, 0),
        )

        tk.Label(
            text,
            text=f"Niveau {progress.level}",
            background=text["background"],
            foreground=self._theme.text_primary,
            font=self._font("Segoe UI Semibold", 12),
        ).pack(anchor="w")

        tk.Label(
            text,
            text=progress.title,
            background=text["background"],
            foreground=self._theme.success,
            font=self._font("Segoe UI", 9),
        ).pack(anchor="w")

        bar = tk.Canvas(
            card,
            height=8,
            background=card["background"],
            highlightthickness=0,
        )
        bar.pack(
            fill=tk.X,
            pady=(12, 6),
        )

        bar.bind(
            "<Configure>",
            lambda event: self._draw_progress(
                bar,
                event.width,
                progress.progress_ratio,
            ),
        )

        footer = tk.Frame(
            card,
            background=card["background"],
        )
        footer.pack(fill=tk.X)

        tk.Label(
            footer,
            text=(
                f"{progress.current_xp:,} / "
                f"{progress.next_level_xp:,} XP"
            ).replace(",", " "),
            background=footer["background"],
            foreground=self._theme.text_secondary,
            font=self._font("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        tk.Label(
            footer,
            text=f"{progress.progress_percent}%",
            background=footer["background"],
            foreground=self._theme.text_primary,
            font=self._font("Segoe UI Semibold", 9),
        ).pack(side=tk.RIGHT)

    def _build_engine_card(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the operational-engine status card."""
        card = self._card(
            parent,
            padding=11,
            level=SurfaceLevel.ANALYTIC,
        )
        card.pack(
            fill=tk.X,
            padx=10,
            pady=(0, 4),
        )

        tk.Label(
            card,
            text=(
                f"{DesktopIcon.STATUS.value}  "
                "Moteur opérationnel"
            ),
            background=card["background"],
            foreground=self._theme.text_primary,
            font=self._font("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            card,
            text="Tous les systèmes actifs",
            background=card["background"],
            foreground=self._theme.text_secondary,
            font=self._font("Segoe UI", 9),
            anchor="w",
        ).pack(
            fill=tk.X,
            pady=(4, 0),
        )

    def _build_main_area(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build one scrollable dashboard beside the fixed sidebar."""
        container = tk.Frame(
            parent,
            background=self._theme.background,
        )
        container.grid(
            row=0,
            column=1,
            sticky="nsew",
        )
        container.grid_columnconfigure(
            0,
            weight=1,
        )
        container.grid_rowconfigure(
            0,
            weight=1,
        )

        viewport = ResponsiveDashboardViewport(
            container,
            background=self._theme.background,
            maximum_content_width=1900,
            scrollbar_thumb=self._blend(
                self._theme.border,
                self._theme.text_secondary,
                0.42,
            ),
            scrollbar_active_thumb=self._theme.accent,
            scrollbar_width=self._px(8),
            minimum_thumb_height=self._px(36),
        )
        viewport.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        self._viewport = viewport

        body = viewport.content
        body.grid_columnconfigure(
            0,
            weight=1,
        )

        self._gallery_images.clear()
        self._section_frames.clear()
        self._footer_container = None
        self._layout_region = None

        self._hero_banner = DashboardHeroBanner(
            body,
            theme=self._theme,
            title=resolve_project_title(
                self._view_model
            ),
            subtitle=(
                self._view_model.description
                or (
                    "Diagnostic intelligent · observations, "
                    "hypothèses et expériences"
                )
            ),
            image_path=self._select_hero_image_path(),
            on_open_gallery=self._open_gallery_dialog,
            on_export_report=self._export_report,
            on_customize_layout=self._open_layout_dialog,
            theme_names=tuple(
                self._theme_name_by_display
            ),
            current_theme=self._theme.display_name,
            on_theme_changed=self._change_theme,
            on_minimize_window=self._minimize_window,
            on_toggle_maximize_window=(
                self._toggle_maximize_window
            ),
            on_close_window=self._close_window,
            visual_scale=self._visual_scale,
        )
        self._hero_banner.bind_window_drag(
            on_start=self._begin_window_drag,
            on_motion=self._drag_window,
            on_end=self._end_window_drag,
        )
        self._hero_banner.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=self._spacing.padding,
            pady=(self._spacing.gutter, 0),
        )

        self._build_metric_row(body)
        self._build_analysis_row(body)
        self._build_customizable_sections(body)
        self._build_footer_container(body)
        self._apply_layout_preferences()
        viewport.refresh()



    def _build_metric_row(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the five diagnostic KPI cards."""
        row = tk.Frame(
            parent,
            background=self._theme.background,
        )
        row.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=self._spacing.padding,
            pady=(self._spacing.gutter, 0),
        )

        for index, metric in enumerate(
            self._view_model.metrics
        ):
            row.grid_columnconfigure(
                index,
                weight=1,
                uniform="metric",
            )

            self._metric_card(
                row,
                metric,
            ).grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(
                    0 if index == 0 else 5,
                    0
                    if index
                    == len(self._view_model.metrics) - 1
                    else 5,
                ),
            )

    def _metric_card(
        self,
        parent: tk.Widget,
        metric: DashboardMetricViewModel,
    ) -> tk.Frame:
        """Build one image-forward diagnostic metric card."""
        accent = self._accent_for_role(
            metric.accent_role
        )
        card = self._surface_card(
            parent,
            background=self._blend(
                self._theme.surface,
                accent,
                0.12,
            ),
            border=self._blend(
                self._theme.border,
                accent,
                0.35,
            ),
            padding=self._spacing.compact,
            level=SurfaceLevel.ANALYTIC,
        )

        summary = tk.Frame(
            card,
            background=card["background"],
        )
        summary.pack(
            fill=tk.X,
        )

        text = tk.Frame(
            summary,
            background=summary["background"],
        )
        text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        tk.Label(
            text,
            text=metric.label,
            background=text["background"],
            foreground=self._theme.text_primary,
            font=self._type(TypographyRole.PRIMARY_LABEL),
        ).pack(anchor="w")

        tk.Label(
            text,
            text=metric.value,
            background=text["background"],
            foreground=self._theme.text_primary,
            font=self._type(TypographyRole.KPI_VALUE),
        ).pack(
            anchor="w",
            pady=(5, 0),
        )

        badge_size = max(24, self._spacing.group * 2)
        badge = tk.Canvas(
            summary,
            width=badge_size,
            height=badge_size,
            background=summary["background"],
            highlightthickness=0,
        )
        badge.pack(
            side=tk.LEFT,
            anchor="n",
            before=text,
            padx=(0, self._px(12)),
        )
        draw_diagnostic_icon(
            badge,
            role=metric.accent_role,
            accent=accent,
            fill=self._blend(
                card["background"],
                accent,
                0.28,
            ),
            size=badge_size,
        )

        tk.Label(
            card,
            text=metric.detail,
            anchor="w",
            justify=tk.LEFT,
            background=card["background"],
            foreground=accent,
            font=self._type(TypographyRole.BODY),
        ).pack(
            fill=tk.X,
            pady=(self._spacing.micro, 0),
        )

        return card


    def _build_analysis_row(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the causal chain and the single ranked hypothesis view."""
        row = tk.Frame(
            parent,
            background=self._theme.background,
        )
        row.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=self._spacing.padding,
            pady=(self._spacing.gutter, 0),
        )
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        chain_card = self._card(
            row,
            padding=11,
        )
        chain_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6),
        )
        self._section_title(
            chain_card,
            "Chaîne causale principale",
        )

        chain = tk.Frame(
            chain_card,
            background=chain_card["background"],
        )
        chain.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(8, 0),
        )

        metric_values = tuple(
            metric.value
            for metric in self._view_model.metrics
        )

        def metric_value(
            index: int,
            fallback: str,
        ) -> str:
            if index < len(metric_values):
                return metric_values[index]

            return fallback

        stages = (
            (
                "success",
                "Observation",
                f"{metric_value(0, '—')} observations",
                self._theme.success,
            ),
            (
                "quality",
                "Qualité",
                f"Fiabilité {metric_value(1, '—')}",
                self._theme.accent,
            ),
            (
                "hypothesis",
                "Abduction",
                f"{metric_value(2, '—')} hypothèses",
                self._theme.hypothesis,
            ),
            (
                "warning",
                "Expériences",
                f"{metric_value(3, '—')} protocoles",
                self._theme.warning,
            ),
            (
                "conclusion",
                "Conclusion",
                f"{metric_value(4, '—')} résultats",
                self._theme.success,
            ),
        )

        chain.grid_rowconfigure(0, weight=1)

        for stage_index in range(len(stages)):
            chain.grid_columnconfigure(
                stage_index * 2,
                weight=1,
                uniform="causal-stage",
            )

        for index, (
            role,
            title,
            subtitle,
            accent,
        ) in enumerate(stages):
            stage = tk.Frame(
                chain,
                background=chain["background"],
            )
            stage.grid(
                row=0,
                column=index * 2,
                sticky="nsew",
                padx=self._px(2),
            )

            badge_size = self._px(64)
            badge = tk.Canvas(
                stage,
                width=badge_size,
                height=badge_size,
                background=stage["background"],
                highlightthickness=0,
            )
            badge.pack()
            draw_diagnostic_icon(
                badge,
                role=role,
                accent=accent,
                fill=self._blend(
                    chain_card["background"],
                    accent,
                    0.20,
                ),
                size=badge_size,
            )

            tk.Label(
                stage,
                text=title,
                background=stage["background"],
                foreground=accent,
                font=self._font("Segoe UI Semibold", 10),
            ).pack(pady=(5, 1))
            tk.Label(
                stage,
                text=subtitle,
                background=stage["background"],
                foreground=self._theme.text_secondary,
                font=self._font("Segoe UI", 8),
                justify=tk.CENTER,
                wraplength=self._px(126),
            ).pack()

            if index < len(stages) - 1:
                tk.Label(
                    chain,
                    text=DesktopIcon.ARROW.value,
                    background=chain["background"],
                    foreground=accent,
                    font=self._font("Segoe UI Symbol", 16),
                ).grid(
                    row=0,
                    column=index * 2 + 1,
                    sticky="ns",
                    padx=self._px(1),
                )

        hypotheses = self._card(
            row,
            padding=11,
        )
        hypotheses.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0),
        )
        self._section_title(
            hypotheses,
            "Hypothèses principales",
        )

        if (
            self._analytics_view_model is None
            or not self._analytics_view_model.probability_bars
        ):
            self._muted_label(
                hypotheses,
                "Aucune hypothèse disponible.",
            ).pack(
                anchor="w",
                pady=(14, 0),
            )
            return

        for probability in (
            self._analytics_view_model.probability_bars[:5]
        ):
            hypothesis_row = tk.Frame(
                hypotheses,
                background=hypotheses["background"],
            )
            hypothesis_row.pack(
                fill=tk.X,
                pady=(2, 0),
            )

            header = tk.Frame(
                hypothesis_row,
                background=hypothesis_row["background"],
            )
            header.pack(fill=tk.X)

            tk.Label(
                header,
                text=probability.identifier,
                background=self._theme.surface_elevated,
                foreground=probability.accent,
                font=self._font("Segoe UI Semibold", 8),
                padx=6,
                pady=1,
            ).pack(side=tk.LEFT)
            tk.Label(
                header,
                text=probability.label,
                background=header["background"],
                foreground=self._theme.text_primary,
                font=self._font("Segoe UI", 8),
            ).pack(
                side=tk.LEFT,
                padx=(8, 0),
            )
            tk.Label(
                header,
                text=f"{probability.probability}%",
                background=header["background"],
                foreground=self._theme.text_primary,
                font=self._font("Segoe UI Semibold", 8),
            ).pack(side=tk.RIGHT)

            bar = tk.Canvas(
                hypothesis_row,
                height=self._px(4),
                background=hypothesis_row["background"],
                highlightthickness=0,
            )
            bar.pack(
                fill=tk.X,
                pady=(2, 0),
            )

            def redraw_bar(
                event: tk.Event,
                *,
                canvas: tk.Canvas = bar,
                value: int = probability.probability,
                color: str = probability.accent,
            ) -> None:
                bar_width = max(
                    1,
                    event.width,
                )
                canvas.delete("all")
                bar_height = max(
                    1,
                    event.height - 1,
                )
                canvas.create_rectangle(
                    0,
                    0,
                    bar_width,
                    bar_height,
                    fill=self._theme.surface_elevated,
                    outline="",
                )
                canvas.create_rectangle(
                    0,
                    0,
                    bar_width * value / 100,
                    bar_height,
                    fill=color,
                    outline="",
                )

            bar.bind(
                "<Configure>",
                redraw_bar,
            )


    def _build_activity_row(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build recent observations and the recommended experiment."""
        row = tk.Frame(
            parent,
            background=self._theme.background,
        )
        row.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)
        row.grid_rowconfigure(0, weight=1)

        activity = self._card(
            row,
            padding=12,
        )
        activity.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 6),
        )

        self._section_title(
            activity,
            "Observations récentes",
        )

        if not self._view_model.latest_activity:
            self._muted_label(
                activity,
                "Votre activité apparaîtra ici.",
            ).pack(anchor="w", pady=(14, 0))
        else:
            for item in self._view_model.latest_activity[:5]:
                self._activity_item(
                    activity,
                    item,
                )

        recommendation = self._card(
            row,
            padding=12,
        )
        recommendation.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(6, 0),
        )

        self._section_title(
            recommendation,
            "Expérience recommandée",
        )

        badge = tk.Label(
            recommendation,
            text="E3   Priorité haute",
            background=self._blend(
                recommendation["background"],
                self._theme.hypothesis,
                0.32,
            ),
            foreground=self._theme.hypothesis,
            font=self._font("Segoe UI Semibold", 9),
            padx=9,
            pady=5,
        )
        badge.pack(
            anchor="w",
            pady=(8, 6),
        )

        self._body_label(
            recommendation,
            "Test d'obscurité contrôlé",
            strong=True,
        ).pack(anchor="w")

        self._muted_label(
            recommendation,
            (
                "Vérifier la présence de lumière résiduelle "
                "dans l'environnement contrôlé."
            ),
            wraplength=310,
        ).pack(
            anchor="w",
            pady=(5, 7),
        )

        self._body_label(
            recommendation,
            "Ressources nécessaires",
            strong=True,
        ).pack(anchor="w")

        self._muted_label(
            recommendation,
            (
                "• Chambre noire\n"
                "• Capteur de luminance étalonné\n"
                "• Sources lumineuses de test\n\n"
                "Durée estimée : 15–30 minutes"
            ),
            wraplength=310,
        ).pack(
            anchor="w",
            pady=(4, 7),
        )

        self._action_button(
            recommendation,
            text="Voir toutes les expériences  →",
            accent=self._theme.warning,
        ).pack(fill=tk.X)





    def _build_customizable_sections(
        self,
        parent: tk.Widget,
    ) -> None:
        """Create the compact customizable dashboard region."""
        region = tk.Frame(
            parent,
            background=self._theme.background,
        )
        region.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=self._spacing.padding,
            pady=(self._spacing.gutter, 0),
        )
        region.grid_columnconfigure(
            0,
            weight=2,
            uniform="dashboard-section",
        )
        region.grid_columnconfigure(
            1,
            weight=1,
            uniform="dashboard-section",
        )
        self._layout_region = region

        builders = {
            DashboardSection.ACTIVITY: (
                self._build_activity_row
            ),
            DashboardSection.ANALYTICS: (
                self._build_diagnostic_analytics
            ),
            DashboardSection.GALLERY: (
                self._build_gallery
            ),
            DashboardSection.MEMORIES: (
                self._build_memories
            ),
        }

        for section in DashboardSection:
            container = tk.Frame(
                region,
                background=self._theme.background,
            )
            container.grid_columnconfigure(
                0,
                weight=1,
            )
            container.grid_rowconfigure(
                0,
                weight=1,
            )
            self._section_frames[
                section
            ] = container
            builders[section](
                container
            )


    def _build_footer_container(
        self,
        parent: tk.Widget,
    ) -> None:
        """Create the footer below the compact dashboard region."""
        container = tk.Frame(
            parent,
            background=self._theme.background,
        )
        container.grid_columnconfigure(
            0,
            weight=1,
        )
        container.grid(
            row=4,
            column=0,
            sticky="ew",
        )
        self._footer_container = container
        self._build_footer(
            container
        )


    def _apply_layout_preferences(
        self,
    ) -> None:
        """Apply visibility and pair adjacent complementary sections."""
        for section_frame in self._section_frames.values():
            section_frame.grid_forget()

        visible_sections = list(
            self._layout_preferences.visible_sections
        )
        processed: set[DashboardSection] = set()
        row = 0

        pair_definitions = (
            (
                frozenset(
                    {
                        DashboardSection.ACTIVITY,
                        DashboardSection.ANALYTICS,
                    }
                ),
                DashboardSection.ACTIVITY,
                DashboardSection.ANALYTICS,
            ),
            (
                frozenset(
                    {
                        DashboardSection.MEMORIES,
                        DashboardSection.GALLERY,
                    }
                ),
                DashboardSection.MEMORIES,
                DashboardSection.GALLERY,
            ),
        )

        for index, section in enumerate(
            visible_sections
        ):
            if section in processed:
                continue

            next_section = (
                visible_sections[index + 1]
                if index + 1 < len(visible_sections)
                else None
            )

            matched_pair: tuple[
                DashboardSection,
                DashboardSection,
            ] | None = None

            if next_section is not None:
                adjacent_pair = frozenset(
                    {
                        section,
                        next_section,
                    }
                )

                for (
                    pair_members,
                    left_section,
                    right_section,
                ) in pair_definitions:
                    if adjacent_pair == pair_members:
                        matched_pair = (
                            left_section,
                            right_section,
                        )
                        break

            if matched_pair is None:
                self._section_frames[
                    section
                ].grid(
                    row=row,
                    column=0,
                    columnspan=2,
                    sticky="nsew",
                    pady=(0, 12),
                )
                processed.add(section)
                row += 1
                continue

            left_section, right_section = matched_pair

            self._section_frames[
                left_section
            ].grid(
                row=row,
                column=0,
                sticky="nsew",
                padx=(0, 6),
                pady=(0, 12),
            )
            self._section_frames[
                right_section
            ].grid(
                row=row,
                column=1,
                sticky="nsew",
                padx=(6, 0),
                pady=(0, 12),
            )
            processed.update(
                matched_pair
            )
            row += 1

        if self._layout_summary_label is not None:
            self._layout_summary_label.configure(
                text=self._layout_summary_text()
            )

        self._refresh_viewport()



    def _layout_summary_text(self) -> str:
        """Return a compact layout summary."""
        visible_count = len(
            self._layout_preferences.visible_sections
        )

        hidden_count = (
            len(DashboardSection)
            - visible_count
        )

        return (
            f"{visible_count} section(s) visible(s)"
            f" · {hidden_count} masquée(s)"
        )

    def _open_layout_dialog(self) -> None:
        """Open the dashboard customization dialog."""
        DashboardLayoutDialog(
            self._root,
            preferences=self._layout_preferences,
            theme=self._theme,
            on_apply=self._update_layout_preferences,
        )

    def _update_layout_preferences(
        self,
        preferences: DashboardLayoutPreferences,
    ) -> None:
        """Apply and persist new preferences."""
        self._layout_preferences = preferences

        if self._layout_store is not None:
            self._layout_store.save(
                preferences
            )

        self._apply_layout_preferences()

    def _build_diagnostic_analytics(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the compact quality panel without duplicate hypotheses."""
        if self._analytics_view_model is None:
            return

        panel = DiagnosticAnalyticsPanel(
            parent,
            view_model=self._analytics_view_model,
            theme=self._theme,
            quality_only=True,
            visual_scale=self._visual_scale,
        )

        panel.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

    def _build_gallery(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build a compact quick gallery for the dashboard."""
        card = self._card(
            parent,
            padding=12,
        )
        card.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        header = tk.Frame(
            card,
            background=card["background"],
        )
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Galerie rapide",
            background=header["background"],
            foreground=self._theme.text_primary,
            font=self._type(TypographyRole.SECTION_TITLE),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text=f"{len(self._gallery_items)} image(s)",
            background=header["background"],
            foreground=self._theme.text_secondary,
            font=self._font("Segoe UI", 9),
        ).pack(side=tk.RIGHT)

        if not self._gallery_items:
            empty = self._surface_card(
                card,
                background=self._theme.surface_elevated,
                border=self._theme.border,
                padding=self._px(16),
                level=SurfaceLevel.COMPACT,
            )
            empty.pack(
                fill=tk.BOTH,
                expand=True,
                pady=(12, 0),
            )

            tk.Label(
                empty,
                text=DesktopIcon.GALLERY.value,
                background=empty["background"],
                foreground=self._theme.accent,
                font=self._font("Segoe UI Symbol", 22),
            ).pack()

            self._muted_label(
                empty,
                "Aucune photo enregistrée.",
            ).pack(pady=(6, 0))
        else:
            gallery_row = tk.Frame(
                card,
                background=card["background"],
            )
            gallery_row.pack(
                fill=tk.X,
                pady=(12, 0),
            )

            visible_items = self._gallery_items[:3]

            for index, item in enumerate(
                visible_items
            ):
                gallery_row.grid_columnconfigure(
                    index,
                    weight=1,
                    uniform="quick-gallery",
                )

                tile = self._surface_card(
                    gallery_row,
                    background=self._theme.surface_elevated,
                    border=self._theme.border,
                    padding=self._px(4),
                    level=SurfaceLevel.COMPACT,
                )
                tile.grid(
                    row=0,
                    column=index,
                    sticky="nsew",
                    padx=(
                        0 if index == 0 else 3,
                        0
                        if index == len(visible_items) - 1
                        else 3,
                    ),
                )

                image_widget = self._gallery_thumbnail(
                    tile,
                    item,
                    width=96,
                    height=64,
                )
                image_widget.pack(
                    fill=tk.X,
                    expand=True,
                )

        actions = tk.Frame(
            card,
            background=card["background"],
        )
        actions.pack(
            fill=tk.X,
            pady=(12, 0),
        )

        def import_gallery_files(
            _event: tk.Event,
        ) -> None:
            self._import_gallery_files()

        def open_gallery(
            _event: tk.Event,
        ) -> None:
            self._open_gallery_dialog()

        import_button = self._action_button(
            actions,
            text=icon_text(
                DesktopIcon.ADD,
                "Ajouter",
            ),
            accent=self._theme.success,
        )
        import_button.bind(
            "<Button-1>",
            import_gallery_files,
            add="+",
        )
        import_button.pack(side=tk.LEFT)

        open_button = self._action_button(
            actions,
            text="Ouvrir la galerie  →",
            accent=self._theme.accent,
        )
        open_button.bind(
            "<Button-1>",
            open_gallery,
            add="+",
        )
        open_button.pack(
            side=tk.RIGHT,
        )




    def _wire_gallery_entries(self) -> None:
        """Wire legacy gallery actions outside the explicit primary menu."""
        excluded_roots = (
            (self._sidebar,)
            if self._sidebar is not None
            else ()
        )
        bind_gallery_navigation(
            self._root,
            self._open_gallery_dialog,
            excluded_roots=excluded_roots,
        )

    def _select_hero_image_path(
        self,
    ) -> Path | None:
        """Select a genuinely panoramic project image for the hero."""
        return select_hero_image_path(
            tuple(
                item.path
                for item in self._gallery_items
            )
        )

    def _refresh_hero_banner(self) -> None:
        """Synchronize the hero with the best panoramic gallery item."""
        if self._hero_banner is None:
            return

        self._hero_banner.set_image_path(
            self._select_hero_image_path()
        )
        self._refresh_viewport()

    def _export_report(self) -> None:
        """Export a readable HTML project report."""
        destination = filedialog.asksaveasfilename(
            parent=self._root,
            title="Exporter le rapport EcoBiome",
            defaultextension=".html",
            filetypes=(
                ("Rapport HTML", "*.html"),
                ("Tous les fichiers", "*.*"),
            ),
            initialfile=(
                f"{self._view_model.project_name}"
                "-rapport.html"
            ),
        )

        if not destination:
            return

        metric_rows = "".join(
            (
                "<tr>"
                f"<th>{escape(metric.label)}</th>"
                f"<td>{escape(metric.value)}</td>"
                f"<td>{escape(metric.detail)}</td>"
                "</tr>"
            )
            for metric in self._view_model.metrics
        )

        activity_rows = "".join(
            (
                "<li>"
                f"<strong>{escape(item.title)}</strong>"
                f" — {escape(item.description)}"
                "</li>"
            )
            for item in self._view_model.latest_activity[:10]
        )

        generated_at = datetime.now(
            tz=UTC
        ).strftime(
            "%d/%m/%Y %H:%M UTC"
        )

        report = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{escape(self._view_model.project_name)} — Rapport EcoBiome</title>
<style>
body {{
    max-width: 980px;
    margin: 40px auto;
    padding: 0 24px;
    color: #173239;
    font: 16px/1.55 "Segoe UI", sans-serif;
}}
h1, h2 {{ color: #0b5d4b; }}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 18px 0 28px;
}}
th, td {{
    border: 1px solid #bfd7d1;
    padding: 10px 12px;
    text-align: left;
}}
th {{ background: #eaf6f0; }}
small {{ color: #607980; }}
</style>
</head>
<body>
<h1>{escape(self._view_model.project_name)}</h1>
<p>{escape(self._view_model.description)}</p>
<p><small>Rapport généré le {generated_at}</small></p>
<h2>Indicateurs</h2>
<table>
<thead><tr><th>Indicateur</th><th>Valeur</th><th>Détail</th></tr></thead>
<tbody>{metric_rows}</tbody>
</table>
<h2>Activité récente</h2>
<ul>{activity_rows or "<li>Aucune activité récente.</li>"}</ul>
</body>
</html>
"""

        try:
            Path(destination).write_text(
                report,
                encoding="utf-8",
            )
        except OSError as error:
            messagebox.showerror(
                "Export impossible",
                str(error),
                parent=self._root,
            )
            return

        messagebox.showinfo(
            "Rapport exporté",
            (
                "Le rapport HTML a été enregistré. "
                "Il peut être imprimé en PDF depuis le navigateur."
            ),
            parent=self._root,
        )


    def _open_gallery_dialog(self) -> None:
        """Open the project gallery in a larger viewer."""
        if not self._gallery_items:
            messagebox.showinfo(
                "Galerie vide",
                "Aucune image n'est disponible dans ce projet.",
                parent=self._root,
            )
            return

        GalleryViewerDialog(
            self._root,
            items=self._gallery_items,
            theme=self._theme,
        )

    def _import_gallery_files(self) -> None:
        """Select images and delegate their import to the project."""
        if (
            self._gallery_directory is None
            or self._on_import_gallery_files is None
        ):
            messagebox.showinfo(
                "Import indisponible",
                (
                    "Aucun gestionnaire d'import de médias "
                    "n'est configuré pour ce tableau de bord."
                ),
                parent=self._root,
            )
            return

        selected_files = filedialog.askopenfilenames(
            parent=self._root,
            title="Ajouter des images au projet",
            filetypes=(
                (
                    "Images",
                    (
                        "*.png *.jpg *.jpeg *.webp "
                        "*.bmp *.gif *.tif *.tiff"
                    ),
                ),
                (
                    "Tous les fichiers",
                    "*.*",
                ),
            ),
        )

        if not selected_files:
            return

        source_paths = tuple(
            Path(value)
            for value in selected_files
        )

        try:
            self._on_import_gallery_files(
                source_paths
            )

        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Import impossible",
                str(error),
                parent=self._root,
            )
            return

        self._refresh_gallery_section()

        messagebox.showinfo(
            "Import terminé",
            (
                f"{len(source_paths)} image(s) "
                "ajoutée(s) au projet."
            ),
            parent=self._root,
        )

    def _refresh_gallery_section(self) -> None:
        """Reload media files and rebuild the gallery section."""
        if self._gallery_directory is None:
            return

        self._gallery_items = build_media_gallery(
            self._gallery_directory,
            limit=50,
        )

        gallery_frame = self._section_frames.get(
            DashboardSection.GALLERY
        )

        if gallery_frame is None:
            return

        for child in gallery_frame.winfo_children():
            child.destroy()

        self._gallery_images.clear()

        self._build_gallery(
            gallery_frame
        )

        self._refresh_hero_banner()
        self._wire_gallery_entries()
        self._apply_layout_preferences()

    def _gallery_thumbnail(
        self,
        parent: tk.Widget,
        item: MediaGalleryItem,
        *,
        width: int = 260,
        height: int = 145,
    ) -> tk.Widget:
        """Create one fitted thumbnail or a graceful placeholder."""
        if width <= 0 or height <= 0:
            raise ValueError(
                "Thumbnail dimensions must be positive."
            )

        try:
            with Image.open(item.path) as source:
                image = source.convert("RGB")
                image.thumbnail(
                    (width, height),
                    Image.Resampling.LANCZOS,
                )

                canvas_image = Image.new(
                    "RGB",
                    (width, height),
                    self._theme.surface_elevated,
                )

                x = (
                    canvas_image.width
                    - image.width
                ) // 2

                y = (
                    canvas_image.height
                    - image.height
                ) // 2

                canvas_image.paste(
                    image,
                    (x, y),
                )

            photo = ImageTk.PhotoImage(
                canvas_image
            )

            self._gallery_images.append(photo)

            return tk.Label(
                parent,
                image=photo,
                background=parent["background"],
                borderwidth=0,
            )

        except OSError:
            placeholder = tk.Frame(
                parent,
                background=self._blend(
                    self._theme.surface_elevated,
                    self._theme.accent,
                    0.12,
                ),
                width=width,
                height=height,
            )
            placeholder.pack_propagate(False)

            tk.Label(
                placeholder,
                text=DesktopIcon.GALLERY.value,
                background=placeholder["background"],
                foreground=self._theme.accent,
                font=self._font("Segoe UI Symbol", 24),
            ).pack(expand=True)

            return placeholder

    def _build_memories(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build compact scientific memories and milestones."""
        card = self._card(
            parent,
            padding=12,
        )
        card.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self._section_title(
            card,
            "Souvenirs & jalons",
        )

        row = tk.Frame(
            card,
            background=card["background"],
        )
        row.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(10, 0),
        )

        memories = self._view_model.memories[:3]

        for memory in memories:
            self._memory_card(
                row,
                memory,
            ).pack(
                side=tk.LEFT,
                fill=tk.BOTH,
                expand=True,
                padx=(0, 6),
            )

        add_card = self._surface_card(
            row,
            background=self._theme.surface_elevated,
            border=self._theme.border,
            padding=self._px(12),
            level=SurfaceLevel.COMPACT,
        )
        add_card.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        tk.Label(
            add_card,
            text=DesktopIcon.ADD.value,
            background=add_card["background"],
            foreground=self._theme.text_secondary,
            font=self._font("Segoe UI", 18),
        ).pack()

        self._muted_label(
            add_card,
            "Ajouter un souvenir",
        ).pack(pady=(4, 0))

        self._muted_label(
            add_card,
            "Marquer un jalon important",
        ).pack()

    def _build_footer(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the EcoBiome footer."""
        footer = tk.Frame(
            parent,
            background=self._theme.background,
        )
        footer.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=self._spacing.group,
            pady=(
                self._spacing.gutter,
                self._spacing.padding,
            ),
        )

        tk.Label(
            footer,
            text=(
                f"{DesktopIcon.LOGO.value}  "
                "« La nature ne ment jamais, ce sont nos "
                "instruments qui doivent être questionnés. »"
            ),
            background=footer["background"],
            foreground=self._theme.success,
            font=self._type(TypographyRole.BODY),
        ).pack(side=tk.LEFT)

        tk.Label(
            footer,
            text="●  EcoBiome Desktop Prototype v0.27",
            background=footer["background"],
            foreground=self._theme.text_secondary,
            font=self._type(TypographyRole.METADATA),
        ).pack(side=tk.RIGHT)

    def _activity_item(
        self,
        parent: tk.Widget,
        item: DashboardActivityViewModel,
    ) -> None:
        """Build one recent activity row."""
        row = tk.Frame(
            parent,
            background=parent["background"],
        )
        row.pack(
            fill=tk.X,
            pady=2,
        )

        accent = (
            self._theme.success
            if item.importance == "high"
            else self._theme.accent
        )

        tk.Label(
            row,
            text=item.symbol,
            background=self._blend(
                parent["background"],
                accent,
                0.25,
            ),
            foreground=accent,
            font=self._font("Segoe UI Symbol", 11),
            padx=5,
            pady=2,
        ).pack(side=tk.LEFT)

        text = tk.Frame(
            row,
            background=row["background"],
        )
        text.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(8, 0),
        )

        self._body_label(
            text,
            item.title,
            strong=True,
        ).pack(anchor="w")

        metadata = (
            f"{item.category}  ·  {item.occurred_at}"
        )

        self._muted_label(
            text,
            metadata,
        ).pack(anchor="w")

        tk.Label(
            row,
            text=(
                "Haute"
                if item.importance == "high"
                else "Normale"
            ),
            background=self._blend(
                row["background"],
                accent,
                0.20,
            ),
            foreground=accent,
            font=self._font("Segoe UI Semibold", 8),
            padx=7,
            pady=3,
        ).pack(side=tk.RIGHT)

    def _distribution_row(
        self,
        parent: tk.Widget,
        label: str,
        count: int,
    ) -> None:
        """Build one event-distribution row."""
        row = tk.Frame(
            parent,
            background=parent["background"],
        )
        row.pack(
            fill=tk.X,
            pady=7,
        )

        self._muted_label(
            row,
            label,
        ).pack(side=tk.LEFT)

        tk.Label(
            row,
            text=str(count),
            background=row["background"],
            foreground=self._theme.text_primary,
            font=self._font("Segoe UI Semibold", 10),
        ).pack(side=tk.RIGHT)

        bar = tk.Canvas(
            parent,
            height=5,
            background=parent["background"],
            highlightthickness=0,
        )
        bar.pack(fill=tk.X)

        def redraw_distribution(
            event: tk.Event,
            *,
            canvas: tk.Canvas = bar,
            value: int = count,
        ) -> None:
            self._draw_distribution(
                canvas,
                event.width,
                value,
            )

        bar.bind(
            "<Configure>",
            redraw_distribution,
        )

    def _memory_card(
        self,
        parent: tk.Widget,
        memory: DashboardMemoryViewModel,
    ) -> tk.Frame:
        """Build one memory card."""
        card = self._surface_card(
            parent,
            background=self._theme.surface_elevated,
            border=self._theme.border,
            padding=self._px(13),
            level=SurfaceLevel.COMPACT,
        )

        tk.Label(
            card,
            text=memory.symbol,
            background=card["background"],
            foreground=self._theme.success,
            font=self._font("Segoe UI Symbol", 18),
        ).pack(anchor="w")

        self._body_label(
            card,
            memory.title,
            strong=True,
        ).pack(
            anchor="w",
            pady=(7, 2),
        )

        self._muted_label(
            card,
            memory.subtitle,
        ).pack(anchor="w")

        self._muted_label(
            card,
            memory.date_label,
        ).pack(
            anchor="w",
            pady=(8, 0),
        )

        return card

    def _card(
        self,
        parent: tk.Widget,
        *,
        padding: int,
        level: SurfaceLevel = SurfaceLevel.PANEL,
    ) -> tk.Frame:
        """Create one standard surface card."""
        return self._surface_card(
            parent,
            background=self._theme.surface,
            border=self._theme.border,
            padding=self._px(padding),
            level=level,
        )

    def _surface_card(
        self,
        parent: tk.Widget,
        *,
        background: str,
        border: str,
        padding: int,
        level: SurfaceLevel = SurfaceLevel.PANEL,
    ) -> RoundedSurfaceCard:
        """Create one elevated rounded surface."""
        return RoundedSurfaceCard(
            parent,
            background=background,
            outer_background=str(
                parent["background"]
            ),
            border=border,
            shadow=self._darken(
                self._theme.background,
                0.32,
            ),
            padding=padding,
            level=level,
            visual_scale=self._visual_scale,
        )

    def _px(
        self,
        value: int,
    ) -> int:
        """Scale one layout dimension for the current display."""
        return max(
            1,
            round(value * self._visual_scale),
        )

    def _font(
        self,
        family: str,
        size: int,
    ) -> tuple[str, int]:
        """Scale one explicit Tk font without changing global scaling."""
        return (
            family,
            self._px(size),
        )

    def _type(
        self,
        role: TypographyRole,
    ) -> tuple[str, int]:
        """Resolve one semantic font for the active display scale."""
        return typography_font(
            role,
            visual_scale=self._visual_scale,
        )

    def _section_title(
        self,
        parent: tk.Widget,
        text: str,
    ) -> None:
        """Render one section title."""
        tk.Label(
            parent,
            text=text,
            background=parent["background"],
            foreground=self._theme.text_primary,
            font=self._type(TypographyRole.SECTION_TITLE),
        ).pack(anchor="w")

    def _body_label(
        self,
        parent: tk.Widget,
        text: str,
        *,
        strong: bool,
    ) -> tk.Label:
        """Create one body label."""
        return tk.Label(
            parent,
            text=text,
            background=parent["background"],
            foreground=self._theme.text_primary,
            font=self._type(
                TypographyRole.PRIMARY_LABEL
                if strong
                else TypographyRole.BODY
            ),
            justify=tk.LEFT,
        )

    def _muted_label(
        self,
        parent: tk.Widget,
        text: str,
        *,
        wraplength: int = 0,
    ) -> tk.Label:
        """Create one secondary-text label."""
        return tk.Label(
            parent,
            text=text,
            background=parent["background"],
            foreground=self._theme.text_secondary,
            font=self._type(TypographyRole.METADATA),
            justify=tk.LEFT,
            wraplength=wraplength,
        )

    def _action_button(
        self,
        parent: tk.Widget,
        *,
        text: str,
        accent: str,
    ) -> tk.Label:
        """Create one outlined action button."""
        return tk.Label(
            parent,
            text=text,
            background=parent["background"],
            foreground=accent,
            font=self._font("Segoe UI Semibold", 9),
            padx=14,
            pady=8,
            highlightthickness=1,
            highlightbackground=accent,
            cursor="hand2",
        )

    def _draw_progress(
        self,
        canvas: tk.Canvas,
        width: int,
        ratio: float,
    ) -> None:
        """Draw one progression bar."""
        canvas.delete("all")

        canvas.create_rectangle(
            0,
            1,
            width,
            7,
            fill=self._theme.surface_elevated,
            outline="",
        )

        canvas.create_rectangle(
            0,
            1,
            width * ratio,
            7,
            fill=self._theme.success,
            outline="",
        )

    def _draw_distribution(
        self,
        canvas: tk.Canvas,
        width: int,
        value: int,
    ) -> None:
        """Draw one journal-distribution bar."""
        canvas.delete("all")

        canvas.create_rectangle(
            0,
            1,
            width,
            4,
            fill=self._theme.surface_elevated,
            outline="",
        )

        ratio = min(1.0, value / 10)

        canvas.create_rectangle(
            0,
            1,
            width * ratio,
            4,
            fill=self._theme.success,
            outline="",
        )

    def _change_theme(
        self,
        display_name: str,
    ) -> None:
        """Coalesce theme selections outside the current Tk callback."""
        identifier = self._theme_name_by_display[
            display_name
        ]

        self._pending_theme_identifier = identifier

        if self._theme_change_after_id is None:
            self._theme_change_after_id = (
                self._root.after_idle(
                    self._apply_pending_theme
                )
            )

    def _apply_pending_theme(self) -> None:
        """Apply only the last theme selected before Tk becomes idle."""
        self._theme_change_after_id = None
        identifier = self._pending_theme_identifier
        self._pending_theme_identifier = None

        if identifier is not None:
            self._apply_theme(identifier)

    def _apply_theme(
        self,
        identifier: ThemeIdentifier,
    ) -> None:
        """Rebuild the shell with one selected visual theme."""
        self._theme = get_desktop_theme(
            identifier
        )

        self._viewport = None
        self._hero_banner = None
        self._footer_container = None
        self._layout_region = None
        self._sidebar = None
        self._sidebar_navigation_canvas = None
        self._sidebar_navigation_content = None
        self._sidebar_navigation_scrollbar = None

        for child in self._root.winfo_children():
            child.destroy()

        self._build_interface()
        self._wire_gallery_entries()

        if self._on_theme_changed is not None:
            self._on_theme_changed(identifier)


    def _refresh_viewport(self) -> None:
        """Refresh the current main viewport when it exists."""
        if self._viewport is not None:
            self._viewport.refresh()

    def _on_root_configure(
        self,
        event: tk.Event,
    ) -> None:
        """Keep the sidebar proportional to the live window width."""
        if (
            event.widget is not self._root
            or self._sidebar is None
        ):
            return

        self._sidebar.configure(
            width=responsive_sidebar_width(
                max(1, event.width)
            )
        )

    def _show_window(self) -> None:
        """Reveal the application with integrated window chrome."""
        self._root.deiconify()

        if self._start_maximized:
            self._maximize_window()
        else:
            self._root.update_idletasks()
            self._apply_borderless_window()

    def _apply_borderless_window(self) -> None:
        """Hide the native title bar after one window-state transition."""
        try:
            self._root.overrideredirect(True)
        except tk.TclError:
            return

    def _maximize_window(self) -> None:
        """Maximize the application before replacing the native chrome."""
        if not self._window_is_maximized:
            self._window_restore_geometry = (
                self._root.geometry()
            )

        try:
            self._root.overrideredirect(False)
            self._root.state("zoomed")
            self._root.update_idletasks()
            self._window_is_maximized = True
            self._root.after_idle(
                self._apply_borderless_window
            )

        except tk.TclError:
            self._root.geometry(
                f"{self._root.winfo_screenwidth()}x"
                f"{self._root.winfo_screenheight()}+0+0"
            )
            self._root.overrideredirect(True)
            self._window_is_maximized = True

    def _restore_window(self) -> None:
        """Restore the borderless application to its previous geometry."""
        try:
            self._root.overrideredirect(False)
            self._root.state("normal")
            self._root.geometry(
                self._window_restore_geometry
            )
            self._root.update_idletasks()
            self._root.overrideredirect(True)
            self._window_is_maximized = False
        except tk.TclError:
            return

    def _toggle_maximize_window(self) -> None:
        """Toggle between restored and maximized borderless states."""
        if self._window_is_maximized:
            self._restore_window()
        else:
            self._maximize_window()

    def _minimize_window(self) -> None:
        """Temporarily restore native ownership before iconifying."""
        try:
            self._root.overrideredirect(False)
            self._root.iconify()
        except tk.TclError:
            return

    def _close_window(self) -> None:
        """Close the application from the integrated window controls."""
        try:
            self._root.destroy()
        except tk.TclError:
            return

    def _on_root_map(
        self,
        event: tk.Event,
    ) -> None:
        """Restore the integrated chrome after taskbar activation."""
        if event.widget is not self._root:
            return

        self._root.after_idle(
            self._apply_borderless_window
        )

    def _begin_window_drag(
        self,
        event: tk.Event,
    ) -> None:
        """Record the pointer offset for a borderless-window drag."""
        if self._window_is_maximized:
            previous_left = self._root.winfo_x()
            previous_width = max(
                1,
                self._root.winfo_width(),
            )
            horizontal_ratio = max(
                0.08,
                min(
                    0.92,
                    (event.x_root - previous_left)
                    / previous_width,
                ),
            )
            self._restore_window()
            restored_width = max(
                1,
                self._root.winfo_width(),
            )
            horizontal_offset = round(
                restored_width * horizontal_ratio
            )
            vertical_offset = self._px(18)
            self._root.geometry(
                f"+{event.x_root - horizontal_offset}"
                f"+{event.y_root - vertical_offset}"
            )
            self._window_drag_offset = (
                horizontal_offset,
                vertical_offset,
            )
            return

        self._window_drag_offset = (
            event.x_root - self._root.winfo_x(),
            event.y_root - self._root.winfo_y(),
        )

    def _drag_window(
        self,
        event: tk.Event,
    ) -> None:
        """Move the restored borderless window with the pointer."""
        if self._window_drag_offset is None:
            return

        horizontal_offset, vertical_offset = (
            self._window_drag_offset
        )
        self._root.geometry(
            f"+{event.x_root - horizontal_offset}"
            f"+{event.y_root - vertical_offset}"
        )

    def _end_window_drag(
        self,
        _event: tk.Event,
    ) -> None:
        """End one integrated-window drag gesture."""
        self._window_drag_offset = None

    def _accent_for_role(
        self,
        role: str,
    ) -> str:
        """Resolve one semantic accent color."""
        colors = {
            "accent": self._theme.accent,
            "quality": "#4FA4FF",
            "success": self._theme.success,
            "warning": self._theme.warning,
            "hypothesis": self._theme.hypothesis,
            "conclusion": "#4ED3C5",
        }

        return colors.get(
            role,
            self._theme.accent,
        )

    @staticmethod
    def _blend(
        first: str,
        second: str,
        ratio: float,
    ) -> str:
        """Blend two hexadecimal colors."""
        ratio = max(
            0.0,
            min(1.0, ratio),
        )

        first_rgb = tuple(
            int(
                first[index:index + 2],
                16,
            )
            for index in (1, 3, 5)
        )

        second_rgb = tuple(
            int(
                second[index:index + 2],
                16,
            )
            for index in (1, 3, 5)
        )

        result = tuple(
            round(
                start
                + (end - start) * ratio
            )
            for start, end in zip(
                first_rgb,
                second_rgb,
                strict=True,
            )
        )

        return "#" + "".join(
            f"{component:02x}"
            for component in result
        )

    @classmethod
    def _darken(
        cls,
        color: str,
        ratio: float,
    ) -> str:
        """Darken one hexadecimal color."""
        return cls._blend(
            color,
            "#000000",
            ratio,
        )


def run_desktop_dashboard(
    view_model: DesktopDashboardViewModel,
    *,
    gallery_items: tuple[MediaGalleryItem, ...] = (),
    gallery_directory: Path | None = None,
    on_import_gallery_files: (
        Callable[[tuple[Path, ...]], None] | None
    ) = None,
    analytics_view_model: (
        DiagnosticAnalyticsViewModel | None
    ) = None,
    layout_preferences: (
        DashboardLayoutPreferences | None
    ) = None,
    layout_store: (
        DashboardLayoutStore | None
    ) = None,
    initial_theme: ThemeIdentifier = (
        ThemeIdentifier.ECOBIOME_NIGHT
    ),
    initial_geometry: str = "1500x900",
    start_maximized: bool = True,
) -> None:
    """Create and run the EcoBiome desktop dashboard."""
    EcoBiomeDesktopApp(
        view_model,
        gallery_items=gallery_items,
        gallery_directory=gallery_directory,
        on_import_gallery_files=(
            on_import_gallery_files
        ),
        analytics_view_model=analytics_view_model,
        layout_preferences=layout_preferences,
        layout_store=layout_store,
        initial_theme=initial_theme,
        initial_geometry=initial_geometry,
        start_maximized=start_maximized,
    ).run()
