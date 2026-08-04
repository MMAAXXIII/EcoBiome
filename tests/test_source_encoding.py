from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PYTHON_SOURCE_ROOTS = (
    "analyzers",
    "api",
    "cloud",
    "collector_core",
    "collectors",
    "database",
)


def test_collector_python_sources_are_utf8_without_bom() -> None:
    invalid_files: list[str] = []

    for root_name in PYTHON_SOURCE_ROOTS:
        root = PROJECT_ROOT / root_name

        if not root.exists():
            continue

        for path in sorted(root.rglob("*.py")):
            raw = path.read_bytes()

            if raw.startswith(b"\xef\xbb\xbf"):
                invalid_files.append(
                    f"{path.relative_to(PROJECT_ROOT)}: UTF-8 BOM"
                )
                continue

            try:
                raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                invalid_files.append(
                    f"{path.relative_to(PROJECT_ROOT)}: {exc}"
                )

    assert not invalid_files, (
        "Sources Python non conformes à UTF-8 sans BOM :\n"
        + "\n".join(invalid_files)
    )