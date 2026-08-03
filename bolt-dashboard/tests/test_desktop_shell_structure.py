"""Structural regression tests for the fixed desktop shell."""

import ast
from pathlib import Path

APP_PATH = Path(
    "src/ecobiome/ui/desktop/app.py"
)
RESPONSIVE_PATH = Path(
    "src/ecobiome/ui/desktop/responsive.py"
)
DEMO_MEDIA_PATH = Path(
    "src/ecobiome/ui/desktop/demo_media.py"
)


def _app_methods() -> tuple[str, dict[str, ast.FunctionDef]]:
    source = APP_PATH.read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    application_class = next(
        node
        for node in tree.body
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "EcoBiomeDesktopApp"
        )
    )

    return source, {
        node.name: node
        for node in application_class.body
        if isinstance(node, ast.FunctionDef)
    }


def test_shell_is_mounted_directly_in_root() -> None:
    source, methods = _app_methods()
    build_interface = ast.get_source_segment(
        source,
        methods["_build_interface"],
    )

    assert build_interface is not None
    assert "self._root" in build_interface
    assert "self._dashboard_parent" not in source


def test_hero_belongs_to_main_area() -> None:
    source, methods = _app_methods()
    main_area = ast.get_source_segment(
        source,
        methods["_build_main_area"],
    )

    assert main_area is not None
    assert "DashboardHeroBanner(" in main_area
    assert "ResponsiveDashboardViewport(" in main_area
    assert "self._build_header(" not in main_area


def test_legacy_visual_overlay_methods_are_removed() -> None:
    _source, methods = _app_methods()

    assert "_build_header" not in methods
    assert "_build_layout_toolbar" not in methods
    assert "_install_visual_enhancements" not in methods


def test_responsive_viewport_does_not_mutate_tk_scaling() -> None:
    source = RESPONSIVE_PATH.read_text(
        encoding="utf-8"
    )

    assert '"scaling"' not in source
    assert "tk.call" not in source
    assert "fit_content_height" in source


def test_demo_media_import_is_recursive() -> None:
    source = DEMO_MEDIA_PATH.read_text(
        encoding="utf-8"
    )

    assert 'directory.rglob("*")' in source
    assert "directory.iterdir()" not in source
