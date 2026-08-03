"""Transcript import utilities."""

from dataclasses import dataclass
from pathlib import Path

from ecobiome.knowledge_acquisition.source import (
    KnowledgeSource,
    SourceType,
)


@dataclass(frozen=True, slots=True)
class ImportedTranscript:
    """Pair one source record with its normalized transcript."""

    source: KnowledgeSource
    text: str

    def __post_init__(self) -> None:
        """Reject empty transcripts."""
        normalized = self.text.strip()

        if not normalized:
            raise ValueError("A transcript cannot be empty.")

        object.__setattr__(self, "text", normalized)


def load_transcript(
    path: Path,
    *,
    title: str,
    locator: str,
    author: str | None = None,
    language: str = "fr",
    source_type: SourceType = SourceType.TRANSCRIPT,
) -> ImportedTranscript:
    """Load one UTF-8 transcript and preserve its provenance."""
    if not path.is_file():
        raise FileNotFoundError(f"Transcript file not found: {path}")

    text = path.read_text(encoding="utf-8")

    source = KnowledgeSource(
        title=title,
        source_type=source_type,
        locator=locator,
        author=author,
        language=language,
    )

    return ImportedTranscript(source=source, text=text)
