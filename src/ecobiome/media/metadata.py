"""Descriptive metadata associated with media assets."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class MediaMetadata:
    """User-controlled descriptive metadata for one media asset."""

    title: str
    description: str = ""
    captured_at: datetime | None = None
    tags: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate and normalize descriptive metadata."""
        title = self.title.strip()
        description = self.description.strip()

        if not title:
            raise ValueError(
                "Media title cannot be empty."
            )

        if (
            self.captured_at is not None
            and self.captured_at.tzinfo is None
        ):
            raise ValueError(
                "Media capture timestamp must be timezone-aware."
            )

        normalized_tags = tuple(
            dict.fromkeys(
                tag.strip().lower()
                for tag in self.tags
                if tag.strip()
            )
        )

        normalized_attributes: dict[str, str] = {}

        for raw_key, raw_value in self.attributes:
            key = raw_key.strip()
            value = raw_value.strip()

            if not key:
                raise ValueError(
                    "Media attribute keys cannot be empty."
                )

            normalized_attributes[key] = value

        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "description",
            description,
        )
        object.__setattr__(
            self,
            "tags",
            normalized_tags,
        )
        object.__setattr__(
            self,
            "attributes",
            tuple(normalized_attributes.items()),
        )

    @property
    def attribute_map(self) -> dict[str, str]:
        """Return attributes as an independent dictionary."""
        return dict(self.attributes)
