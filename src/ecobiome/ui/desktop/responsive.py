"""Responsive scrolling infrastructure for the desktop dashboard."""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True, kw_only=True)
class DashboardViewportMetrics:
    """Describe a display ratio without mutating Tk global scaling."""

    screen_width: int
    screen_height: int
    reference_width: int = 1920
    reference_height: int = 1080
    minimum_ratio: float = 0.72
    maximum_ratio: float = 1.0

    @property
    def fit_ratio(self) -> float:
        """Return a clamped informational display ratio."""
        if (
            self.screen_width <= 0
            or self.screen_height <= 0
        ):
            raise ValueError(
                "Screen dimensions must be positive."
            )

        if (
            self.reference_width <= 0
            or self.reference_height <= 0
        ):
            raise ValueError(
                "Reference dimensions must be positive."
            )

        if not (
            0
            < self.minimum_ratio
            <= self.maximum_ratio
        ):
            raise ValueError(
                "Viewport scaling bounds are invalid."
            )

        raw_ratio = min(
            self.screen_width
            / self.reference_width,
            self.screen_height
            / self.reference_height,
        )

        return max(
            self.minimum_ratio,
            min(
                self.maximum_ratio,
                raw_ratio,
            ),
        )


def fit_content_height(
    viewport_height: int,
    requested_height: int,
) -> int:
    """Fill the viewport while preserving taller scrollable content."""
    if (
        viewport_height < 0
        or requested_height < 0
    ):
        raise ValueError(
            "Viewport heights cannot be negative."
        )

    return max(
        1,
        viewport_height,
        requested_height,
    )


def responsive_sidebar_width(
    viewport_width: int,
    *,
    minimum: int = 200,
    maximum: int = 450,
    ratio: float = 0.17,
) -> int:
    """Keep the navigation rail proportional without crowding content."""
    if viewport_width <= 0:
        raise ValueError(
            "Viewport width must be positive."
        )

    if not 0 < minimum <= maximum:
        raise ValueError(
            "Sidebar width bounds are invalid."
        )

    if not 0 < ratio < 1:
        raise ValueError(
            "Sidebar width ratio must be between zero and one."
        )

    return max(
        minimum,
        min(
            maximum,
            round(viewport_width * ratio),
        ),
    )


def responsive_content_width(
    viewport_width: int,
    *,
    maximum: int = 1900,
) -> int:
    """Cap ultra-wide dashboard content while preserving narrow layouts."""
    if viewport_width <= 0:
        raise ValueError(
            "Viewport width must be positive."
        )

    if maximum <= 0:
        raise ValueError(
            "Maximum content width must be positive."
        )

    return min(
        viewport_width,
        maximum,
    )


def geometry_dimensions(
    geometry: str,
) -> tuple[int, int]:
    """Extract positive width and height from one Tk geometry string."""
    match = re.fullmatch(
        r"\s*(\d+)x(\d+)(?:[+-]+\d+){0,2}\s*",
        geometry,
    )

    if match is None:
        raise ValueError(
            "Initial desktop geometry is invalid."
        )

    width = int(match.group(1))
    height = int(match.group(2))

    if width <= 0 or height <= 0:
        raise ValueError(
            "Initial desktop geometry dimensions must be positive."
        )

    return width, height


def scrollbar_thumb_geometry(
    first: float,
    last: float,
    *,
    track_height: int,
    minimum_height: int,
) -> tuple[int, int]:
    """Resolve one bounded vertical scrollbar thumb geometry."""
    if track_height <= 0 or minimum_height <= 0:
        raise ValueError(
            "Scrollbar dimensions must be positive."
        )

    if not 0.0 <= first <= last <= 1.0:
        raise ValueError(
            "Scrollbar fractions must be ordered between zero and one."
        )

    thumb_top = round(track_height * first)
    thumb_bottom = round(track_height * last)
    resolved_minimum = min(
        track_height,
        minimum_height,
    )

    if thumb_bottom - thumb_top < resolved_minimum:
        thumb_bottom = min(
            track_height,
            thumb_top + resolved_minimum,
        )
        thumb_top = max(
            0,
            thumb_bottom - resolved_minimum,
        )

    return thumb_top, thumb_bottom


def scrollbar_fraction_for_thumb(
    thumb_top: int,
    *,
    track_height: int,
    thumb_height: int,
) -> float:
    """Translate a dragged thumb position to a canvas scroll fraction."""
    if track_height <= 0 or thumb_height <= 0:
        raise ValueError(
            "Scrollbar dimensions must be positive."
        )

    travel = max(
        1,
        track_height - min(
            track_height,
            thumb_height,
        ),
    )

    return max(
        0.0,
        min(
            1.0,
            thumb_top / travel,
        ),
    )


