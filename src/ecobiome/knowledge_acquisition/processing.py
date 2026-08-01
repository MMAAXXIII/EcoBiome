"""Text preparation for later scientific claim extraction."""

import re


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
        candidate = (
            paragraph
            if not current
            else f"{current}\n\n{paragraph}"
        )

        if len(candidate) <= maximum_characters:
            current = candidate
            continue

        if current:
            passages.append(current)

        current = paragraph

    if current:
        passages.append(current)

    return tuple(passages)
