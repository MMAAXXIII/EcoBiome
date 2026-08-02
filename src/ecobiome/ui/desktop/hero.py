"""Image-rich project hero for the EcoBiome desktop dashboard."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from PIL import (
    Image,
    ImageDraw,
    ImageOps,
    ImageTk,
)

from ecobiome.ui.desktop.theme import DesktopTheme


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

    floor_y = round(
        height * 0.82
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

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
            str(item[3]).casefold(),
        )
    )

    return candidates[0][3]


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
    ) -> None:
        super().__init__(
            parent,
            background=theme.background,
            height=172,
        )
        self._container = parent
        self._theme = theme
        self._title = title
        self._subtitle = subtitle
        self._image_path = image_path
        self._source_image: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._redraw_after_id: str | None = None

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
            highlightthickness=1,
            highlightbackground=theme.border,
            height=172,
        )
        self._canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self._gallery_button = tk.Button(
            self._canvas,
            text="Ouvrir la galerie  →",
            command=on_open_gallery,
            background=theme.success,
            foreground="#FFFFFF",
            activebackground=theme.accent,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor="hand2",
            font=(
                "Segoe UI Semibold",
                9,
            ),
        )

        self._export_button: tk.Button | None = None
        if on_export_report is not None:
            self._export_button = tk.Button(
                self._canvas,
                text="⇩  Exporter le rapport",
                command=on_export_report,
                background=theme.surface_elevated,
                foreground=theme.success,
                activebackground=theme.border,
                activeforeground=theme.text_primary,
                relief=tk.FLAT,
                padx=13,
                pady=8,
                cursor="hand2",
                font=(
                    "Segoe UI Semibold",
                    9,
                ),
            )

        self._layout_button: tk.Button | None = None
        if on_customize_layout is not None:
            self._layout_button = tk.Button(
                self._canvas,
                text="⚙  Disposition",
                command=on_customize_layout,
                background=theme.surface_elevated,
                foreground=theme.text_primary,
                activebackground=theme.border,
                activeforeground=theme.text_primary,
                relief=tk.FLAT,
                padx=12,
                pady=8,
                cursor="hand2",
                font=(
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
                self._canvas,
                theme_variable,
                *theme_names,
            )

            def handle_theme_variable_change(
                *_args: str,
            ) -> None:
                theme_change_callback(
                    theme_variable.get()
                )

            theme_variable.trace_add(
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
                highlightthickness=1,
                highlightbackground=theme.border,
                font=(
                    "Segoe UI",
                    9,
                ),
            )
            self._theme_menu["menu"].configure(
                background=theme.surface,
                foreground=theme.text_primary,
                activebackground=theme.accent,
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

        self.after_idle(
            self._redraw
        )

    def set_image_path(
        self,
        image_path: Path | None,
    ) -> None:
        """Replace the project image used by the banner."""
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
        self._source_image = None

        if self._image_path is None:
            return

        try:
            with Image.open(
                self._image_path
            ) as source:
                self._source_image = source.convert(
                    "RGB"
                )

        except OSError:
            self._source_image = None

    def _schedule_redraw(
        self,
        _event: tk.Event | None = None,
    ) -> None:
        """Debounce redraws triggered by resizing."""
        if self._redraw_after_id is not None:
            self.after_cancel(
                self._redraw_after_id
            )

        self._redraw_after_id = self.after(
            40,
            self._redraw,
        )

    def _redraw(self) -> None:
        """Render the responsive image, overlay and controls."""
        self._redraw_after_id = None

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
            30,
            25,
            text=self._title,
            fill=self._theme.text_primary,
            anchor="nw",
            font=(
                "Segoe UI Semibold",
                25,
            ),
        )
        self._canvas.create_text(
            31,
            72,
            text=self._subtitle,
            fill=self._theme.text_secondary,
            anchor="nw",
            width=max(
                320,
                min(680, width - 520),
            ),
            font=(
                "Segoe UI",
                10,
            ),
        )
        self._canvas.create_text(
            31,
            126,
            text="●  Projet actif",
            fill=self._theme.success,
            anchor="nw",
            font=(
                "Segoe UI Semibold",
                10,
            ),
        )

        right = width - 24

        if self._theme_menu is not None:
            self._canvas.create_window(
                right,
                18,
                window=self._theme_menu,
                anchor="ne",
            )

        if self._export_button is not None:
            self._canvas.create_window(
                right,
                66,
                window=self._export_button,
                anchor="ne",
            )

        self._canvas.create_window(
            right,
            height - 18,
            window=self._gallery_button,
            anchor="se",
        )

        if self._layout_button is not None:
            self._canvas.create_window(
                right - 160,
                height - 18,
                window=self._layout_button,
                anchor="se",
            )

    def _render_background(
        self,
        *,
        width: int,
        height: int,
    ) -> Image.Image:
        """Build a wide source image or illustrated aquarium fallback."""
        source_is_panorama = False

        if self._source_image is not None:
            source_width, source_height = (
                self._source_image.size
            )

            if source_height > 0:
                source_is_panorama = (
                    source_width / source_height
                    >= 2.15
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
                centering=(0.52, 0.5),
            )

        rgba_image = image.convert(
            "RGBA"
        )
        overlay = Image.new(
            "RGBA",
            (width, height),
            (1, 10, 13, 96),
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
                226
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
                    1,
                    12,
                    15,
                    alpha,
                ),
            )

        return Image.alpha_composite(
            rgba_image,
            overlay,
        ).convert("RGB")
