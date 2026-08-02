"""Tkinter implementation of the EcoBiome visual dashboard."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from PIL import Image, ImageTk

from ecobiome.ui.desktop.gallery import (
    MediaGalleryItem,
)
from ecobiome.ui.desktop.icons import (
    DesktopIcon,
    icon_text,
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
        initial_theme: ThemeIdentifier = (
            ThemeIdentifier.ECOBIOME_NIGHT
        ),
        on_theme_changed: (
            Callable[[ThemeIdentifier], None] | None
        ) = None,
    ) -> None:
        self._view_model = view_model
        self._gallery_items = gallery_items
        self._gallery_images: list[ImageTk.PhotoImage] = []
        self._theme = get_desktop_theme(initial_theme)
        self._on_theme_changed = on_theme_changed

        self._root = tk.Tk()
        self._root.title(
            f"EcoBiome — {view_model.project_name}"
        )
        self._root.geometry("1500x900")
        self._root.minsize(1180, 720)

        self._theme_name_by_display = {
            theme.display_name: theme.identifier
            for theme in available_desktop_themes()
        }

        self._build_interface()

    def run(self) -> None:
        """Start the desktop event loop."""
        self._root.mainloop()

    def _build_interface(self) -> None:
        """Build the complete interface."""
        self._root.configure(
            background=self._theme.background
        )

        shell = tk.Frame(
            self._root,
            background=self._theme.background,
        )
        shell.pack(
            fill=tk.BOTH,
            expand=True,
        )

        shell.grid_columnconfigure(0, minsize=245)
        shell.grid_columnconfigure(1, weight=1)
        shell.grid_rowconfigure(0, weight=1)

        self._build_sidebar(shell)
        self._build_main_area(shell)

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
            width=245,
            highlightthickness=1,
            highlightbackground=self._theme.border,
        )
        sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        sidebar.grid_propagate(False)

        logo = tk.Frame(
            sidebar,
            background=sidebar["background"],
        )
        logo.pack(
            fill=tk.X,
            padx=20,
            pady=(22, 18),
        )

        tk.Label(
            logo,
            text=DesktopIcon.LOGO.value,
            background=logo["background"],
            foreground=self._theme.success,
            font=("Segoe UI Symbol", 32),
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
            font=("Segoe UI Semibold", 20),
        ).pack(anchor="w")

        tk.Label(
            logo_text,
            text="Diagnostic intelligent",
            background=logo_text["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        navigation = (
            (
                DesktopIcon.DASHBOARD,
                "Tableau de bord",
                True,
            ),
            (
                DesktopIcon.JOURNAL,
                "Journal scientifique",
                False,
            ),
            (
                DesktopIcon.GALLERY,
                "Galerie",
                False,
            ),
            (
                DesktopIcon.PROJECTS,
                "Projets",
                False,
            ),
            (
                DesktopIcon.DIAGNOSTIC,
                "IA & Diagnostic",
                False,
            ),
            (
                DesktopIcon.ANALYSES,
                "Analyses",
                False,
            ),
            (
                DesktopIcon.EXPERIMENTS,
                "Expériences",
                False,
            ),
            (
                DesktopIcon.LEARNING,
                "Apprentissage",
                False,
            ),
            (
                DesktopIcon.STATISTICS,
                "Statistiques",
                False,
            ),
            (
                DesktopIcon.COMMUNITY,
                "Communauté",
                False,
            ),
            (
                DesktopIcon.DONATIONS,
                "Dons",
                False,
            ),
            (
                DesktopIcon.SHOP,
                "Boutique",
                False,
            ),
            (
                DesktopIcon.SETTINGS,
                "Paramètres",
                False,
            ),
        )

        navigation_frame = tk.Frame(
            sidebar,
            background=sidebar["background"],
        )
        navigation_frame.pack(
            fill=tk.X,
            padx=12,
        )

        for icon, label, selected in navigation:
            self._navigation_button(
                navigation_frame,
                icon=icon,
                label=label,
                selected=selected,
            )

        spacer = tk.Frame(
            sidebar,
            background=sidebar["background"],
        )
        spacer.pack(
            fill=tk.BOTH,
            expand=True,
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
                font=("Segoe UI Symbol", 16),
                padx=9,
            ).pack(side=tk.LEFT)

    def _navigation_button(
        self,
        parent: tk.Widget,
        *,
        icon: DesktopIcon,
        label: str,
        selected: bool,
    ) -> None:
        """Build one sidebar navigation item."""
        background = (
            self._blend(
                self._theme.success,
                self._theme.background,
                0.25,
            )
            if selected
            else parent["background"]
        )

        foreground = (
            self._theme.text_primary
            if selected
            else self._theme.text_secondary
        )

        button = tk.Label(
            parent,
            text=icon_text(icon, label),
            anchor="w",
            background=background,
            foreground=foreground,
            font=("Segoe UI Semibold" if selected else "Segoe UI", 10),
            padx=14,
            pady=10,
            cursor="hand2",
        )
        button.pack(
            fill=tk.X,
            pady=2,
        )

    def _build_progress_card(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the progression card."""
        progress = self._view_model.progress

        card = self._card(
            parent,
            padding=14,
        )
        card.pack(
            fill=tk.X,
            padx=14,
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
            font=("Segoe UI Symbol", 25),
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
            font=("Segoe UI Semibold", 12),
        ).pack(anchor="w")

        tk.Label(
            text,
            text=progress.title,
            background=text["background"],
            foreground=self._theme.success,
            font=("Segoe UI", 9),
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
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        tk.Label(
            footer,
            text=f"{progress.progress_percent}%",
            background=footer["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 9),
        ).pack(side=tk.RIGHT)

    def _build_engine_card(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the operational-engine status card."""
        card = self._card(
            parent,
            padding=14,
        )
        card.pack(
            fill=tk.X,
            padx=14,
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
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(fill=tk.X)

        tk.Label(
            card,
            text="Tous les systèmes actifs",
            background=card["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(
            fill=tk.X,
            pady=(4, 0),
        )

    def _build_main_area(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build scrollable main dashboard area."""
        container = tk.Frame(
            parent,
            background=self._theme.background,
        )
        container.grid(
            row=0,
            column=1,
            sticky="nsew",
        )
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            container,
            background=self._theme.background,
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            container,
            orient=tk.VERTICAL,
            command=canvas.yview,
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        body = tk.Frame(
            canvas,
            background=self._theme.background,
        )

        window_id = canvas.create_window(
            (0, 0),
            window=body,
            anchor="nw",
        )

        body.bind(
            "<Configure>",
            lambda _event: canvas.configure(
                scrollregion=canvas.bbox("all")
            ),
        )

        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                window_id,
                width=event.width,
            ),
        )

        body.grid_columnconfigure(0, weight=1)

        self._gallery_images.clear()

        self._build_header(body)
        self._build_metric_row(body)
        self._build_analysis_row(body)
        self._build_activity_row(body)
        self._build_gallery(body)
        self._build_memories(body)
        self._build_footer(body)

    def _build_header(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build the aquarium-inspired project hero."""
        hero = tk.Frame(
            parent,
            background=self._blend(
                self._theme.surface,
                self._theme.success,
                0.10,
            ),
            height=145,
            highlightthickness=1,
            highlightbackground=self._theme.border,
        )
        hero.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(18, 14),
        )
        hero.grid_propagate(False)

        hero.grid_columnconfigure(0, weight=1)

        left = tk.Frame(
            hero,
            background=hero["background"],
        )
        left.grid(
            row=0,
            column=0,
            sticky="nw",
            padx=24,
            pady=20,
        )

        tk.Label(
            left,
            text=self._view_model.project_name,
            background=left["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 26),
        ).pack(anchor="w")

        tk.Label(
            left,
            text=(
                f"{DesktopIcon.STATUS.value}  "
                f"{self._view_model.status_title}"
            ),
            background=left["background"],
            foreground=self._theme.success,
            font=("Segoe UI Semibold", 10),
        ).pack(
            anchor="w",
            pady=(8, 0),
        )

        tk.Label(
            left,
            text=self._view_model.description,
            background=left["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 10),
            wraplength=620,
            justify=tk.LEFT,
        ).pack(
            anchor="w",
            pady=(8, 0),
        )

        right = tk.Frame(
            hero,
            background=hero["background"],
        )
        right.grid(
            row=0,
            column=1,
            sticky="ne",
            padx=24,
            pady=20,
        )

        theme_variable = tk.StringVar(
            value=self._theme.display_name
        )

        theme_menu = tk.OptionMenu(
            right,
            theme_variable,
            *tuple(self._theme_name_by_display),
        )

        def handle_theme_change(
            *_arguments: str,
        ) -> None:
            self._change_theme(
                theme_variable.get()
            )

        theme_variable.trace_add(
            "write",
            handle_theme_change,
        )
        theme_menu.configure(
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.surface,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            font=("Segoe UI", 9),
        )
        theme_menu["menu"].configure(
            background=self._theme.surface,
            foreground=self._theme.text_primary,
            activebackground=self._theme.accent,
        )
        theme_menu.pack(
            anchor="e",
            pady=(0, 10),
        )

        self._action_button(
            right,
            text=icon_text(
                DesktopIcon.EXPORT,
                "Exporter le rapport",
            ),
            accent=self._theme.success,
        ).pack(anchor="e")

    def _build_metric_row(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build top KPI cards."""
        row = tk.Frame(
            parent,
            background=self._theme.background,
        )
        row.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
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
        """Build one colored metric card."""
        accent = self._accent_for_role(
            metric.accent_role
        )

        card = tk.Frame(
            parent,
            background=self._blend(
                self._theme.surface,
                accent,
                0.12,
            ),
            highlightthickness=1,
            highlightbackground=self._blend(
                self._theme.border,
                accent,
                0.35,
            ),
            padx=16,
            pady=14,
        )

        header = tk.Frame(
            card,
            background=card["background"],
        )
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text=metric.label,
            background=header["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 10),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text=metric.symbol,
            background=self._blend(
                card["background"],
                accent,
                0.35,
            ),
            foreground=accent,
            font=("Segoe UI Symbol", 18),
            padx=10,
            pady=6,
        ).pack(side=tk.RIGHT)

        tk.Label(
            card,
            text=metric.value,
            background=card["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 25),
        ).pack(anchor="w")

        tk.Label(
            card,
            text=metric.detail,
            background=card["background"],
            foreground=accent,
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        return card

    def _build_analysis_row(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build causal chain and distribution panels."""
        row = tk.Frame(
            parent,
            background=self._theme.background,
        )
        row.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(14, 0),
        )

        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        chain_card = self._card(row, padding=18)
        chain_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 7),
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
            pady=(18, 5),
        )

        stages = (
            (
                DesktopIcon.OBSERVATION,
                "Observation",
                "Données collectées",
                self._theme.success,
            ),
            (
                DesktopIcon.QUALITY,
                "Qualité",
                "Validation",
                self._theme.accent,
            ),
            (
                DesktopIcon.HYPOTHESIS,
                "Abduction",
                "Hypothèses",
                self._theme.hypothesis,
            ),
            (
                DesktopIcon.EXPERIMENTS,
                "Expériences",
                "Évaluation",
                self._theme.warning,
            ),
            (
                DesktopIcon.CONCLUSION,
                "Conclusion",
                "Apprentissage",
                self._theme.success,
            ),
        )

        for index, (
            icon,
            title,
            subtitle,
            accent,
        ) in enumerate(stages):
            stage = tk.Frame(
                chain,
                background=chain["background"],
            )
            stage.pack(
                side=tk.LEFT,
                fill=tk.BOTH,
                expand=True,
            )

            tk.Label(
                stage,
                text=icon.value,
                background=self._blend(
                    chain["background"],
                    accent,
                    0.22,
                ),
                foreground=accent,
                font=("Segoe UI Symbol", 24),
                padx=15,
                pady=12,
            ).pack()

            tk.Label(
                stage,
                text=title,
                background=stage["background"],
                foreground=accent,
                font=("Segoe UI Semibold", 10),
            ).pack(pady=(8, 2))

            tk.Label(
                stage,
                text=subtitle,
                background=stage["background"],
                foreground=self._theme.text_secondary,
                font=("Segoe UI", 8),
            ).pack()

            if index < len(stages) - 1:
                tk.Label(
                    chain,
                    text=DesktopIcon.ARROW.value,
                    background=chain["background"],
                    foreground=accent,
                    font=("Segoe UI Symbol", 18),
                ).pack(
                    side=tk.LEFT,
                    padx=3,
                )

        distribution = self._card(row, padding=18)
        distribution.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(7, 0),
        )

        self._section_title(
            distribution,
            "Répartition du journal",
        )

        if not self._view_model.event_distribution:
            self._muted_label(
                distribution,
                "Aucune donnée disponible.",
            ).pack(anchor="w", pady=(16, 0))
        else:
            for label, count in (
                self._view_model.event_distribution
            ):
                self._distribution_row(
                    distribution,
                    label,
                    count,
                )

    def _build_activity_row(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build recent activity and recommendation panels."""
        row = tk.Frame(
            parent,
            background=self._theme.background,
        )
        row.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
            pady=(14, 0),
        )

        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=2)

        activity = self._card(row, padding=18)
        activity.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 7),
        )

        self._section_title(
            activity,
            "Observations récentes",
        )

        if not self._view_model.latest_activity:
            self._muted_label(
                activity,
                "Votre activité apparaîtra ici.",
            ).pack(anchor="w", pady=(16, 0))
        else:
            for item in self._view_model.latest_activity[:5]:
                self._activity_item(
                    activity,
                    item,
                )

        recommendation = self._card(
            row,
            padding=18,
        )
        recommendation.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(7, 0),
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
            font=("Segoe UI Semibold", 9),
            padx=10,
            pady=6,
        )
        badge.pack(
            anchor="w",
            pady=(14, 12),
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
            wraplength=360,
        ).pack(
            anchor="w",
            pady=(10, 14),
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
            wraplength=360,
        ).pack(
            anchor="w",
            pady=(8, 14),
        )

        self._action_button(
            recommendation,
            text="Voir toutes les expériences  →",
            accent=self._theme.warning,
        ).pack(fill=tk.X)


    def _build_gallery(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build a real image gallery from project media."""
        card = self._card(
            parent,
            padding=16,
        )
        card.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=20,
            pady=(14, 0),
        )

        header = tk.Frame(
            card,
            background=card["background"],
        )
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Galerie du projet",
            background=header["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 13),
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text=f"{len(self._gallery_items)} image(s)",
            background=header["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
        ).pack(side=tk.RIGHT)

        if not self._gallery_items:
            empty = tk.Frame(
                card,
                background=self._theme.surface_elevated,
                highlightthickness=1,
                highlightbackground=self._theme.border,
                padx=20,
                pady=24,
            )
            empty.pack(
                fill=tk.X,
                pady=(14, 0),
            )

            tk.Label(
                empty,
                text=DesktopIcon.GALLERY.value,
                background=empty["background"],
                foreground=self._theme.accent,
                font=("Segoe UI Symbol", 24),
            ).pack()

            self._muted_label(
                empty,
                "Aucune photo enregistrée dans ce projet.",
            ).pack(pady=(8, 0))

            return

        gallery_row = tk.Frame(
            card,
            background=card["background"],
        )
        gallery_row.pack(
            fill=tk.X,
            pady=(14, 0),
        )

        visible_items = self._gallery_items[:4]

        for index, item in enumerate(visible_items):
            gallery_row.grid_columnconfigure(
                index,
                weight=1,
                uniform="gallery",
            )

            tile = tk.Frame(
                gallery_row,
                background=self._theme.surface_elevated,
                highlightthickness=1,
                highlightbackground=self._theme.border,
                padx=8,
                pady=8,
            )
            tile.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(
                    0 if index == 0 else 5,
                    0
                    if index == len(visible_items) - 1
                    else 5,
                ),
            )

            image_widget = self._gallery_thumbnail(
                tile,
                item,
            )
            image_widget.pack(
                fill=tk.X,
                expand=True,
            )

            tk.Label(
                tile,
                text=item.title,
                background=tile["background"],
                foreground=self._theme.text_primary,
                font=("Segoe UI Semibold", 9),
                anchor="w",
            ).pack(
                fill=tk.X,
                pady=(9, 2),
            )

            tk.Label(
                tile,
                text=(
                    f"{item.date_label}  ·  "
                    f"{item.size_label}"
                ),
                background=tile["background"],
                foreground=self._theme.text_secondary,
                font=("Segoe UI", 8),
                anchor="w",
            ).pack(fill=tk.X)

        actions = tk.Frame(
            card,
            background=card["background"],
        )
        actions.pack(
            fill=tk.X,
            pady=(14, 0),
        )

        self._action_button(
            actions,
            text=icon_text(
                DesktopIcon.ADD,
                "Ajouter une photo",
            ),
            accent=self._theme.success,
        ).pack(side=tk.LEFT)

        self._action_button(
            actions,
            text=icon_text(
                DesktopIcon.GALLERY,
                "Ouvrir la galerie",
            ),
            accent=self._theme.accent,
        ).pack(
            side=tk.RIGHT,
        )

    def _gallery_thumbnail(
        self,
        parent: tk.Widget,
        item: MediaGalleryItem,
    ) -> tk.Widget:
        """Create one thumbnail or a graceful placeholder."""
        try:
            with Image.open(item.path) as source:
                image = source.convert("RGB")
                image.thumbnail(
                    (260, 145),
                    Image.Resampling.LANCZOS,
                )

                canvas_image = Image.new(
                    "RGB",
                    (260, 145),
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
                height=145,
            )
            placeholder.pack_propagate(False)

            tk.Label(
                placeholder,
                text=DesktopIcon.GALLERY.value,
                background=placeholder["background"],
                foreground=self._theme.accent,
                font=("Segoe UI Symbol", 28),
            ).pack(expand=True)

            return placeholder

    def _build_memories(
        self,
        parent: tk.Widget,
    ) -> None:
        """Build remembered milestones."""
        card = self._card(
            parent,
            padding=16,
        )
        card.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=20,
            pady=(14, 0),
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
            fill=tk.X,
            pady=(12, 0),
        )

        memories = self._view_model.memories

        for memory in memories:
            self._memory_card(
                row,
                memory,
            ).pack(
                side=tk.LEFT,
                fill=tk.BOTH,
                expand=True,
                padx=(0, 8),
            )

        add_card = tk.Frame(
            row,
            background=self._theme.surface_elevated,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=16,
            pady=16,
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
            font=("Segoe UI", 20),
        ).pack()

        self._muted_label(
            add_card,
            "Ajouter un souvenir",
        ).pack()

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
            row=6,
            column=0,
            sticky="ew",
            padx=24,
            pady=(12, 18),
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
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        tk.Label(
            footer,
            text="●  EcoBiome Desktop Prototype v0.27",
            background=footer["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 8),
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
            pady=7,
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
            font=("Segoe UI Symbol", 13),
            padx=8,
            pady=6,
        ).pack(side=tk.LEFT)

        text = tk.Frame(
            row,
            background=row["background"],
        )
        text.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(10, 0),
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
            font=("Segoe UI Semibold", 8),
            padx=8,
            pady=4,
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
            font=("Segoe UI Semibold", 10),
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
        card = tk.Frame(
            parent,
            background=self._theme.surface_elevated,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=14,
            pady=12,
        )

        tk.Label(
            card,
            text=memory.symbol,
            background=card["background"],
            foreground=self._theme.success,
            font=("Segoe UI Symbol", 18),
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
    ) -> tk.Frame:
        """Create one standard surface card."""
        return tk.Frame(
            parent,
            background=self._theme.surface,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=padding,
            pady=padding,
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
            font=("Segoe UI Semibold", 13),
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
            font=(
                "Segoe UI Semibold"
                if strong
                else "Segoe UI",
                10,
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
            font=("Segoe UI", 9),
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
            font=("Segoe UI Semibold", 9),
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
        """Apply one selected visual theme."""
        identifier = self._theme_name_by_display[
            display_name
        ]

        self._theme = get_desktop_theme(identifier)

        for child in self._root.winfo_children():
            child.destroy()

        self._build_interface()

        if self._on_theme_changed is not None:
            self._on_theme_changed(identifier)

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
    initial_theme: ThemeIdentifier = (
        ThemeIdentifier.ECOBIOME_NIGHT
    ),
) -> None:
    """Create and run the EcoBiome desktop dashboard."""
    EcoBiomeDesktopApp(
        view_model,
        gallery_items=gallery_items,
        initial_theme=initial_theme,
    ).run()
