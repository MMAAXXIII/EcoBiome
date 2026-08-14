"""Text preparation for later scientific claim extraction."""

import re


def _split_oversized_paragraph(
    paragraph: str,
    *,
    maximum_characters: int,
) -> tuple[str, ...]:
    """Split one oversized paragraph without exceeding the limit."""
    remaining = paragraph.strip()
    chunks: list[str] = []

    while len(remaining) > maximum_characters:
        window = remaining[: maximum_characters + 1]
        sentence_breaks = [
            match.start()
            for match in re.finditer(r"(?<=[.!?])\s+", window)
            if 0 < match.start() <= maximum_characters
        ]

        if sentence_breaks:
            split_at = sentence_breaks[-1]
        else:
            whitespace_breaks = [
                match.start()
                for match in re.finditer(r"\s+", window)
                if 0 < match.start() <= maximum_characters
            ]
            split_at = (
                whitespace_breaks[-1]
                if whitespace_breaks
                else maximum_characters
            )

        chunk = remaining[:split_at].strip()

        if not chunk:
            split_at = maximum_characters
            chunk = remaining[:split_at]

        chunks.append(chunk)
        remaining = remaining[split_at:].strip()

    if remaining:
        chunks.append(remaining)

    return tuple(chunks)


def split_into_passages(
    text: str,
    *,
    maximum_characters: int = 1_500,
) -> tuple[str, ...]:
    """Split normalized text into reviewable passages."""
    if maximum_characters <= 0:
        raise ValueError("maximum_characters must be greater than zero.")

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    passages: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > maximum_characters:
            if current:
                passages.append(current)
                current = ""

            passages.extend(
                _split_oversized_paragraph(
                    paragraph,
                    maximum_characters=maximum_characters,
                )
            )
            continue

        candidate = (
            paragraph
            if not current
            else f"{current}\n\n{paragraph}"
        )

        if len(candidate) <= maximum_characters:
            current = candidate
            continue

        passages.append(current)
        current = paragraph

    if current:
        passages.append(current)

    return tuple(passages)
