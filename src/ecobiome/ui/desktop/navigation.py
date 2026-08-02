"""Navigation helpers for the EcoBiome desktop dashboard."""

from __future__ import annotations

import re
import tkinter as tk
import unicodedata
from collections.abc import Callable

_GALLERY_LABELS = frozenset(
    {
        "galerie",
        "galerie complete",
        "ouvrir la galerie",
        "ouvrir la galerie complete",
        "voir la galerie",
    }
)

_GALLERY_SUFFIXES = (
    " ouvrir la galerie",
    " ouvrir la galerie complete",
)


def normalize_navigation_text(
    text: object,
) -> str:
    """Normalize one navigation label for stable matching."""
    if not isinstance(text, str):
        return ""

    decomposed = unicodedata.normalize(
        "NFKD",
        text,
    )

    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )

    alphanumeric = re.sub(
        r"[^a-zA-Z0-9]+",
        " ",
        without_accents,
    )

    return " ".join(
        alphanumeric.casefold().split()
    )


def is_gallery_navigation_text(
    text: object,
) -> bool:
    """Return whether one label represents a gallery action."""
    normalized = normalize_navigation_text(
        text
    )

    return (
        normalized in _GALLERY_LABELS
        or normalized.endswith(
            _GALLERY_SUFFIXES
        )
    )


def bind_gallery_navigation(
    root: tk.Misc,
    callback: Callable[[], None],
) -> int:
    """Connect every explicit gallery navigation entry."""
    bound_widgets = 0
    bound_widget_paths: set[str] = set()

    def handle_click(
        _event: tk.Event,
    ) -> str:
        callback()
        return "break"

    def bind_widget(
        widget: tk.Misc,
    ) -> bool:
        nonlocal bound_widgets

        widget_path = str(
            widget
        )

        if widget_path in bound_widget_paths:
            return False

        if isinstance(
            widget,
            tk.Button,
        ):
            widget.configure(
                command=callback,
                cursor="hand2",
            )

        elif isinstance(
            widget,
            (
                tk.Label,
                tk.Frame,
                tk.LabelFrame,
            ),
        ):
            widget.configure(
                cursor="hand2",
            )

            widget.bind(
                "<Button-1>",
                handle_click,
            )

        else:
            return False

        bound_widget_paths.add(
            widget_path
        )

        bound_widgets += 1

        return True

    def walk(
        widget: tk.Misc,
    ) -> None:
        for child in widget.winfo_children():
            label_text = ""

            if isinstance(
                child,
                (
                    tk.Button,
                    tk.Label,
                ),
            ):
                label_text = str(
                    child.cget("text")
                )

            if is_gallery_navigation_text(
                label_text
            ):
                bind_widget(
                    child
                )

                parent = child.master

                if (
                    isinstance(
                        parent,
                        (
                            tk.Frame,
                            tk.LabelFrame,
                        ),
                    )
                    and len(
                        parent.winfo_children()
                    )
                    <= 4
                ):
                    bind_widget(
                        parent
                    )

            walk(
                child
            )

    walk(
        root
    )

    return bound_widgets
