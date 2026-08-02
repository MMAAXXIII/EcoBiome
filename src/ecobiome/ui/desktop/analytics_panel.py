"""Interactive Tkinter diagnostic-analytics panel."""

from __future__ import annotations

import tkinter as tk

from ecobiome.ui.desktop.analytics import (
    DiagnosticAnalyticsViewModel,
    HypothesisDetailViewModel,
)
from ecobiome.ui.desktop.charts import (
    ProbabilityBar,
    draw_line_chart,
    draw_probability_bar,
    draw_quality_donut,
)
from ecobiome.ui.desktop.theme import DesktopTheme


class DiagnosticAnalyticsPanel(tk.Frame):
    """Display quality charts and interactive hypotheses."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        view_model: DiagnosticAnalyticsViewModel,
        theme: DesktopTheme,
    ) -> None:
        super().__init__(
            parent,
            background=theme.background,
        )

        self._view_model = view_model
        self._theme = theme
        self._selected_identifier: str | None = None
        self._detail_title: tk.Label | None = None
        self._detail_probability: tk.Label | None = None
        self._detail_explanation: tk.Label | None = None
        self._detail_recommendation: tk.Label | None = None
        self._hypothesis_rows: dict[str, tk.Frame] = {}

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self._build_quality_section()
        self._build_hypothesis_section()

        if view_model.hypotheses:
            self._select_hypothesis(
                view_model.hypotheses[0].identifier
            )

    def _build_quality_section(self) -> None:
        """Build global-quality and evolution charts."""
        card = self._card(self)
        card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 7),
        )

        self._title(
            card,
            "Qualité des observations",
        ).pack(anchor="w")

        summary = tk.Frame(
            card,
            background=card["background"],
        )
        summary.pack(
            fill=tk.X,
            pady=(12, 4),
        )

        donut = tk.Canvas(
            summary,
            width=205,
            height=205,
            background=card["background"],
            highlightthickness=0,
        )
        donut.pack(side=tk.LEFT)

        def redraw_donut(
            event: tk.Event,
        ) -> None:
            draw_quality_donut(
                donut,
                width=event.width,
                height=event.height,
                score=self._view_model.quality_score,
                background=card["background"],
                track=self._theme.surface_elevated,
                high_quality=self._theme.success,
                medium_quality=self._theme.warning,
                low_quality=self._theme.danger,
                rejected="#7A8490",
                text_color=self._theme.text_primary,
                secondary_text_color=(
                    self._theme.text_secondary
                ),
            )

        donut.bind(
            "<Configure>",
            redraw_donut,
        )

        legend = tk.Frame(
            summary,
            background=card["background"],
        )
        legend.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(14, 0),
            pady=(12, 0),
        )

        legend_items = (
            (
                "Haute qualité",
                self._view_model.high_quality_count,
                self._theme.success,
            ),
            (
                "Qualité moyenne",
                self._view_model.medium_quality_count,
                self._theme.warning,
            ),
            (
                "Faible qualité",
                self._view_model.low_quality_count,
                self._theme.danger,
            ),
            (
                "Rejetées",
                self._view_model.rejected_count,
                "#7A8490",
            ),
        )

        for label, value, accent in legend_items:
            self._legend_row(
                legend,
                label=label,
                value=value,
                accent=accent,
            )

        tk.Label(
            card,
            text="Évolution récente",
            background=card["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 10),
        ).pack(
            anchor="w",
            pady=(12, 4),
        )

        line_chart = tk.Canvas(
            card,
            height=150,
            background=card["background"],
            highlightthickness=0,
        )
        line_chart.pack(
            fill=tk.X,
            expand=True,
        )

        def redraw_line(
            event: tk.Event,
        ) -> None:
            draw_line_chart(
                line_chart,
                width=event.width,
                height=event.height,
                values=self._view_model.quality_history,
                background=card["background"],
                grid=self._theme.border,
                line=self._theme.accent,
                point=self._theme.success,
                text_color=self._theme.text_secondary,
            )

        line_chart.bind(
            "<Configure>",
            redraw_line,
        )

    def _build_hypothesis_section(self) -> None:
        """Build ranked hypotheses and selected detail."""
        card = self._card(self)
        card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(7, 0),
        )

        self._title(
            card,
            "Hypothèses principales",
        ).pack(anchor="w")

        content = tk.Frame(
            card,
            background=card["background"],
        )
        content.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(12, 0),
        )

        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        ranking = tk.Frame(
            content,
            background=card["background"],
        )
        ranking.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
        )

        if not self._view_model.hypotheses:
            tk.Label(
                ranking,
                text="Aucune hypothèse disponible.",
                background=ranking["background"],
                foreground=self._theme.text_secondary,
                font=("Segoe UI", 9),
            ).pack(anchor="w")

        for probability in (
            self._view_model.probability_bars
        ):
            self._build_probability_row(
                ranking,
                probability,
            )

        detail = tk.Frame(
            content,
            background=self._theme.surface_elevated,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=16,
            pady=14,
        )
        detail.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        self._detail_title = tk.Label(
            detail,
            text="Sélectionnez une hypothèse",
            background=detail["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 12),
            justify=tk.LEFT,
            wraplength=300,
        )
        self._detail_title.pack(anchor="w")

        self._detail_probability = tk.Label(
            detail,
            text="",
            background=detail["background"],
            foreground=self._theme.hypothesis,
            font=("Segoe UI Semibold", 22),
        )
        self._detail_probability.pack(
            anchor="w",
            pady=(10, 4),
        )

        tk.Label(
            detail,
            text="Interprétation",
            background=detail["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 9),
        ).pack(
            anchor="w",
            pady=(8, 3),
        )

        self._detail_explanation = tk.Label(
            detail,
            text="",
            background=detail["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            wraplength=300,
        )
        self._detail_explanation.pack(anchor="w")

        tk.Label(
            detail,
            text="Prochaine action",
            background=detail["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 9),
        ).pack(
            anchor="w",
            pady=(16, 3),
        )

        self._detail_recommendation = tk.Label(
            detail,
            text="",
            background=detail["background"],
            foreground=self._theme.success,
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            wraplength=300,
        )
        self._detail_recommendation.pack(anchor="w")

    def _build_probability_row(
        self,
        parent: tk.Widget,
        probability: ProbabilityBar,
    ) -> None:
        """Build one clickable probability row."""
        row = tk.Frame(
            parent,
            background=self._theme.surface_elevated,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=12,
            pady=10,
            cursor="hand2",
        )
        row.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self._hypothesis_rows[
            probability.identifier
        ] = row

        header = tk.Frame(
            row,
            background=row["background"],
            cursor="hand2",
        )
        header.pack(fill=tk.X)

        identifier = tk.Label(
            header,
            text=probability.identifier,
            background=header["background"],
            foreground=probability.accent,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )
        identifier.pack(side=tk.LEFT)

        title = tk.Label(
            header,
            text=probability.label,
            background=header["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )
        title.pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        percentage = tk.Label(
            header,
            text=f"{probability.probability}%",
            background=header["background"],
            foreground=probability.accent,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        )
        percentage.pack(side=tk.RIGHT)

        bar = tk.Canvas(
            row,
            height=7,
            background=row["background"],
            highlightthickness=0,
            cursor="hand2",
        )
        bar.pack(
            fill=tk.X,
            pady=(8, 0),
        )

        def redraw_probability(
            event: tk.Event,
        ) -> None:
            draw_probability_bar(
                bar,
                width=event.width,
                probability=probability.probability,
                background=self._theme.surface,
                foreground=probability.accent,
            )

        bar.bind(
            "<Configure>",
            redraw_probability,
        )

        widgets: tuple[tk.Widget, ...] = (
            row,
            header,
            identifier,
            title,
            percentage,
            bar,
        )

        def select_hypothesis(
            _event: tk.Event,
            *,
            hypothesis_id: str = probability.identifier,
        ) -> None:
            self._select_hypothesis(
                hypothesis_id
            )

        def highlight_hypothesis(
            _event: tk.Event,
            *,
            frame: tk.Frame = row,
        ) -> None:
            self._highlight_row(
                frame,
                True,
            )

        def unhighlight_hypothesis(
            _event: tk.Event,
            *,
            frame: tk.Frame = row,
        ) -> None:
            self._highlight_row(
                frame,
                False,
            )

        for widget in widgets:
            widget.bind(
                "<Button-1>",
                select_hypothesis,
            )

            widget.bind(
                "<Enter>",
                highlight_hypothesis,
            )

            widget.bind(
                "<Leave>",
                unhighlight_hypothesis,
            )

    def _select_hypothesis(
        self,
        identifier: str,
    ) -> None:
        """Select and display one hypothesis."""
        hypothesis = self._view_model.hypothesis(
            identifier
        )

        self._selected_identifier = identifier

        for row_identifier, row in (
            self._hypothesis_rows.items()
        ):
            selected = row_identifier == identifier

            row.configure(
                highlightbackground=(
                    hypothesis.accent
                    if selected
                    else self._theme.border
                ),
                highlightthickness=(
                    2 if selected else 1
                ),
            )

        self._display_hypothesis(hypothesis)

    def _display_hypothesis(
        self,
        hypothesis: HypothesisDetailViewModel,
    ) -> None:
        """Update the selected-hypothesis detail card."""
        if self._detail_title is not None:
            self._detail_title.configure(
                text=(
                    f"{hypothesis.identifier} · "
                    f"{hypothesis.title}"
                )
            )

        if self._detail_probability is not None:
            self._detail_probability.configure(
                text=f"{hypothesis.probability}%",
                foreground=hypothesis.accent,
            )

        if self._detail_explanation is not None:
            self._detail_explanation.configure(
                text=hypothesis.explanation
            )

        if self._detail_recommendation is not None:
            self._detail_recommendation.configure(
                text=hypothesis.recommendation
            )

    def _highlight_row(
        self,
        row: tk.Frame,
        highlighted: bool,
    ) -> None:
        """Apply a lightweight hover state."""
        row.configure(
            background=(
                self._blend(
                    self._theme.surface_elevated,
                    self._theme.accent,
                    0.10,
                )
                if highlighted
                else self._theme.surface_elevated
            )
        )

    def _legend_row(
        self,
        parent: tk.Widget,
        *,
        label: str,
        value: int,
        accent: str,
    ) -> None:
        """Build one quality legend row."""
        row = tk.Frame(
            parent,
            background=parent["background"],
        )
        row.pack(
            fill=tk.X,
            pady=4,
        )

        tk.Label(
            row,
            text="●",
            background=row["background"],
            foreground=accent,
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        tk.Label(
            row,
            text=label,
            background=row["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
        ).pack(
            side=tk.LEFT,
            padx=(6, 0),
        )

        tk.Label(
            row,
            text=str(value),
            background=row["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 9),
        ).pack(side=tk.RIGHT)

    def _card(
        self,
        parent: tk.Widget,
    ) -> tk.Frame:
        """Create one analytics card."""
        return tk.Frame(
            parent,
            background=self._theme.surface,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=18,
            pady=16,
        )

    def _title(
        self,
        parent: tk.Widget,
        text: str,
    ) -> tk.Label:
        """Create one analytics section title."""
        return tk.Label(
            parent,
            text=text,
            background=parent["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 13),
        )

    @staticmethod
    def _blend(
        first: str,
        second: str,
        ratio: float,
    ) -> str:
        """Blend two hexadecimal colors."""
        normalized_ratio = max(
            0.0,
            min(1.0, ratio),
        )

        first_rgb = tuple(
            int(first[index:index + 2], 16)
            for index in (1, 3, 5)
        )

        second_rgb = tuple(
            int(second[index:index + 2], 16)
            for index in (1, 3, 5)
        )

        result = tuple(
            round(
                start
                + (end - start)
                * normalized_ratio
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
