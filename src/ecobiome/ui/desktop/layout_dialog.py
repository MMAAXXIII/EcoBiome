"""Tkinter dialog for advanced dashboard customization."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox

from ecobiome.ui.desktop.layout import (
    DashboardLayoutPreferences,
    DashboardLayoutPreset,
    DashboardLayoutStore,
    DashboardSection,
    dashboard_layout_for_preset,
    identify_dashboard_layout_preset,
)
from ecobiome.ui.desktop.theme import DesktopTheme

_CUSTOM_PROFILE_LABEL = "Personnalisée"


class DashboardLayoutDialog(tk.Toplevel):
    """Edit dashboard order, visibility and profiles."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        *,
        preferences: DashboardLayoutPreferences,
        theme: DesktopTheme,
        on_apply: Callable[
            [DashboardLayoutPreferences],
            None,
        ],
    ) -> None:
        super().__init__(
            parent,
            background=theme.background,
        )

        self._theme = theme
        self._working_preferences = preferences
        self._on_apply = on_apply

        self._history = [
            preferences
        ]
        self._history_index = 0

        self._row_frames: dict[
            DashboardSection,
            tk.Frame,
        ] = {}

        self._drag_section: (
            DashboardSection | None
        ) = None

        self._drag_target_index: int | None = None

        self._preset_trace_suspended = False

        self._preset_by_label = {
            preset.display_name: preset
            for preset in DashboardLayoutPreset
        }

        self._preset_variable = tk.StringVar(
            master=self,
            value=self._profile_label(
                preferences
            ),
        )

        self._preset_variable.trace_add(
            "write",
            self._on_preset_changed,
        )

        self.title(
            "Personnaliser le tableau de bord"
        )

        self.geometry("680x610")
        self.minsize(590, 520)
        self.resizable(True, True)

        self.transient(parent)

        self.protocol(
            "WM_DELETE_WINDOW",
            self.destroy,
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self._build_header()

        self._rows = tk.Frame(
            self,
            background=theme.background,
            padx=18,
            pady=8,
        )

        self._rows.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self._build_footer()
        self._render_rows()
        self._refresh_controls()

        self.bind(
            "<Control-z>",
            self._undo_shortcut,
        )

        self.bind(
            "<Control-y>",
            self._redo_shortcut,
        )

        self.bind(
            "<Control-Z>",
            self._redo_shortcut,
        )

        self.bind(
            "<Control-0>",
            self._reset_shortcut,
        )

        self.grab_set()
        self.focus_set()

    def _build_header(self) -> None:
        """Build title, profile and history controls."""
        header = tk.Frame(
            self,
            background=self._theme.surface,
            padx=20,
            pady=18,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        tk.Label(
            header,
            text="Organisation du tableau de bord",
            background=header["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 15),
        ).pack(anchor="w")

        tk.Label(
            header,
            text=(
                "Choisissez un profil ou déplacez "
                "directement les sections."
            ),
            background=header["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
            pady=(6, 0),
        )

        controls = tk.Frame(
            header,
            background=header["background"],
        )

        controls.pack(
            fill=tk.X,
            pady=(16, 0),
        )

        tk.Label(
            controls,
            text="Profil",
            background=controls["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        profile_labels = tuple(
            self._preset_by_label
        )

        profile_menu = tk.OptionMenu(
            controls,
            self._preset_variable,
            profile_labels[0],
            *profile_labels[1:],
        )

        profile_menu.configure(
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            highlightthickness=0,
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            cursor="hand2",
        )

        profile_menu["menu"].configure(
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.accent,
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9),
        )

        profile_menu.pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        self._reset_button = self._toolbar_button(
            controls,
            text="Disposition complète",
            command=self._reset_default,
        )

        self._reset_button.pack(
            side=tk.RIGHT,
        )

        self._redo_button = self._toolbar_button(
            controls,
            text="Rétablir",
            command=self._redo,
        )

        self._redo_button.pack(
            side=tk.RIGHT,
            padx=(0, 7),
        )

        self._undo_button = self._toolbar_button(
            controls,
            text="Annuler",
            command=self._undo,
        )

        self._undo_button.pack(
            side=tk.RIGHT,
            padx=(0, 7),
        )

    def _build_footer(self) -> None:
        """Build import, export and apply controls."""
        footer = tk.Frame(
            self,
            background=self._theme.surface,
            padx=20,
            pady=14,
        )

        footer.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        tk.Button(
            footer,
            text="Importer JSON",
            command=self._import_layout,
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            padx=13,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.LEFT)

        tk.Button(
            footer,
            text="Exporter JSON",
            command=self._export_layout,
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            padx=13,
            pady=8,
            cursor="hand2",
        ).pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        tk.Button(
            footer,
            text="Fermer",
            command=self.destroy,
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        tk.Button(
            footer,
            text="Appliquer et enregistrer",
            command=self._apply,
            background=self._theme.accent,
            foreground="#FFFFFF",
            activebackground=self._theme.accent,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        ).pack(
            side=tk.RIGHT,
            padx=(0, 10),
        )

    def _render_rows(self) -> None:
        """Render editable and draggable section rows."""
        for child in self._rows.winfo_children():
            child.destroy()

        self._row_frames.clear()

        for index, section in enumerate(
            self._working_preferences.order
        ):
            self._build_section_row(
                index=index,
                section=section,
            )

    def _build_section_row(
        self,
        *,
        index: int,
        section: DashboardSection,
    ) -> None:
        """Build one draggable section row."""
        visible = (
            section
            not in self._working_preferences.hidden_sections
        )

        row = tk.Frame(
            self._rows,
            background=self._theme.surface,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=12,
            pady=11,
        )

        row.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self._row_frames[
            section
        ] = row

        drag_handle = tk.Label(
            row,
            text="⋮⋮",
            background=row["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI Semibold", 13),
            cursor="fleur",
            padx=4,
        )

        drag_handle.pack(side=tk.LEFT)

        drag_handle.bind(
            "<ButtonPress-1>",
            self._make_drag_start_callback(
                section
            ),
        )

        drag_handle.bind(
            "<B1-Motion>",
            self._drag_motion,
        )

        drag_handle.bind(
            "<ButtonRelease-1>",
            self._finish_drag,
        )

        position = tk.Label(
            row,
            text=str(index + 1),
            width=3,
            background=self._theme.surface_elevated,
            foreground=self._theme.accent,
            font=("Segoe UI Semibold", 10),
            padx=4,
            pady=4,
        )

        position.pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        tk.Label(
            row,
            text=section.display_name,
            background=row["background"],
            foreground=(
                self._theme.text_primary
                if visible
                else self._theme.text_secondary
            ),
            font=("Segoe UI Semibold", 10),
        ).pack(
            side=tk.LEFT,
            padx=(12, 0),
        )

        tk.Button(
            row,
            text=(
                "Visible"
                if visible
                else "Masquée"
            ),
            command=partial(
                self._toggle_visibility,
                section,
            ),
            background=(
                self._theme.success
                if visible
                else self._theme.surface_elevated
            ),
            foreground=(
                "#FFFFFF"
                if visible
                else self._theme.text_secondary
            ),
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        tk.Button(
            row,
            text="↓",
            command=partial(
                self._move,
                section,
                1,
            ),
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            width=3,
            cursor="hand2",
        ).pack(
            side=tk.RIGHT,
            padx=(0, 6),
        )

        tk.Button(
            row,
            text="↑",
            command=partial(
                self._move,
                section,
                -1,
            ),
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            width=3,
            cursor="hand2",
        ).pack(
            side=tk.RIGHT,
            padx=(0, 6),
        )

    def _make_drag_start_callback(
        self,
        section: DashboardSection,
    ) -> Callable[[tk.Event], None]:
        """Create one typed drag-start callback."""
        def callback(
            event: tk.Event,
        ) -> None:
            self._start_drag(
                section,
                event,
            )

        return callback

    def _start_drag(
        self,
        section: DashboardSection,
        _event: tk.Event,
    ) -> None:
        """Start dragging one dashboard section."""
        self._drag_section = section

        self._drag_target_index = (
            self._working_preferences.order.index(
                section
            )
        )

        self._render_drag_target()

    def _drag_motion(
        self,
        event: tk.Event,
    ) -> None:
        """Update the target index during dragging."""
        if self._drag_section is None:
            return

        target_index = (
            len(
                self._working_preferences.order
            )
            - 1
        )

        for index, section in enumerate(
            self._working_preferences.order
        ):
            row = self._row_frames[
                section
            ]

            midpoint = (
                row.winfo_rooty()
                + row.winfo_height() / 2
            )

            if event.y_root < midpoint:
                target_index = index
                break

        if (
            target_index
            != self._drag_target_index
        ):
            self._drag_target_index = (
                target_index
            )

            self._render_drag_target()

    def _finish_drag(
        self,
        _event: tk.Event,
    ) -> None:
        """Apply the final position of a dragged section."""
        section = self._drag_section
        target_index = self._drag_target_index

        self._drag_section = None
        self._drag_target_index = None

        if (
            section is None
            or target_index is None
        ):
            self._render_rows()
            return

        updated = (
            self._working_preferences.move_to(
                section,
                target_index,
            )
        )

        if updated == self._working_preferences:
            self._render_rows()
            return

        self._set_preferences(
            updated
        )

    def _render_drag_target(self) -> None:
        """Highlight the current drag destination."""
        for index, section in enumerate(
            self._working_preferences.order
        ):
            row = self._row_frames[
                section
            ]

            selected = (
                index
                == self._drag_target_index
            )

            row.configure(
                highlightbackground=(
                    self._theme.accent
                    if selected
                    else self._theme.border
                ),
                highlightthickness=(
                    2
                    if selected
                    else 1
                ),
            )

    def _move(
        self,
        section: DashboardSection,
        offset: int,
    ) -> None:
        """Move one section and record history."""
        self._set_preferences(
            self._working_preferences.move(
                section,
                offset,
            )
        )

    def _toggle_visibility(
        self,
        section: DashboardSection,
    ) -> None:
        """Toggle visibility and record history."""
        self._set_preferences(
            self._working_preferences.toggle_visibility(
                section
            )
        )

    def _set_preferences(
        self,
        preferences: DashboardLayoutPreferences,
        *,
        record_history: bool = True,
    ) -> None:
        """Apply working preferences and refresh controls."""
        if preferences == self._working_preferences:
            self._update_profile_label()
            self._refresh_controls()
            return

        self._working_preferences = preferences

        if record_history:
            self._history = self._history[
                : self._history_index + 1
            ]

            self._history.append(
                preferences
            )

            self._history_index = (
                len(self._history) - 1
            )

        self._update_profile_label()
        self._render_rows()
        self._refresh_controls()

    def _undo(self) -> None:
        """Restore the previous layout state."""
        if self._history_index == 0:
            return

        self._history_index -= 1

        self._set_preferences(
            self._history[
                self._history_index
            ],
            record_history=False,
        )

    def _redo(self) -> None:
        """Restore the next layout state."""
        if (
            self._history_index
            >= len(self._history) - 1
        ):
            return

        self._history_index += 1

        self._set_preferences(
            self._history[
                self._history_index
            ],
            record_history=False,
        )

    def _reset_default(self) -> None:
        """Restore the complete default profile."""
        self._set_preferences(
            dashboard_layout_for_preset(
                DashboardLayoutPreset.COMPLETE
            )
        )

    def _on_preset_changed(
        self,
        _variable_name: str,
        _index: str,
        _operation: str,
    ) -> None:
        """Apply a profile selected from the menu."""
        if self._preset_trace_suspended:
            return

        selected_label = (
            self._preset_variable.get()
        )

        preset = self._preset_by_label.get(
            selected_label
        )

        if preset is None:
            return

        self._set_preferences(
            dashboard_layout_for_preset(
                preset
            )
        )

    def _profile_label(
        self,
        preferences: DashboardLayoutPreferences,
    ) -> str:
        """Return the matching profile or custom label."""
        preset = identify_dashboard_layout_preset(
            preferences
        )

        if preset is None:
            return _CUSTOM_PROFILE_LABEL

        return preset.display_name

    def _update_profile_label(self) -> None:
        """Synchronize the profile selector."""
        self._preset_trace_suspended = True

        try:
            self._preset_variable.set(
                self._profile_label(
                    self._working_preferences
                )
            )

        finally:
            self._preset_trace_suspended = False

    def _refresh_controls(self) -> None:
        """Update undo and redo availability."""
        self._undo_button.configure(
            state=(
                tk.NORMAL
                if self._history_index > 0
                else tk.DISABLED
            )
        )

        self._redo_button.configure(
            state=(
                tk.NORMAL
                if (
                    self._history_index
                    < len(self._history) - 1
                )
                else tk.DISABLED
            )
        )

    def _import_layout(self) -> None:
        """Import dashboard preferences from JSON."""
        selected_path = filedialog.askopenfilename(
            parent=self,
            title="Importer une disposition",
            filetypes=(
                (
                    "Disposition EcoBiome",
                    "*.json",
                ),
                (
                    "Tous les fichiers",
                    "*.*",
                ),
            ),
        )

        if not selected_path:
            return

        store = DashboardLayoutStore(
            path=Path(selected_path)
        )

        try:
            preferences = store.load()

        except (OSError, TypeError, ValueError) as error:
            messagebox.showerror(
                "Import impossible",
                str(error),
                parent=self,
            )
            return

        self._set_preferences(
            preferences
        )

    def _export_layout(self) -> None:
        """Export current preferences to JSON."""
        selected_path = filedialog.asksaveasfilename(
            parent=self,
            title="Exporter la disposition",
            defaultextension=".json",
            initialfile="ecobiome-dashboard-layout.json",
            filetypes=(
                (
                    "Disposition EcoBiome",
                    "*.json",
                ),
                (
                    "Tous les fichiers",
                    "*.*",
                ),
            ),
        )

        if not selected_path:
            return

        store = DashboardLayoutStore(
            path=Path(selected_path)
        )

        try:
            store.save(
                self._working_preferences
            )

        except OSError as error:
            messagebox.showerror(
                "Export impossible",
                str(error),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Disposition exportée",
            "Le profil a été enregistré avec succès.",
            parent=self,
        )

    def _apply(self) -> None:
        """Apply preferences and close."""
        self._on_apply(
            self._working_preferences
        )

        self.destroy()

    def _undo_shortcut(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle Ctrl+Z."""
        self._undo()
        return "break"

    def _redo_shortcut(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle Ctrl+Y or Ctrl+Shift+Z."""
        self._redo()
        return "break"

    def _reset_shortcut(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle Ctrl+0."""
        self._reset_default()
        return "break"

    def _toolbar_button(
        self,
        parent: tk.Widget,
        *,
        text: str,
        command: Callable[[], None],
    ) -> tk.Button:
        """Create one toolbar button."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            disabledforeground=self._theme.text_secondary,
            relief=tk.FLAT,
            padx=11,
            pady=6,
            cursor="hand2",
        )
