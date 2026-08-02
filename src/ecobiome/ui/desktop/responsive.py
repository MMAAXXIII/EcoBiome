"""Responsive scrolling infrastructure for the desktop dashboard."""

from __future__ import annotations

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
            1.0,
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


class ResponsiveDashboardViewport:
    """Host dashboard content in a vertically scrollable child area."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        background: str,
    ) -> None:
        self._background = background

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

        self.scrollbar = tk.Scrollbar(
            self.container,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
        )
        self.scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.canvas.configure(
            yscrollcommand=self.scrollbar.set,
        )

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


    def bind_scrolling(
        self,
        root: tk.Tk,
    ) -> None:
        """Bind wheel and keyboard navigation to one application root."""
        root.bind(
            "<MouseWheel>",
            self._on_mousewheel,
        )
        root.bind(
            "<Button-4>",
            self._on_scroll_up,
        )
        root.bind(
            "<Button-5>",
            self._on_scroll_down,
        )
        root.bind(
            "<Home>",
            self._on_home,
        )
        root.bind(
            "<End>",
            self._on_end,
        )

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
        content_height = fit_content_height(
            canvas_height,
            self.content.winfo_reqheight(),
        )

        self.canvas.itemconfigure(
            self._content_window,
            width=canvas_width,
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

    def _on_mousewheel(
        self,
        event: tk.Event,
    ) -> str | None:
        """Scroll with the Windows or macOS mouse wheel."""
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

    def _on_scroll_up(
        self,
        event: tk.Event,
    ) -> str | None:
        """Scroll upward on X11."""
        if not self._pointer_is_inside_canvas(
            event
        ):
            return None

        self.canvas.yview_scroll(
            -1,
            "units",
        )

        return "break"

    def _on_scroll_down(
        self,
        event: tk.Event,
    ) -> str | None:
        """Scroll downward on X11."""
        if not self._pointer_is_inside_canvas(
            event
        ):
            return None

        self.canvas.yview_scroll(
            1,
            "units",
        )

        return "break"

    def _on_home(
        self,
        _event: tk.Event,
    ) -> str:
        """Move to the beginning of the dashboard."""
        self.scroll_to_top()

        return "break"

    def _on_end(
        self,
        _event: tk.Event,
    ) -> str:
        """Move to the end of the dashboard."""
        self.scroll_to_bottom()

        return "break"
