"""Reusable rounded surfaces for the Tkinter desktop interface."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from PIL import Image, ImageDraw, ImageTk
from ecobiome.ui.desktop.design_tokens import surface_geometry


class SurfaceLevel(StrEnum):
    """Stable visual levels used by every rounded dashboard surface."""

    PANEL = "panel"
    ANALYTIC = "analytic"
    COMPACT = "compact"


@dataclass(frozen=True, slots=True)
class SurfaceProfile:
    """Resolved geometry for one level of the surface system."""

    level: SurfaceLevel
    radius: int
    shadow_offset: int


def surface_profile(
    level: SurfaceLevel | str,
    *,
    visual_scale: float = 1.0,
) -> SurfaceProfile:
    """Resolve one of the three supported surface geometries."""
    if visual_scale <= 0:
        raise ValueError(
            "Surface visual scale must be positive."
        )

    resolved_level = SurfaceLevel(level)
    # Use centralized design tokens for surface geometry so tuning is simple
    # and traceable. surface_geometry returns scaled (radius, shadow_offset)
    # keyed by the SurfaceLevel.value ("panel", "analytic", "compact").
    geometry = surface_geometry(visual_scale=visual_scale)
    radius, shadow_offset = geometry[resolved_level.value]

    return SurfaceProfile(
        level=resolved_level,
        radius=max(2, round(radius * visual_scale)),
        shadow_offset=max(
            1,
            round(shadow_offset * visual_scale),
        ),
    )


def render_rounded_surface(
    width: int,
    height: int,
    *,
    outer_background: str,
    surface: str,
    border: str,
    shadow: str,
    radius: int,
    shadow_offset: int,
    supersampling: int = 2,
) -> Image.Image:
    """Render one antialiased card surface at native display size."""
    resolved_width = max(1, width)
    resolved_height = max(1, height)
    scale = max(1, supersampling)
    scaled_size = (
        resolved_width * scale,
        resolved_height * scale,
    )
    image = Image.new(
        "RGB",
        scaled_size,
        outer_background,
    )
    drawing = ImageDraw.Draw(image)
    scaled_radius = max(1, radius * scale)
    scaled_shadow_offset = max(1, shadow_offset * scale)
    inset = scale
    right = max(inset, scaled_size[0] - inset - 1)
    bottom = max(inset, scaled_size[1] - inset - 1)
    surface_bottom = max(
        inset,
        bottom - scaled_shadow_offset,
    )

    drawing.rounded_rectangle(
        (
            inset,
            inset + scaled_shadow_offset,
            right,
            bottom,
        ),
        radius=scaled_radius,
        fill=shadow,
    )
    drawing.rounded_rectangle(
        (
            inset,
            inset,
            right,
            surface_bottom,
        ),
        radius=scaled_radius,
        fill=surface,
        outline=border,
        width=scale,
    )

    if scale == 1:
        return image

    return image.resize(
        (resolved_width, resolved_height),
        Image.Resampling.LANCZOS,
    )


class RoundedSurfaceCard(tk.Frame):
    """Expose a normal content frame mounted on a rounded canvas host."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        background: str,
        outer_background: str,
        border: str,
        shadow: str,
        padding: int,
        level: SurfaceLevel | str = SurfaceLevel.PANEL,
        visual_scale: float = 1.0,
    ) -> None:
        profile = surface_profile(
            level,
            visual_scale=visual_scale,
        )
        self._host = tk.Canvas(
            parent,
            background=outer_background,
            borderwidth=0,
            highlightthickness=0,
        )
        self._surface_color = background
        self._outer_background = outer_background
        self._border_color = border
        self._shadow_color = shadow
        self._surface_level = profile.level
        self._radius = profile.radius
        self._content_inset = max(
            2,
            round(self._radius * 0.38),
        )
        self._shadow_offset = profile.shadow_offset
        self._surface_photo: ImageTk.PhotoImage | None = None
        self._redraw_after_id: str | None = None
        self._size_sync_after_id: str | None = None
        self._last_rendered_size: tuple[int, int] | None = None

        super().__init__(
            self._host,
            background=background,
            borderwidth=0,
            padx=padding,
            pady=padding,
        )

        self._content_window = self._host.create_window(
            (
                self._content_inset,
                self._content_inset,
            ),
            window=self,
            anchor="nw",
        )

        self._host.bind(
            "<Configure>",
            self._schedule_surface_redraw,
        )
        self._size_sync_after_id = (
            self._host.after_idle(
                self._run_size_sync,
            )
        )

    @property
    def surface_level(self) -> SurfaceLevel:
        """Return the semantic level represented by this card."""
        return self._surface_level

    def grid(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Mount the rounded host with grid."""
        self._host.grid(*args, **kwargs)

    def grid_configure(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Update grid options on the rounded host."""
        self._host.grid_configure(
            *args,
            **kwargs,
        )

    def grid_remove(self) -> None:
        """Temporarily hide the rounded host."""
        self._host.grid_remove()

    def grid_forget(self) -> None:
        """Unmanage the rounded host from grid."""
        self._host.grid_forget()

    def pack(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Mount the rounded host with pack."""
        self._host.pack(*args, **kwargs)

    def pack_configure(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Update pack options on the rounded host."""
        self._host.pack_configure(
            *args,
            **kwargs,
        )

    def pack_forget(self) -> None:
        """Unmanage the rounded host from pack."""
        self._host.pack_forget()

    def destroy(self) -> None:
        """Destroy both the content frame and its canvas host."""
        host = self._host

        if self._redraw_after_id is not None:
            try:
                host.after_cancel(
                    self._redraw_after_id
                )
            except tk.TclError:
                pass

            self._redraw_after_id = None

        if self._size_sync_after_id is not None:
            try:
                host.after_cancel(
                    self._size_sync_after_id
                )
            except tk.TclError:
                pass

            self._size_sync_after_id = None

        super().destroy()

        if host.winfo_exists():
            host.destroy()

    def _sync_requested_size(self) -> None:
        """Expose the content's natural size to the canvas host."""
        try:
            content_exists = self.winfo_exists()
        except tk.TclError:
            return

        if not content_exists:
            return

        self.update_idletasks()
        requested_width = max(
            1,
            self.winfo_reqwidth()
            + 2 * self._content_inset,
        )
        requested_height = max(
            1,
            self.winfo_reqheight()
            + 2 * self._content_inset
            + self._shadow_offset
            + 1,
        )

        if (
            int(self._host.cget("width"))
            != requested_width
        ):
            self._host.configure(
                width=requested_width
            )

        if (
            int(self._host.cget("height"))
            != requested_height
        ):
            self._host.configure(
                height=requested_height
            )

    def _run_size_sync(self) -> None:
        """Synchronize once after the card's contents have been built."""
        self._size_sync_after_id = None
        self._sync_requested_size()

    def _schedule_surface_redraw(
        self,
        _event: tk.Event,
    ) -> None:
        """Debounce surface rendering while the viewport is resizing."""
        if self._redraw_after_id is not None:
            self._host.after_cancel(
                self._redraw_after_id
            )

        self._redraw_after_id = self._host.after(
            16,
            self._redraw_surface,
        )

    def _redraw_surface(self) -> None:
        """Draw the rounded fill, border and subtle lower shadow."""
        self._redraw_after_id = None
        width = max(1, self._host.winfo_width())
        height = max(1, self._host.winfo_height())
        surface_bottom = max(
            2,
            height - self._shadow_offset - 1,
        )
        content_width = max(
            1,
            width - 2 * self._content_inset,
        )
        content_height = max(
            1,
            surface_bottom
            - 2 * self._content_inset,
        )

        if self._last_rendered_size != (width, height):
            rendered = render_rounded_surface(
                width,
                height,
                outer_background=self._outer_background,
                surface=self._surface_color,
                border=self._border_color,
                shadow=self._shadow_color,
                radius=self._radius,
                shadow_offset=self._shadow_offset,
            )
            self._surface_photo = ImageTk.PhotoImage(
                rendered,
                master=self._host,
            )
            self._last_rendered_size = (width, height)
            self._host.delete("surface-image")
            self._host.create_image(
                0,
                0,
                image=self._surface_photo,
                anchor="nw",
                tags=("surface-image",),
            )

        self._host.coords(
            self._content_window,
            self._content_inset,
            self._content_inset,
        )
        self._host.itemconfigure(
            self._content_window,
            width=content_width,
            height=content_height,
        )
        self._host.tag_lower("surface-image")


def normalize_role(
    role: str,
) -> str:
    """Normalize one visual icon role to a supported identifier."""
    supported = {
        "success",
        "quality",
        "hypothesis",
        "warning",
        "conclusion",
    }

    return role if role in supported else "success"


def draw_diagnostic_icon(
    canvas: tk.Canvas,
    *,
    role: str,
    accent: str,
    fill: str,
    size: int,
) -> None:
    """Draw one crisp diagnostic pictogram inside a circular badge."""
    canvas.delete("all")
    normalized_role = normalize_role(role)
    center = size / 2
    radius = size * 0.43
    canvas.create_oval(
        center - radius,
        center - radius,
        center + radius,
        center + radius,
        fill=fill,
        outline=accent,
        width=max(1, round(size / 28)),
    )

    drawers = {
        "success": _draw_leaf,
        "quality": _draw_shield,
        "hypothesis": _draw_hypothesis,
        "warning": _draw_flask,
        "conclusion": _draw_target,
    }
    drawers[normalized_role](
        canvas,
        size,
        accent,
    )


def _scaled_points(
    size: int,
    points: Sequence[tuple[float, float]],
) -> tuple[float, ...]:
    """Scale normalized point pairs to one square icon canvas."""
    values: list[float] = []

    for x, y in points:
        values.extend((x * size, y * size))

    return tuple(values)


def _draw_leaf(
    canvas: tk.Canvas,
    size: int,
    accent: str,
) -> None:
    canvas.create_polygon(
        _scaled_points(
            size,
            (
                (0.31, 0.56),
                (0.38, 0.35),
                (0.63, 0.29),
                (0.68, 0.51),
                (0.52, 0.67),
            ),
        ),
        smooth=True,
        fill=accent,
        outline=accent,
    )
    canvas.create_line(
        size * 0.35,
        size * 0.69,
        size * 0.58,
        size * 0.39,
        fill=accent,
        width=max(1, round(size / 28)),
    )


def _draw_shield(
    canvas: tk.Canvas,
    size: int,
    accent: str,
) -> None:
    canvas.create_polygon(
        _scaled_points(
            size,
            (
                (0.50, 0.27),
                (0.67, 0.35),
                (0.64, 0.58),
                (0.50, 0.72),
                (0.36, 0.58),
                (0.33, 0.35),
            ),
        ),
        fill="",
        outline=accent,
        width=max(1, round(size / 24)),
    )
    canvas.create_line(
        size * 0.50,
        size * 0.30,
        size * 0.50,
        size * 0.68,
        fill=accent,
        width=max(1, round(size / 34)),
    )


def _draw_hypothesis(
    canvas: tk.Canvas,
    size: int,
    accent: str,
) -> None:
    nodes = (
        (0.40, 0.39),
        (0.59, 0.36),
        (0.50, 0.54),
        (0.38, 0.61),
        (0.62, 0.62),
    )
    line_width = max(1, round(size / 38))

    for start, end in (
        (nodes[0], nodes[1]),
        (nodes[0], nodes[2]),
        (nodes[1], nodes[2]),
        (nodes[2], nodes[3]),
        (nodes[2], nodes[4]),
    ):
        canvas.create_line(
            start[0] * size,
            start[1] * size,
            end[0] * size,
            end[1] * size,
            fill=accent,
            width=line_width,
        )

    node_radius = size * 0.045

    for x, y in nodes:
        canvas.create_oval(
            x * size - node_radius,
            y * size - node_radius,
            x * size + node_radius,
            y * size + node_radius,
            fill=accent,
            outline="",
        )


def _draw_flask(
    canvas: tk.Canvas,
    size: int,
    accent: str,
) -> None:
    line_width = max(1, round(size / 26))
    canvas.create_line(
        (
            size * 0.43,
            size * 0.30,
            size * 0.57,
            size * 0.30,
        ),
        fill=accent,
        width=line_width,
    )
    canvas.create_line(
        [
            size * 0.46,
            size * 0.30,
            size * 0.46,
            size * 0.47,
            size * 0.34,
            size * 0.66,
            size * 0.66,
            size * 0.66,
            size * 0.54,
            size * 0.47,
            size * 0.54,
            size * 0.30,
        ],
        fill=accent,
        width=line_width,
        joinstyle=tk.ROUND,
    )
    canvas.create_line(
        (
            size * 0.39,
            size * 0.58,
            size * 0.61,
            size * 0.58,
        ),
        fill=accent,
        width=line_width,
    )


def _draw_target(
    canvas: tk.Canvas,
    size: int,
    accent: str,
) -> None:
    for ratio in (0.23, 0.11):
        radius = size * ratio
        canvas.create_oval(
            size / 2 - radius,
            size / 2 - radius,
            size / 2 + radius,
            size / 2 + radius,
            outline=accent,
            width=max(1, round(size / 32)),
        )
    center_radius = size * 0.035
    canvas.create_oval(
        size / 2 - center_radius,
        size / 2 - center_radius,
        size / 2 + center_radius,
        size / 2 + center_radius,
        fill=accent,
        outline="",
    )
