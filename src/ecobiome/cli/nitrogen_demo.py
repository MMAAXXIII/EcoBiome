"""CLI surface for the frozen reproducible nitrogen vertical."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ecobiome.reasoning.nitrogen_vertical_runtime_v1 import (
    build_frozen_g7a_nitrogen_vertical_demonstration_v1,
)


def add_nitrogen_demo_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the first user-visible nitrogen demonstration command."""
    parser = subparsers.add_parser(
        "nitrogen-demo",
        help=(
            "Render the reviewed reproducible nitrogen vertical "
            "(explicit extents; no kinetics)."
        ),
    )
    parser.add_argument(
        "--scientific-foundation",
        type=Path,
        required=True,
        help="Path to the exact reviewed Scientific Foundation V6 SQLite DB.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output representation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional UTF-8 output file; otherwise write to stdout.",
    )
    return parser


def _render_payload(demonstration: Any, output_format: str) -> str:
    if output_format == "markdown":
        return demonstration.render_markdown() + "\n"
    if output_format == "json":
        return (
            json.dumps(
                demonstration.canonical_payload(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    raise ValueError(f"unsupported nitrogen-demo format: {output_format!r}")


def _write_utf8(text: str, output_path: Path | None) -> None:
    if output_path is not None:
        path = output_path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def nitrogen_demo_command(args: argparse.Namespace) -> int:
    """Reproduce and render the frozen reviewed vertical."""
    demonstration = build_frozen_g7a_nitrogen_vertical_demonstration_v1(
        args.scientific_foundation
    )
    text = _render_payload(demonstration, args.format)
    _write_utf8(text, args.output)
    return 0
