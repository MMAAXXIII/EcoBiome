from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    PROJECT_ROOT / "collectors" / "ia_piped_collector.py",
    PROJECT_ROOT / "collectors" / "ia_youtube_html_collector.py",
)


def _qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def test_targeted_requests_calls_have_timeouts() -> None:
    missing_timeouts: list[str] = []

    for path in TARGETS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _qualified_name(node.func) != "requests.get":
                continue
            keyword_names = {
                keyword.arg
                for keyword in node.keywords
                if keyword.arg is not None
            }
            if "timeout" not in keyword_names:
                missing_timeouts.append(f"{path.name}:{node.lineno}")

    assert not missing_timeouts


def test_youtube_html_collector_has_no_bare_except() -> None:
    path = PROJECT_ROOT / "collectors" / "ia_youtube_html_collector.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bare_handlers = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is None
    ]
    assert not bare_handlers
