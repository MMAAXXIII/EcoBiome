"""Full-size media-gallery viewer for the EcoBiome desktop UI."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, replace
from typing import Literal

from PIL import Image, ImageTk

from ecobiome.ui.desktop.gallery import (
    MediaGalleryItem,
)
from ecobiome.ui.desktop.theme import DesktopTheme


@dataclass(frozen=True, slots=True, kw_only=True)
class GalleryNavigator:
    """Navigate through an immutable collection of gallery items."""

    items: tuple[MediaGalleryItem, ...]
    index: int = 0

    def __post_init__(self) -> None:
        """Validate the current gallery position."""
        items = tuple(self.items)

        if not items and self.index != 0:
            raise ValueError(
                "An empty gallery must use index zero."
            )

        if items and not 0 <= self.index < len(items):
            raise IndexError(
                "Gallery index is outside the available items."
            )

        object.__setattr__(
            self,
            "items",
            items,
        )

    @property
    def current(
        self,
    ) -> MediaGalleryItem | None:
        """Return the currently selected item."""
        if not self.items:
            return None

        return self.items[self.index]

    @property
    def position_label(self) -> str:
        """Return a human-readable gallery position."""
        if not self.items:
            return "0 / 0"

        return (
            f"{self.index + 1} / "
            f"{len(self.items)}"
        )

    def next(
        self,
    ) -> GalleryNavigator:
        """Move to the next item with wrap-around."""
        if not self.items:
            return self

        return replace(
            self,
            index=(
                self.index + 1
            ) % len(self.items),
        )

    def previous(
        self,
    ) -> GalleryNavigator:
        """Move to the previous item with wrap-around."""
        if not self.items:
            return self

        return replace(
            self,
            index=(
                self.index - 1
            ) % len(self.items),
        )

    def select(
        self,
        index: int,
    ) -> GalleryNavigator:
        """Select an explicit item index."""
        if not self.items:
            if index == 0:
                return self

            raise IndexError(
                "Cannot select an item in an empty gallery."
            )

        if not 0 <= index < len(self.items):
            raise IndexError(
                "Gallery index is outside the available items."
            )

        if index == self.index:
            return self

        return replace(
            self,
            index=index,
        )


class GalleryViewerDialog(tk.Toplevel):
    """Display project images at a larger size."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        *,
        items: tuple[MediaGalleryItem, ...],
        theme: DesktopTheme,
    ) -> None:
        super().__init__(
            parent,
            background=theme.background,
        )

        self._theme = theme
        self._navigator = GalleryNavigator(
            items=items
        )

        self._photo: ImageTk.PhotoImage | None = None

        self._image_label: tk.Label | None = None
        self._title_label: tk.Label | None = None
        self._metadata_label: tk.Label | None = None
        self._path_label: tk.Label | None = None
        self._position_label: tk.Label | None = None

        self.title(
            "Galerie EcoBiome"
        )

        self.geometry("1040x760")
        self.minsize(760, 560)
        self.resizable(True, True)
        self.transient(parent)

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self._build_header()
        self._build_image_area()
        self._build_footer()
        self._show_current()

        self.bind(
            "<Left>",
            self._previous_shortcut,
        )

        self.bind(
            "<Right>",
            self._next_shortcut,
        )

        self.bind(
            "<Escape>",
            self._close_shortcut,
        )

        self.grab_set()
        self.focus_set()

    def _build_header(self) -> None:
        """Build the image title and position."""
        header = tk.Frame(
            self,
            background=self._theme.surface,
            padx=20,
            pady=16,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self._title_label = tk.Label(
            header,
            text="Galerie du projet",
            background=header["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 15),
            anchor="w",
        )

        self._title_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
        )

        self._position_label = tk.Label(
            header,
            text=self._navigator.position_label,
            background=header["background"],
            foreground=self._theme.accent,
            font=("Segoe UI Semibold", 11),
        )

        self._position_label.pack(
            side=tk.RIGHT,
        )

    def _build_image_area(self) -> None:
        """Build the main image and metadata area."""
        body = tk.Frame(
            self,
            background=self._theme.background,
            padx=20,
            pady=18,
        )

        body.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        body.grid_columnconfigure(
            0,
            weight=1,
        )

        body.grid_rowconfigure(
            0,
            weight=1,
        )

        image_container = tk.Frame(
            body,
            background=self._theme.surface_elevated,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=10,
            pady=10,
        )

        image_container.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self._image_label = tk.Label(
            image_container,
            text="",
            background=image_container["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 11),
        )

        self._image_label.pack(
            fill=tk.BOTH,
            expand=True,
        )

        metadata = tk.Frame(
            body,
            background=self._theme.surface,
            highlightthickness=1,
            highlightbackground=self._theme.border,
            padx=16,
            pady=12,
        )

        metadata.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(12, 0),
        )

        self._metadata_label = tk.Label(
            metadata,
            text="",
            background=metadata["background"],
            foreground=self._theme.text_primary,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        )

        self._metadata_label.pack(
            fill=tk.X,
        )

        self._path_label = tk.Label(
            metadata,
            text="",
            background=metadata["background"],
            foreground=self._theme.text_secondary,
            font=("Segoe UI", 8),
            anchor="w",
            justify=tk.LEFT,
            wraplength=900,
        )

        self._path_label.pack(
            fill=tk.X,
            pady=(5, 0),
        )

    def _build_footer(self) -> None:
        """Build navigation and closing controls."""
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

        navigation_state: Literal["normal", "disabled"] = (
            "normal"
            if len(self._navigator.items) > 1
            else "disabled"
        )

        tk.Button(
            footer,
            text="← Précédente",
            command=self._show_previous,
            state=navigation_state,
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            disabledforeground=self._theme.text_secondary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.LEFT)

        tk.Button(
            footer,
            text="Suivante →",
            command=self._show_next,
            state=navigation_state,
            background=self._theme.surface_elevated,
            foreground=self._theme.text_primary,
            disabledforeground=self._theme.text_secondary,
            activebackground=self._theme.border,
            activeforeground=self._theme.text_primary,
            relief=tk.FLAT,
            padx=16,
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
            background=self._theme.accent,
            foreground="#FFFFFF",
            activebackground=self._theme.accent,
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

    def _show_current(self) -> None:
        """Render the selected image and its metadata."""
        item = self._navigator.current

        if self._position_label is not None:
            self._position_label.configure(
                text=self._navigator.position_label
            )

        if item is None:
            if self._image_label is not None:
                self._image_label.configure(
                    text="Aucune image disponible.",
                    image="",
                )

            return

        if self._title_label is not None:
            self._title_label.configure(
                text=item.title
            )

        if self._metadata_label is not None:
            self._metadata_label.configure(
                text=(
                    f"{item.date_label}"
                    f"  ·  {item.size_label}"
                    f"  ·  {item.suffix.upper()}"
                )
            )

        if self._path_label is not None:
            self._path_label.configure(
                text=str(item.path)
            )

        if self._image_label is None:
            return

        try:
            with Image.open(item.path) as source:
                image = source.convert("RGB")

                image.thumbnail(
                    (900, 520),
                    Image.Resampling.LANCZOS,
                )

                background = Image.new(
                    "RGB",
                    (900, 520),
                    self._theme.surface_elevated,
                )

                x_position = (
                    background.width
                    - image.width
                ) // 2

                y_position = (
                    background.height
                    - image.height
                ) // 2

                background.paste(
                    image,
                    (
                        x_position,
                        y_position,
                    ),
                )

            self._photo = ImageTk.PhotoImage(
                background,
                master=self,
            )

            self._image_label.configure(
                image=self._photo,
                text="",
            )

        except OSError:
            self._photo = None

            self._image_label.configure(
                image="",
                text=(
                    "Cette image ne peut pas "
                    "être affichée."
                ),
            )

    def _show_previous(self) -> None:
        """Display the previous image."""
        self._navigator = (
            self._navigator.previous()
        )

        self._show_current()

    def _show_next(self) -> None:
        """Display the next image."""
        self._navigator = (
            self._navigator.next()
        )

        self._show_current()

    def _previous_shortcut(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle the left-arrow shortcut."""
        self._show_previous()
        return "break"

    def _next_shortcut(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle the right-arrow shortcut."""
        self._show_next()
        return "break"

    def _close_shortcut(
        self,
        _event: tk.Event,
    ) -> str:
        """Handle the escape shortcut."""
        self.destroy()
        return "break"
