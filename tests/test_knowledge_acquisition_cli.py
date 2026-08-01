"""Tests for the transcript import command."""

import json
from pathlib import Path

from ecobiome.knowledge_acquisition.cli import main


def test_import_transcript_command(
    tmp_path: Path,
    capsys: object,
) -> None:
    transcript_path = tmp_path / "youtube.txt"
    output_path = tmp_path / "source_manifest.json"

    transcript_path.write_text(
        "A large volume improves thermal stability.\n\n"
        "Stable temperature can reduce biological stress.",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "import-transcript",
            str(transcript_path),
            "--title",
            "Aquatic thermal stability",
            "--locator",
            "https://www.youtube.com/watch?v=example",
            "--author",
            "Example channel",
            "--source-type",
            "youtube",
            "--maximum-passage-characters",
            "60",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.is_file()

    manifest = json.loads(output_path.read_text(encoding="utf-8"))

    assert manifest["source"]["title"] == "Aquatic thermal stability"
    assert manifest["source"]["source_type"] == "youtube"
    assert manifest["transcript"]["passage_count"] == 2
    assert len(manifest["passages"]) == 2


def test_cli_without_command_displays_help(
    capsys: object,
) -> None:
    exit_code = main([])

    assert exit_code == 0
