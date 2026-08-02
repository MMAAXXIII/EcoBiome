"""Tkinter prototype of the EcoBiome project dashboard."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ecobiome.ui.desktop.theme import (
    ThemeIdentifier,
    available_desktop_themes,
    get_desktop_theme,
)
from ecobiome.ui.desktop.view_model import (
    DesktopDashboardViewModel,
)


class EcoBiomeDesktopApp:
    """Display one EcoBiome dashboard snapshot."""

    def __init__(
        self,
        view_model: DesktopDashboardViewModel,
        *,
        initial_theme: ThemeIdentifier = (
            ThemeIdentifier.ECOBIOME_NIGHT
        ),
        on_theme_changed: (
            Callable[[ThemeIdentifier], None] | None
        ) = None,
    ) -> None:
        self._view_model = view_model
        self._theme = get_desktop_theme(initial_theme)
        self._on_theme_changed = on_theme_changed

        self._root = tk.Tk()
        self._root.title(
            f"EcoBiome — {view_model.project_name}"
        )
        self._root.geometry("1280x800")
        self._root.minsize(980, 640)

        self._style = ttk.Style(self._root)
        self._theme_name_by_display = {
            theme.display_name: theme.identifier
            for theme in available_desktop_themes()
        }

        self._configure_theme()
        self._build_interface()

    def run(self) -> None:
        """Start the desktop event loop."""
        self._root.mainloop()

    def _configure_theme(self) -> None:
        """Apply semantic theme tokens to Tk widgets."""
        theme = self._theme

        self._root.configure(
            background=theme.background
        )

        self._style.theme_use("clam")

        self._style.configure(
            "Eco.TFrame",
            background=theme.background,
        )

        self._style.configure(
            "Surface.TFrame",
            background=theme.surface,
        )

        self._style.configure(
            "Elevated.TFrame",
            background=theme.surface_elevated,
        )

        self._style.configure(
            "Title.TLabel",
            background=theme.background,
            foreground=theme.text_primary,
            font=("Segoe UI Semibold", 27),
        )

        self._style.configure(
            "Subtitle.TLabel",
            background=theme.background,
            foreground=theme.text_secondary,
            font=("Segoe UI", 11),
        )

        self._style.configure(
            "Section.TLabel",
            background=theme.surface,
            foreground=theme.text_primary,
            font=("Segoe UI Semibold", 14),
        )

        self._style.configure(
            "MetricValue.TLabel",
            background=theme.surface,
            foreground=theme.text_primary,
            font=("Segoe UI Semibold", 24),
        )

        self._style.configure(
            "MetricLabel.TLabel",
            background=theme.surface,
            foreground=theme.text_secondary,
            font=("Segoe UI", 10),
        )

        self._style.configure(
            "MetricSymbol.TLabel",
            background=theme.surface,
            foreground=theme.accent,
            font=("Segoe UI Symbol", 18),
        )

        self._style.configure(
            "StatusTitle.TLabel",
            background=theme.surface_elevated,
            foreground=theme.success,
            font=("Segoe UI Semibold", 12),
        )

        self._style.configure(
            "StatusText.TLabel",
            background=theme.surface_elevated,
            foreground=theme.text_secondary,
            font=("Segoe UI", 10),
        )

        self._style.configure(
            "ActivityTitle.TLabel",
            background=theme.surface,
            foreground=theme.text_primary,
            font=("Segoe UI Semibold", 10),
        )

        self._style.configure(
            "ActivityMeta.TLabel",
            background=theme.surface,
            foreground=theme.text_secondary,
            font=("Segoe UI", 9),
        )

        self._style.configure(
            "ActivitySymbol.TLabel",
            background=theme.surface,
            foreground=theme.accent,
            font=("Segoe UI Symbol", 17),
        )

        self._style.configure(
            "Eco.TCombobox",
            fieldbackground=theme.surface_elevated,
            background=theme.surface_elevated,
            foreground=theme.text_primary,
            arrowcolor=theme.text_primary,
            bordercolor=theme.border,
        )

        self._style.map(
            "Eco.TCombobox",
            fieldbackground=[
                ("readonly", theme.surface_elevated),
            ],
            foreground=[
                ("readonly", theme.text_primary),
            ],
            selectbackground=[
                ("readonly", theme.surface_elevated),
            ],
            selectforeground=[
                ("readonly", theme.text_primary),
            ],
        )

    def _build_interface(self) -> None:
        """Build the complete project-dashboard layout."""
        root_frame = ttk.Frame(
            self._root,
            style="Eco.TFrame",
            padding=(28, 22),
        )
        root_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(2, weight=1)

        self._build_header(root_frame)
        self._build_metrics(root_frame)
        self._build_content(root_frame)
        self._build_footer(root_frame)

    def _build_header(
        self,
        parent: ttk.Frame,
    ) -> None:
        """Build title, project metadata and theme selector."""
        header = ttk.Frame(
            parent,
            style="Eco.TFrame",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 20),
        )
        header.columnconfigure(0, weight=1)

        title_group = ttk.Frame(
            header,
            style="Eco.TFrame",
        )
        title_group.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            title_group,
            text="EcoBiome",
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            title_group,
            text=(
                f"{self._view_model.project_name}  ·  "
                f"{self._view_model.project_type}"
            ),
            style="Subtitle.TLabel",
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        ttk.Label(
            title_group,
            text=self._view_model.description,
            style="Subtitle.TLabel",
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        controls = ttk.Frame(
            header,
            style="Eco.TFrame",
        )
        controls.grid(
            row=0,
            column=1,
            sticky="e",
        )

        ttk.Label(
            controls,
            text="Thème",
            style="Subtitle.TLabel",
        ).pack(
            side=tk.LEFT,
            padx=(0, 8),
        )

        selected_theme = tk.StringVar(
            value=self._theme.display_name
        )

        theme_selector = ttk.Combobox(
            controls,
            state="readonly",
            width=20,
            style="Eco.TCombobox",
            textvariable=selected_theme,
            values=tuple(
                self._theme_name_by_display
            ),
        )
        theme_selector.pack(side=tk.LEFT)

        theme_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._change_theme(
                selected_theme.get()
            ),
        )

    def _build_metrics(
        self,
        parent: ttk.Frame,
    ) -> None:
        """Build the row of project summary cards."""
        metrics = ttk.Frame(
            parent,
            style="Eco.TFrame",
        )
        metrics.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 20),
        )

        for index, metric in enumerate(
            self._view_model.metrics
        ):
            metrics.columnconfigure(index, weight=1)

            card = ttk.Frame(
                metrics,
                style="Surface.TFrame",
                padding=(18, 15),
            )
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(
                    0 if index == 0 else 6,
                    0
                    if index
                    == len(self._view_model.metrics) - 1
                    else 6,
                ),
            )

            ttk.Label(
                card,
                text=metric.symbol,
                style="MetricSymbol.TLabel",
            ).pack(anchor="w")

            ttk.Label(
                card,
                text=metric.value,
                style="MetricValue.TLabel",
            ).pack(
                anchor="w",
                pady=(3, 0),
            )

            ttk.Label(
                card,
                text=metric.label,
                style="MetricLabel.TLabel",
            ).pack(anchor="w")

    def _build_content(
        self,
        parent: ttk.Frame,
    ) -> None:
        """Build activity and project-insight panels."""
        content = ttk.Frame(
            parent,
            style="Eco.TFrame",
        )
        content.grid(
            row=2,
            column=0,
            sticky="nsew",
        )

        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        self._build_activity_panel(content)
        self._build_insight_panel(content)

    def _build_activity_panel(
        self,
        parent: ttk.Frame,
    ) -> None:
        """Build the recent scientific activity panel."""
        panel = ttk.Frame(
            parent,
            style="Surface.TFrame",
            padding=20,
        )
        panel.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
        )

        ttk.Label(
            panel,
            text="Activité récente",
            style="Section.TLabel",
        ).pack(anchor="w")

        if not self._view_model.latest_activity:
            ttk.Label(
                panel,
                text=(
                    "Aucune activité pour le moment. "
                    "Votre journal commencera ici."
                ),
                style="ActivityMeta.TLabel",
            ).pack(
                anchor="w",
                pady=(22, 0),
            )
            return

        for activity in self._view_model.latest_activity:
            row = ttk.Frame(
                panel,
                style="Surface.TFrame",
                padding=(0, 14),
            )
            row.pack(
                fill=tk.X,
                expand=False,
            )

            symbol = ttk.Label(
                row,
                text=activity.symbol,
                style="ActivitySymbol.TLabel",
                width=3,
            )
            symbol.pack(
                side=tk.LEFT,
                anchor="n",
            )

            text_group = ttk.Frame(
                row,
                style="Surface.TFrame",
            )
            text_group.pack(
                side=tk.LEFT,
                fill=tk.X,
                expand=True,
            )

            ttk.Label(
                text_group,
                text=activity.title,
                style="ActivityTitle.TLabel",
            ).pack(anchor="w")

            metadata = (
                f"{activity.category}  ·  "
                f"{activity.occurred_at}"
            )

            ttk.Label(
                text_group,
                text=metadata,
                style="ActivityMeta.TLabel",
            ).pack(
                anchor="w",
                pady=(2, 0),
            )

            if activity.description:
                ttk.Label(
                    text_group,
                    text=activity.description,
                    style="ActivityMeta.TLabel",
                    wraplength=590,
                ).pack(
                    anchor="w",
                    pady=(3, 0),
                )

            if activity.tags:
                ttk.Label(
                    text_group,
                    text=activity.tags,
                    style="ActivityMeta.TLabel",
                ).pack(
                    anchor="w",
                    pady=(3, 0),
                )

    def _build_insight_panel(
        self,
        parent: ttk.Frame,
    ) -> None:
        """Build status and event-distribution panels."""
        right_column = ttk.Frame(
            parent,
            style="Eco.TFrame",
        )
        right_column.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        status = ttk.Frame(
            right_column,
            style="Elevated.TFrame",
            padding=20,
        )
        status.pack(
            fill=tk.X,
            pady=(0, 12),
        )

        ttk.Label(
            status,
            text=self._view_model.status_title,
            style="StatusTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            status,
            text=self._view_model.status_message,
            style="StatusText.TLabel",
            wraplength=380,
        ).pack(
            anchor="w",
            pady=(6, 0),
        )

        distribution = ttk.Frame(
            right_column,
            style="Surface.TFrame",
            padding=20,
        )
        distribution.pack(
            fill=tk.BOTH,
            expand=True,
        )

        ttk.Label(
            distribution,
            text="Répartition du journal",
            style="Section.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 14),
        )

        if not self._view_model.event_distribution:
            ttk.Label(
                distribution,
                text="Aucune donnée disponible.",
                style="ActivityMeta.TLabel",
            ).pack(anchor="w")
            return

        for label, count in (
            self._view_model.event_distribution
        ):
            row = ttk.Frame(
                distribution,
                style="Surface.TFrame",
            )
            row.pack(
                fill=tk.X,
                pady=5,
            )

            ttk.Label(
                row,
                text=label,
                style="ActivityMeta.TLabel",
            ).pack(side=tk.LEFT)

            ttk.Label(
                row,
                text=str(count),
                style="ActivityTitle.TLabel",
            ).pack(side=tk.RIGHT)

    def _build_footer(
        self,
        parent: ttk.Frame,
    ) -> None:
        """Build project metadata footer."""
        footer_text = (
            f"Dernière mise à jour : "
            f"{self._view_model.updated_at}"
        )

        if self._view_model.tags:
            footer_text += (
                f"   ·   {self._view_model.tags}"
            )

        ttk.Label(
            parent,
            text=footer_text,
            style="Subtitle.TLabel",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=(16, 0),
        )

    def _change_theme(
        self,
        display_name: str,
    ) -> None:
        """Apply a theme selected by the user."""
        identifier = self._theme_name_by_display[
            display_name
        ]

        self._theme = get_desktop_theme(identifier)

        for child in self._root.winfo_children():
            child.destroy()

        self._configure_theme()
        self._build_interface()

        if self._on_theme_changed is not None:
            self._on_theme_changed(identifier)


def run_desktop_dashboard(
    view_model: DesktopDashboardViewModel,
    *,
    initial_theme: ThemeIdentifier = (
        ThemeIdentifier.ECOBIOME_NIGHT
    ),
) -> None:
    """Create and run the EcoBiome desktop dashboard."""
    EcoBiomeDesktopApp(
        view_model,
        initial_theme=initial_theme,
    ).run()