class CanvasVerticalScrollbar:
    """Draw a theme-aware vertical scrollbar for one Tk canvas."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        target: tk.Canvas,
        background: str,
        thumb: str,
        active_thumb: str,
        width: int = 8,
        minimum_thumb_height: int = 28,
    ) -> None:
        if width <= 0 or minimum_thumb_height <= 0:
            raise ValueError(
                "Scrollbar dimensions must be positive."
            )

        self._target = target
        self._width = width
        self._minimum_thumb_height = minimum_thumb_height
        self._drag_offset: int | None = None
        self.widget = tk.Canvas(
            parent,
            width=width,
            background=background,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )
        self._thumb = self.widget.create_rectangle(
            1,
            0,
            max(2, width - 1),
            1,
            fill=thumb,
            activefill=active_thumb,
            outline="",
        )

        target.configure(
            yscrollcommand=self.set,
        )
        self.widget.bind(
            "<Configure>",
            self._refresh,
        )
        self.widget.bind(
            "<ButtonPress-1>",
            self._begin_drag,
        )
        self.widget.bind(
            "<B1-Motion>",
            self._drag,
        )
        self.widget.bind(
            "<ButtonRelease-1>",
            self._end_drag,
        )

    def grid(
        self,
        *,
        row: int,
        column: int,
        sticky: str = "ns",
    ) -> None:
        """Mount the scrollbar canvas with grid."""
        self.widget.grid(
            row=row,
            column=column,
            sticky=sticky,
        )

    def set(
        self,
        first: float | str,
        last: float | str,
    ) -> None:
        """Synchronize visibility and thumb position from a canvas view."""
        first_fraction = float(first)
        last_fraction = float(last)

        if first_fraction <= 0.0 and last_fraction >= 1.0:
            self.widget.grid_remove()
            return

        self.widget.grid()
        track_height = max(
            1,
            self.widget.winfo_height(),
        )
        thumb_top, thumb_bottom = scrollbar_thumb_geometry(
            first_fraction,
            last_fraction,
            track_height=track_height,
            minimum_height=self._minimum_thumb_height,
        )
        self.widget.coords(
            self._thumb,
            1,
            thumb_top,
            max(2, self._width - 1),
            thumb_bottom,
        )

    def _refresh(
        self,
        _event: tk.Event,
    ) -> None:
        first, last = self._target.yview()
        self.set(first, last)

    def _move_to_pointer(
        self,
        event: tk.Event,
        *,
        offset: int,
    ) -> None:
        track_height = max(
            1,
            self.widget.winfo_height(),
        )
        coordinates = self.widget.coords(
            self._thumb
        )
        thumb_height = max(
            1,
            round(coordinates[3] - coordinates[1]),
        )
        thumb_top = max(
            0,
            min(
                track_height - thumb_height,
                event.y - offset,
            ),
        )
        fraction = scrollbar_fraction_for_thumb(
            thumb_top,
            track_height=track_height,
            thumb_height=thumb_height,
        )
        self._target.yview_moveto(fraction)

    def _begin_drag(
        self,
        event: tk.Event,
    ) -> str:
        coordinates = self.widget.coords(
            self._thumb
        )

        if coordinates[1] <= event.y <= coordinates[3]:
            self._drag_offset = round(
                event.y - coordinates[1]
            )
        else:
            thumb_height = max(
                1,
                round(coordinates[3] - coordinates[1]),
            )
            self._drag_offset = thumb_height // 2
            self._move_to_pointer(
                event,
                offset=self._drag_offset,
            )

        return "break"

    def _drag(
        self,
        event: tk.Event,
    ) -> str:
        if self._drag_offset is not None:
            self._move_to_pointer(
                event,
                offset=self._drag_offset,
            )

        return "break"

    def _end_drag(
        self,
        _event: tk.Event,
    ) -> str:
        self._drag_offset = None
        return "break"


class ResponsiveDashboardViewport:
    """Host dashboard content in a vertically scrollable child area."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        background: str,
        maximum_content_width: int = 1900,
        scrollbar_thumb: str = "#53666D",
        scrollbar_active_thumb: str = "#75D85A",
        scrollbar_width: int = 8,
        minimum_thumb_height: int = 28,
    ) -> None:
        if maximum_content_width <= 0:
            raise ValueError(
                "Maximum content width must be positive."
            )

        self._background = background
        self._maximum_content_width = maximum_content_width

        self.container = tk.Frame(
            parent,
            background=background,
        )
        self.container.grid_columnconfigure(
            0,
            weight=1,
        )
        self.container.grid_rowconfigure(
            0,
            weight=1,
        )

        self.canvas = tk.Canvas(
            self.container,
            background=background,
            borderwidth=0,
            highlightthickness=0,
            yscrollincrement=24,
        )
        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self._scrollbar = CanvasVerticalScrollbar(
            self.container,
            target=self.canvas,
            background=background,
            thumb=scrollbar_thumb,
            active_thumb=scrollbar_active_thumb,
            width=scrollbar_width,
            minimum_thumb_height=minimum_thumb_height,
        )
        self._scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        self.scrollbar = self._scrollbar.widget

        self.content = tk.Frame(
            self.canvas,
            background=background,
        )
        self.content.grid_columnconfigure(
            0,
            weight=1,
        )

        self._content_window = (
            self.canvas.create_window(
                (0, 0),
                window=self.content,
                anchor="nw",
            )
        )

        self.content.bind(
            "<Configure>",
            self._on_content_configure,
        )
        self.canvas.bind(
            "<Configure>",
            self._on_canvas_configure,
        )

    def grid(
        self,
        *,
        row: int,
        column: int,
        sticky: str = "nsew",
        padx: int | tuple[int, int] = 0,
        pady: int | tuple[int, int] = 0,
    ) -> None:
        """Mount the viewport with grid."""
        self.container.grid(
            row=row,
            column=column,
            sticky=sticky,
            padx=padx,
            pady=pady,
        )

    def pack(
        self,
        *,
        fill: Literal[
            "none",
            "x",
            "y",
            "both",
        ] = "both",
        expand: bool = True,
    ) -> None:
        """Mount the viewport with pack."""
        self.container.pack(
            fill=fill,
            expand=expand,
        )

    @property
    def is_alive(self) -> bool:
        """Return whether the viewport can safely receive delegated events."""
        try:
            return bool(
                self.container.winfo_exists()
                and self.canvas.winfo_exists()
            )
        except tk.TclError:
            return False

    def scroll_to_top(self) -> None:
        """Move to the first dashboard row."""
        self.canvas.yview_moveto(
            0.0
        )

    def scroll_to_bottom(self) -> None:
        """Move to the last dashboard row."""
        self.canvas.yview_moveto(
            1.0
        )

    def refresh(self) -> None:
        """Synchronize width, minimum height and scroll bounds."""
        self.content.update_idletasks()
        self.canvas.update_idletasks()

        canvas_width = max(
            1,
            self.canvas.winfo_width(),
        )
        canvas_height = max(
            1,
            self.canvas.winfo_height(),
        )
        content_width = responsive_content_width(
            canvas_width,
            maximum=self._maximum_content_width,
        )
        content_x = max(
            0,
            (canvas_width - content_width) // 2,
        )
        content_height = fit_content_height(
            canvas_height,
            self.content.winfo_reqheight(),
        )

        self.canvas.coords(
            self._content_window,
            content_x,
            0,
        )
        self.canvas.itemconfigure(
            self._content_window,
            width=content_width,
            height=content_height,
        )
        self.canvas.configure(
            scrollregion=(
                0,
                0,
                canvas_width,
                content_height,
            )
        )

    def _pointer_is_inside_canvas(
        self,
        event: tk.Event,
    ) -> bool:
        """Return whether the pointer currently targets the main viewport."""
        left = self.canvas.winfo_rootx()
        top = self.canvas.winfo_rooty()
        right = left + self.canvas.winfo_width()
        bottom = top + self.canvas.winfo_height()

        return (
            left <= event.x_root <= right
            and top <= event.y_root <= bottom
        )

    def _on_content_configure(
        self,
        _event: tk.Event,
    ) -> None:
        """Update scrolling after content geometry changes."""
        self.refresh()

    def _on_canvas_configure(
        self,
        _event: tk.Event,
    ) -> None:
        """Make content fill the available viewport dimensions."""
        self.refresh()

    def handle_mousewheel(
        self,
        event: tk.Event,
    ) -> str | None:
        """Handle a delegated Windows or macOS mouse-wheel event."""
        if (
            event.delta == 0
            or not self._pointer_is_inside_canvas(
                event
            )
        ):
            return None

        direction = (
            -1
            if event.delta > 0
            else 1
        )
        magnitude = max(
            1,
            abs(event.delta) // 120,
        )

        self.canvas.yview_scroll(
            direction * magnitude,
            "units",
        )

        return "break"

    def handle_scroll_up(
        self,
        event: tk.Event,
    ) -> str | None:
        """Handle a delegated X11 upward-scroll event."""
        if not self._pointer_is_inside_canvas(
            event
        ):
            return None

        self.canvas.yview_scroll(
            -1,
            "units",
        )

        return "break"

    def handle_scroll_down(
        self,
        event: tk.Event,
    ) -> str | None:
        """Handle a delegated X11 downward-scroll event."""
        if not self._pointer_is_inside_canvas(
            event
        ):
            return None

        self.canvas.yview_scroll(
            1,
            "units",
        )

        return "break"

    def handle_home(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle a delegated request to show the dashboard beginning."""
        self.scroll_to_top()

        return "break"

    def handle_end(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle a delegated request to show the dashboard end."""
        self.scroll_to_bottom()

        return "break"
