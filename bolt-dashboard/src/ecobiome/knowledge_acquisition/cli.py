"""Command-line tools for knowledge acquisition."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from ecobiome.knowledge_acquisition.processing import split_into_passages
from ecobiome.knowledge_acquisition.source import SourceType
from ecobiome.knowledge_acquisition.transcript import load_transcript


def build_parser() -> argparse.ArgumentParser:
    """Create the knowledge-acquisition command parser."""
    parser = argparse.ArgumentParser(
        prog="ecobiome",
        description="EcoBiome scientific ecosystem platform.",
    )

    subparsers = parser.add_subparsers(dest="command")

    import_parser = subparsers.add_parser(
        "import-transcript",
        help="Import a transcript while preserving its provenance.",
    )

    import_parser.add_argument(
        "path",
        type=Path,
        help="Path to the UTF-8 transcript file.",
    )
    import_parser.add_argument(
        "--title",
        required=True,
        help="Human-readable source title.",
    )
    import_parser.add_argument(
        "--locator",
        required=True,
        help="Original URL or stable source locator.",
    )
    import_parser.add_argument(
        "--author",
        default=None,
        help="Source author or channel.",
    )
    import_parser.add_argument(
        "--language",
        default="fr",
        help="Transcript language code. Default: fr.",
    )
    import_parser.add_argument(
        "--source-type",
        choices=[member.value for member in SourceType],
        default=SourceType.TRANSCRIPT.value,
        help="Type of imported source.",
    )
    import_parser.add_argument(
        "--maximum-passage-characters",
        type=int,
        default=1_500,
        help="Maximum approximate size of one review passage.",
    )
    import_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON manifest output path.",
    )

    return parser


def import_transcript_command(args: argparse.Namespace) -> int:
    """Execute the transcript import command."""
    imported = load_transcript(
        args.path,
        title=args.title,
        locator=args.locator,
        author=args.author,
        language=args.language,
        source_type=SourceType(args.source_type),
    )

    passages = split_into_passages(
        imported.text,
        maximum_characters=args.maximum_passage_characters,
    )

    manifest = {
        "schema_version": "0.1",
        "source": {
            "id": str(imported.source.id),
            "title": imported.source.title,
            "source_type": imported.source.source_type.value,
            "locator": imported.source.locator,
            "author": imported.source.author,
            "language": imported.source.language,
            "description": imported.source.description,
            "imported_at": imported.source.imported_at.isoformat(),
        },
        "transcript": {
            "path": str(args.path),
            "character_count": len(imported.text),
            "passage_count": len(passages),
        },
        "passages": [
            {
                "index": index,
                "text": passage,
                "review_status": "imported",
            }
            for index, passage in enumerate(passages, start=1)
        ],
    }

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("=" * 58)
    print("EcoBiome — Import de transcription")
    print("=" * 58)
    print(f"Titre       : {imported.source.title}")
    print(f"Type        : {imported.source.source_type.value}")
    print(f"Langue      : {imported.source.language}")
    print(f"Caractères  : {len(imported.text)}")
    print(f"Passages    : {len(passages)}")
    print(f"Identifiant : {imported.source.id}")

    if args.output is not None:
        print(f"Manifeste   : {args.output}")

    print()
    print("Statut : importé — validation scientifique requise.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the EcoBiome command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import-transcript":
        return import_transcript_command(args)

    parser.print_help()
    return 0
