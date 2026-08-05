"""Encoding checks for the canonical Python package."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src" / "ecobiome"


def test_canonical_python_sources_are_utf8_without_bom() -> None:
    invalid_files: list[str] = []

    for path in sorted(SOURCE_ROOT.rglob("*.py")):
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
        "Canonical Python sources are not UTF-8 without BOM:\n"
        + "\n".join(invalid_files)
    )