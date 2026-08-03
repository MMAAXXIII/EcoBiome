"""Image-rich project hero for the EcoBiome desktop dashboard."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
import os
from pathlib import Path
from typing import Literal

from PIL import (
    Image,
    ImageDraw,
    ImageOps,
    ImageTk,
)

from ecobiome.ui.desktop.design_tokens import (
    TypographyRole,
    typography_font,
)

_HERO_REFERENCE_PATH = (
    Path(__file__).resolve().parent
    / "assets"
    / "hero_reference.png"
)
from ecobiome.ui.desktop.theme import DesktopTheme

_PANORAMA_MINIMUM_RATIO = 2.15


def _load_rgb_image(
    image_path: Path | None,
) -> Image.Image | None:
    """Load one RGB image without retaining a file handle."""
    if image_path is None:
        return None

    try:
        with Image.open(image_path) as source:
            return source.convert("RGB")

    except OSError:
        return None


def _is_panorama(
    image: Image.Image | None,
) -> bool:
    """Return whether an image can fill the shallow hero safely."""
    if image is None:
        return False

    width, height = image.size

    return (
        height > 0
        and width / height
        >= _PANORAMA_MINIMUM_RATIO
    )


def cover_dimensions(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
) -> tuple[int, int]:
    """Return dimensions that cover the requested target area."""
    dimensions = (
        source_width,
        source_height,
        target_width,
        target_height,
    )

    if any(
        value <= 0
        for value in dimensions
    ):
        raise ValueError(
            "Image dimensions must be positive."
        )

    ratio = max(
        target_width / source_width,
        target_height / source_height,
    )

    return (
        max(
            1,
            round(source_width * ratio),
        ),
        max(
            1,
            round(source_height * ratio),
        ),
    )


def resolve_project_title(
    view_model: object,
) -> str:
    """Extract a stable project title without coupling."""
    for attribute in (
        "project_name",
        "name",
        "title",
    ):
        value = getattr(
            view_model,
            attribute,
            None,
        )

        if (
            isinstance(value, str)
            and value.strip()
        ):
            return value.strip()

    return "Projet EcoBiome"


def resolve_mount_geometry_manager(
    *,
    packed_children: int,
    gridded_children: int,
) -> Literal["pack", "grid"]:
    """Select the geometry manager already used by a container."""
    if (
        packed_children < 0
        or gridded_children < 0
    ):
        raise ValueError(
            "Child counts cannot be negative."
        )

    if packed_children and gridded_children:
        raise ValueError(
            "A Tkinter container cannot mix pack and grid children."
        )

    if gridded_children:
        return "grid"

    return "pack"


def _hex_to_rgb(
    color: str,
) -> tuple[int, int, int]:
    """Convert one hexadecimal color to RGB."""
    return (
        int(color[1:3], 16),
        int(color[3:5], 16),
        int(color[5:7], 16),
    )


def _blend_rgb(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    """Blend two RGB colors."""
    bounded_ratio = max(
        0.0,
        min(1.0, ratio),
    )

    blended = [
        round(
            start
            + (end - start)
            * bounded_ratio
        )
        for start, end in zip(
            first,
            second,
            strict=True,
        )
    ]

    return (
        blended[0],
        blended[1],
        blended[2],
    )


def _normalize_draw_box(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
) -> tuple[int, int, int, int]:
    """Return ImageDraw coordinates ordered on both axes."""
    return (
        min(x0, x1),
        min(y0, y1),
        max(x0, x1),
        max(y0, y1),
    )


def build_aquarium_fallback(
    *,
    width: int,
    height: int,
    theme: DesktopTheme,
) -> Image.Image:
    """Build a deterministic aquarium illustration for an empty gallery."""
    if width <= 0 or height <= 0:
        raise ValueError(
            "Fallback dimensions must be positive."
        )

    top = _hex_to_rgb(
        theme.surface
    )
    bottom = _hex_to_rgb(
        theme.background
    )
    image = Image.new(
        "RGB",
        (width, height),
        top,
    )
    drawing = ImageDraw.Draw(
        image,
        "RGBA",
    )

    for y in range(height):
        ratio = y / max(
            1,
            height - 1,
        )
        gradient_color = _blend_rgb(
            top,
            bottom,
            ratio,
        )
        drawing.line(
            (0, y, width, y),
            fill=(*gradient_color, 255),
        )

    # Add a subtle light band and water shimmer for depth.
    highlight = Image.new(
        "RGBA",
        (width, height),
        (255, 255, 255, 0),
    )
    highlight_draw = ImageDraw.Draw(
        highlight,
        "RGBA",
    )
    highlight_draw.ellipse(
        (
            round(width * 0.48),
            round(height * 0.01),
            round(width * 0.98),
            round(height * 0.30),
        ),
        fill=(255, 255, 255, 22),
    )

    for wave_index in range(6):
        baseline = round(height * (0.08 + wave_index * 0.045))
        wave_length = round(width * 0.16)
        alpha = max(6, 22 - wave_index * 3)
        for x_offset in range(-wave_length, width + wave_length, wave_length * 2):
            highlight_draw.line(
                (
                    x_offset,
                    baseline,
                    x_offset + wave_length,
                    baseline,
                ),
                fill=(255, 255, 255, alpha),
                width=1,
            )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        highlight,
    ).convert("RGB")

    floor_y = round(
        height * 0.82
    )
    drawing = ImageDraw.Draw(
        image,
        "RGBA",
    )
    drawing.rectangle(
        (0, floor_y, width, height),
        fill=(4, 25, 24, 235),
    )

    plant_positions = (
        0.48,
        0.57,
        0.67,
        0.78,
        0.90,
    )

    for plant_index, position in enumerate(
        plant_positions
    ):
        x = round(
            width * position
        )
        stem_height = round(
            height
            * (
                0.34
                + plant_index * 0.055
            )
        )
        stem_top = floor_y - stem_height
        stem_color = (
            44,
            132 + plant_index * 10,
            77,
            225,
        )
        drawing.line(
            (x, floor_y, x, stem_top),
            fill=stem_color,
            width=max(
                2,
                width // 700,
            ),
        )

        for leaf_index in range(5):
            leaf_y = floor_y - round(
                stem_height
                * (
                    0.18
                    + leaf_index * 0.16
                )
            )
            leaf_width = max(
                12,
                width // 70,
            )
            leaf_height = max(
                7,
                height // 22,
            )
            direction = (
                -1
                if leaf_index % 2 == 0
                else 1
            )
            drawing.ellipse(
                _normalize_draw_box(
                    x + direction * 2,
                    leaf_y - leaf_height,
                    x + direction * leaf_width,
                    leaf_y + leaf_height,
                ),
                fill=(
                    38,
                    146 + plant_index * 8,
                    72,
                    145,
                ),
            )

    bubble_positions = (
        (0.61, 0.25, 6),
        (0.66, 0.13, 4),
        (0.74, 0.31, 8),
        (0.84, 0.18, 5),
        (0.92, 0.36, 7),
    )

    for x_ratio, y_ratio, radius in bubble_positions:
        x = round(
            width * x_ratio
        )
        y = round(
            height * y_ratio
        )
        drawing.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            ),
            outline=(
                180,
                238,
                230,
                150,
            ),
            width=2,
        )

    fish_specs = (
        (0.55, 0.30, 1.0, (239, 128, 45, 235)),
        (0.69, 0.48, 0.78, (90, 196, 242, 235)),
        (0.82, 0.28, 0.90, (244, 94, 57, 235)),
        (0.90, 0.57, 0.66, (234, 173, 45, 225)),
    )

    for x_ratio, y_ratio, scale, fish_color in fish_specs:
        center_x = round(
            width * x_ratio
        )
        center_y = round(
            height * y_ratio
        )
        body_width = max(
            42,
            round(width * 0.065 * scale),
        )
        body_height = max(
            18,
            round(height * 0.16 * scale),
        )
        tail_width = round(
            body_width * 0.42
        )

        drawing.ellipse(
            (
                center_x - body_width // 2,
                center_y - body_height // 2,
                center_x + body_width // 2,
                center_y + body_height // 2,
            ),
            fill=fish_color,
            outline=(255, 220, 135, 150),
            width=1,
        )
        drawing.polygon(
            (
                (
                    center_x + body_width // 2 - 2,
                    center_y,
                ),
                (
                    center_x + body_width // 2 + tail_width,
                    center_y - body_height // 2,
                ),
                (
                    center_x + body_width // 2 + tail_width,
                    center_y + body_height // 2,
                ),
            ),
            fill=(
                fish_color[0],
                fish_color[1],
                fish_color[2],
                190,
            ),
        )
        eye_radius = max(
            2,
            body_height // 10,
        )
        drawing.ellipse(
            (
                center_x - body_width // 3 - eye_radius,
                center_y - eye_radius,
                center_x - body_width // 3 + eye_radius,
                center_y + eye_radius,
            ),
            fill=(245, 250, 250, 255),
        )
        drawing.ellipse(
            (
                center_x - body_width // 3 - 1,
                center_y - 1,
                center_x - body_width // 3 + 2,
                center_y + 2,
            ),
            fill=(2, 10, 12, 255),
        )

    return image


def select_hero_image_path(
    paths: tuple[Path, ...],
) -> Path | None:
    """Select the project image whose ratio best suits a wide hero."""
    candidates: list[
        tuple[float, int, float, Path]
    ] = []

    for path in paths:
        candidate = Path(path)

        if not candidate.is_file():
            continue

        try:
            with Image.open(candidate) as source:
                width, height = source.size

        except OSError:
            continue

        if width <= 0 or height <= 0:
            continue

        ratio = width / height
        target_ratio = 3.2
        ratio_distance = abs(
            ratio - target_ratio
        )
        area = width * height

        candidates.append(
            (
                ratio_distance,
                -area,
                -ratio,
                candidate,
            )
        )

    if os.environ.get("ECOBIOME_USE_HERO_REFERENCE") == "1" and _HERO_REFERENCE_PATH.is_file():
        return _HERO_REFERENCE_PATH

    if candidates:
        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
                str(item[3]).casefold(),
            )
        )

        return candidates[0][3]

    return None


class DashboardHeroBanner(tk.Frame):
    """Display a project banner backed by real or generated imagery."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: DesktopTheme,
        title: str,
        image_path: Path | None,
        on_open_gallery: Callable[[], None],
        on_export_report: Callable[[], None] | None = None,
        subtitle: str = (
            "Diagnostic intelligent · observations, "
            "hypothèses et expériences"
        ),
        on_customize_layout: Callable[[], None] | None = None,
        theme_names: tuple[str, ...] = (),
        current_theme: str | None = None,
        on_theme_changed: Callable[[str], None] | None = None,
        on_minimize_window: Callable[[], None] | None = None,
        on_toggle_maximize_window: Callable[[], None] | None = None,
        on_close_window: Callable[[], None] | None = None,
        visual_scale: float = 1.0,
    ) -> None:
        if visual_scale <= 0:
            raise ValueError(
                "Hero visual scale must be positive."
            )

        self._visual_scale = visual_scale
        hero_height = self._px(180)
        super().__init__(
            parent,
            background=theme.background,
            height=hero_height,
        )
        self._container = parent
        self._theme = theme
        self._title = title
        self._subtitle = subtitle
        self._image_path = image_path
        self._source_image: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._disposed = False
        self._initial_redraw_completed = False
        self._initial_redraw_after_id: str | None = None
        self._redraw_after_id: str | None = None
        self._theme_trace_id: str | None = None

        window_callbacks = (
            on_minimize_window,
            on_toggle_maximize_window,
            on_close_window,
        )

        if any(window_callbacks) and not all(window_callbacks):
            raise ValueError(
                "Integrated window controls require all callbacks."
            )

        self.grid_propagate(
            False
        )
        self.grid_columnconfigure(
            0,
            weight=1,
        )
        self.grid_rowconfigure(
            0,
            weight=1,
        )

        self._canvas = tk.Canvas(
            self,
            background=theme.surface,
            borderwidth=0,
            highlightthickness=0,
            height=hero_height,
        )
        self._canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self._toolbar = tk.Frame(
            self._canvas,
            background=theme.surface,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=theme.border,
            padx=self._px(5),
            pady=self._px(5),
        )
        self._primary_actions = tk.Frame(
            self._toolbar,
            background=theme.surface,
        )
        self._primary_actions.pack(fill=tk.X)

        self._window_controls: tk.Frame | None = None
        if all(window_callbacks):
            assert on_minimize_window is not None
            assert on_toggle_maximize_window is not None
            assert on_close_window is not None
            self._window_controls = tk.Frame(
                self._primary_actions,
                background=theme.surface,
            )
            self._window_controls.pack(
                side=tk.RIGHT,
                padx=(self._px(5), 0),
            )

            window_button_specifications = (
                (
                    "−",
                    on_minimize_window,
                    theme.text_secondary,
                    theme.surface_elevated,
                ),
                (
                    "□",
                    on_toggle_maximize_window,
                    theme.text_primary,
                    theme.surface_elevated,
                ),
                (
                    "×",
                    on_close_window,
                    theme.text_primary,
                    theme.danger,
                ),
            )

            for (
                symbol,
                callback,
                foreground,
                active_background,
            ) in window_button_specifications:
                tk.Button(
                    self._window_controls,
                    text=symbol,
                    command=callback,
                    takefocus=True,
                    background=theme.surface,
                    foreground=foreground,
                    activebackground=active_background,
                    activeforeground=theme.text_primary,
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=1,
                    highlightbackground=theme.surface,
                    highlightcolor=theme.accent,
                    width=2,
                    padx=self._px(2),
                    pady=self._px(2),
                    cursor="hand2",
                    font=self._font("Segoe UI Semibold", 10),
                ).pack(side=tk.LEFT)

        self._gallery_button = tk.Button(
            self._primary_actions,
            text="Ouvrir la galerie  →",
            command=on_open_gallery,
            background=theme.success,
            foreground="#FFFFFF",
            activebackground=theme.accent,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=self._px(11),
            pady=self._px(5),
            cursor="hand2",
            font=self._font(
                "Segoe UI Semibold",
                9,
            ),
        )

        self._export_button: tk.Button | None = None
        if on_export_report is not None:
            self._export_button = tk.Button(
                self._toolbar,
                text="⇩  Exporter le rapport",
                command=on_export_report,
                background=theme.surface_elevated,
                foreground=theme.success,
                activebackground=theme.border,
                activeforeground=theme.text_primary,
                relief=tk.FLAT,
                padx=self._px(12),
                pady=self._px(5),
                highlightthickness=1,
                highlightbackground=theme.success,
                cursor="hand2",
                font=self._font(
                    "Segoe UI Semibold",
                    9,
                ),
            )

        self._layout_button: tk.Button | None = None
        if on_customize_layout is not None:
            self._layout_button = tk.Button(
                self._primary_actions,
                text="⚙  Disposition",
                command=on_customize_layout,
                background=theme.surface_elevated,
                foreground=theme.text_primary,
                activebackground=theme.border,
                activeforeground=theme.text_primary,
                relief=tk.FLAT,
                padx=self._px(9),
                pady=self._px(5),
                cursor="hand2",
                font=self._font(
                    "Segoe UI Semibold",
                    9,
                ),
            )

        self._theme_variable: tk.StringVar | None = None
        self._theme_menu: tk.OptionMenu | None = None

        if (
            theme_names
            and current_theme is not None
            and on_theme_changed is not None
        ):
            self._theme_variable = tk.StringVar(
                master=self,
                value=current_theme
            )
            theme_variable = self._theme_variable
            theme_change_callback = on_theme_changed

            if (
                theme_variable is None
                or theme_change_callback is None
            ):
                raise RuntimeError(
                    "Theme controls require a variable "
                    "and a change callback."
                )

            self._theme_menu = tk.OptionMenu(
                self._primary_actions,
                theme_variable,
                *theme_names,
            )

            def handle_theme_variable_change(
                *_args: str,
            ) -> None:
                if self._disposed:
                    return

                try:
                    selected_theme = theme_variable.get()
                except tk.TclError:
                    return

                theme_change_callback(selected_theme)

            self._theme_trace_id = theme_variable.trace_add(
                "write",
                handle_theme_variable_change,
            )
            self._theme_menu.configure(
                background=theme.surface_elevated,
                foreground=theme.text_primary,
                activebackground=theme.border,
                activeforeground=theme.text_primary,
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0,
                width=13,
                font=self._font(
                    "Segoe UI",
                    9,
                ),
            )
            self._theme_menu["menu"].configure(
                background=theme.surface,
                foreground=theme.text_primary,
                activebackground=theme.accent,
            )

        self._theme_symbol = tk.Label(
            self._primary_actions,
            text="☼",
            background=theme.surface,
            foreground=theme.warning,
            font=self._font(
                "Segoe UI Symbol",
                14,
            ),
            padx=self._px(5),
        )
        self._theme_symbol.pack(side=tk.LEFT)

        if self._theme_menu is not None:
            self._theme_menu.pack(
                side=tk.LEFT,
                padx=(0, self._px(5)),
            )

        if self._layout_button is not None:
            self._layout_button.pack(
                side=tk.LEFT,
                padx=(0, self._px(5)),
            )

        self._gallery_button.pack(side=tk.LEFT)

        if self._export_button is not None:
            self._export_button.pack(
                anchor="e",
                pady=(self._px(6), 0),
            )

        self._canvas.bind(
            "<Configure>",
            self._schedule_redraw,
        )

        self._load_source_image()

    @property
    def has_source_image(self) -> bool:
        """Return whether a real project image is loaded."""
        return self._source_image is not None

    def destroy(self) -> None:
        """Release Tcl callbacks and destroy the banner exactly once."""
        if self._disposed:
            return

        self._disposed = True
        theme_variable = self._theme_variable
        theme_trace_id = self._theme_trace_id

        if (
            theme_variable is not None
            and theme_trace_id is not None
        ):
            try:
                theme_variable.trace_remove(
                    "write",
                    theme_trace_id,
                )
            except tk.TclError:
                pass

        self._theme_trace_id = None

        for attribute_name in (
            "_initial_redraw_after_id",
            "_redraw_after_id",
        ):
            callback_id = getattr(
                self,
                attribute_name,
            )

            if callback_id is None:
                continue

            try:
                self.after_cancel(callback_id)
            except tk.TclError:
                pass

            setattr(self, attribute_name, None)

        self._photo = None
        super().destroy()

    def bind_window_drag(
        self,
        *,
        on_start: Callable[[tk.Event], None],
        on_motion: Callable[[tk.Event], None],
        on_end: Callable[[tk.Event], None],
    ) -> None:
        """Make the illustrated background act as a window drag surface."""
        self._canvas.bind(
            "<ButtonPress-1>",
            on_start,
            add="+",
        )
        self._canvas.bind(
            "<B1-Motion>",
            on_motion,
            add="+",
        )
        self._canvas.bind(
            "<ButtonRelease-1>",
            on_end,
            add="+",
        )

    def _px(
        self,
        value: int,
    ) -> int:
        """Scale one hero dimension for the current display."""
        return max(
            1,
            round(value * self._visual_scale),
        )

    def _font(
        self,
        family: str,
        size: int,
    ) -> tuple[str, int]:
        """Return one explicitly scaled hero font."""
        return (
            family,
            self._px(size),
        )

    def _type(
        self,
        role: TypographyRole,
    ) -> tuple[str, int]:
        """Resolve one semantic hero font for the display scale."""
        return typography_font(
            role,
            visual_scale=self._visual_scale,
        )

    def mount_at_top(self) -> None:
        """Insert the banner before existing dashboard content."""
        packed_children = tuple(
            child
            for child in self._container.pack_slaves()
            if (
                child is not self
                and isinstance(child, tk.Widget)
            )
        )
        gridded_children = tuple(
            child
            for child in self._container.grid_slaves()
            if (
                child is not self
                and isinstance(child, tk.Widget)
            )
        )

        geometry_manager = resolve_mount_geometry_manager(
            packed_children=len(packed_children),
            gridded_children=len(gridded_children),
        )

        if geometry_manager == "pack":
            if packed_children:
                self.pack(
                    fill=tk.X,
                    padx=18,
                    pady=(14, 4),
                    before=packed_children[0],
                )

            else:
                self.pack(
                    fill=tk.X,
                    padx=18,
                    pady=(14, 4),
                )

        else:
            for child in gridded_children:
                row_value = child.grid_info().get(
                    "row"
                )
                if row_value is not None:
                    child.grid_configure(
                        row=int(row_value) + 1,
                    )

            self.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=18,
                pady=(14, 4),
            )

        if (
            not self._disposed
            and not self._initial_redraw_completed
            and self._initial_redraw_after_id is None
        ):
            self._initial_redraw_after_id = (
                self.after_idle(
                    self._run_initial_redraw
                )
            )

    def set_image_path(
        self,
        image_path: Path | None,
    ) -> None:
        """Replace the project image used by the banner."""
        if self._disposed:
            return

        normalized_path = (
            Path(image_path)
            if image_path is not None
            else None
        )

        if normalized_path == self._image_path:
            return

        self._image_path = normalized_path
        self._load_source_image()
        self._schedule_redraw()

    def _load_source_image(self) -> None:
        """Load the image without retaining a file handle."""
        self._source_image = _load_rgb_image(
            self._image_path
        )

    def _schedule_redraw(
        self,
        _event: tk.Event | None = None,
    ) -> None:
        """Debounce redraws triggered by resizing."""
        if self._disposed:
            return

        if self._redraw_after_id is not None:
            try:
                self.after_cancel(
                    self._redraw_after_id
                )
            except tk.TclError:
                pass

            self._redraw_after_id = None

        self._redraw_after_id = self.after(
            40,
            self._run_scheduled_redraw,
        )

    def _run_initial_redraw(self) -> None:
        """Run the owned first redraw when the banner is still alive."""
        self._initial_redraw_after_id = None
        self._initial_redraw_completed = True

        if not self._disposed:
            self._redraw()

    def _run_scheduled_redraw(self) -> None:
        """Run one debounced redraw when the banner is still alive."""
        self._redraw_after_id = None

        if not self._disposed:
            self._redraw()

    def _redraw(self) -> None:
        """Render the responsive image, overlay and controls."""
        if self._disposed:
            return

        try:
            canvas_exists = self._canvas.winfo_exists()
        except tk.TclError:
            return

        if not canvas_exists:
            return

        width = max(
            1,
            self._canvas.winfo_width(),
        )
        height = max(
            1,
            self._canvas.winfo_height(),
        )
        rendered = self._render_background(
            width=width,
            height=height,
        )

        self._photo = ImageTk.PhotoImage(
            rendered,
            master=self,
        )

        self._canvas.delete(
            "all"
        )
        self._canvas.create_image(
            0,
            0,
            image=self._photo,
            anchor="nw",
        )

        self._canvas.create_text(
            self._px(28),
            self._px(14),
            text=self._title,
            fill=self._theme.text_primary,
            anchor="nw",
            font=self._type(TypographyRole.PROJECT_TITLE),
        )
        self._canvas.create_text(
            self._px(29),
            self._px(52),
            text=self._subtitle,
            fill=self._theme.text_secondary,
            anchor="nw",
            width=max(
                self._px(320),
                min(
                    self._px(680),
                    width - self._px(520),
                ),
            ),
            font=self._type(TypographyRole.BODY),
        )
        self._canvas.create_text(
            self._px(29),
            self._px(94),
            text="●  Projet actif",
            fill=self._theme.success,
            anchor="nw",
            font=self._type(TypographyRole.PRIMARY_LABEL),
        )

        self._canvas.create_window(
            width - self._px(14),
            self._px(10),
            window=self._toolbar,
            anchor="ne",
        )

    def _render_background(
        self,
        *,
        width: int,
        height: int,
    ) -> Image.Image:
        """Build a wide source image or illustrated aquarium fallback."""
        source_is_panorama = _is_panorama(
            self._source_image
        )

        if (
            self._source_image is None
            or not source_is_panorama
        ):
            image = build_aquarium_fallback(
                width=width,
                height=height,
                theme=self._theme,
            )

        else:
            image = ImageOps.fit(
                self._source_image,
                (width, height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.4),
            )
 
        rgba_image = image.convert(
            "RGBA"
        )
        overlay = Image.new(
            "RGBA",
            (width, height),
            (3, 18, 27, 0),
        )
        overlay_drawing = ImageDraw.Draw(
            overlay,
            "RGBA",
        )
 
        gradient_width = min(
            width,
            max(
                720,
                round(width * 0.66),
            ),
        )
        steps = 64
 
        for step in range(steps):
            start_x = round(
                gradient_width * step / steps
            )
            end_x = round(
                gradient_width
                * (step + 1)
                / steps
            )
            alpha = round(
                160
                * (1 - step / steps)
            )
            overlay_drawing.rectangle(
                (
                    start_x,
                    0,
                    end_x,
                    height,
                ),
                fill=(
                    3,
                    18,
                    27,
                    alpha,
                ),
            )
 
        overlay_drawing.ellipse(
            (
                round(width * 0.34),
                round(height * 0.04),
                round(width * 0.76),
                round(height * 0.40),
            ),
            fill=(255, 255, 255, 18),
        )
        overlay_drawing.ellipse(
            (
                round(width * 0.62),
                round(height * 0.12),
                round(width * 0.88),
                round(height * 0.26),
            ),
            fill=(255, 255, 255, 12),
        )
 
        composited = Image.alpha_composite(
            rgba_image,
            overlay,
        )
 
        vignette_mask = Image.new(
            "L",
            (width, height),
            0,
        )
        vignette_drawing = ImageDraw.Draw(
            vignette_mask,
            "L",
        )
        vignette_drawing.ellipse(
            (
                -round(width * 0.18),
                -round(height * 0.18),
                round(width * 1.18),
                round(height * 1.18),
            ),
            fill=255,
        )
        edge_shadow = Image.new(
            "RGBA",
            (width, height),
            (0, 0, 0, 112),
        )
        composited = Image.composite(
            composited,
            edge_shadow,
            vignette_mask,
        ).convert("RGB")

        radius = max(
            1,
            min(
                14,
                width // 2,
                height // 2,
            ),
        )
        mask = Image.new(
            "L",
            (width, height),
            0,
        )
        mask_drawing = ImageDraw.Draw(mask)
        mask_drawing.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=radius,
            fill=255,
        )

        rounded = Image.new(
            "RGB",
            (width, height),
            self._theme.background,
        )
        rounded.paste(
            composited,
            (0, 0),
            mask,
        )
        border = ImageDraw.Draw(rounded)
        border.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=radius,
            outline=self._theme.border,
            width=1,
        )

        return rounded
