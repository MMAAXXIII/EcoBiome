"""YouTube metadata and timed-transcript acquisition adapter."""

from __future__ import annotations

import importlib.metadata
import json
import os
import re
import threading
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionContext,
    AcquisitionDiagnostic,
    AcquisitionError,
    AcquisitionRequest,
    AcquisitionResult,
    AdapterMatch,
    CanonicalSource,
    RepresentationDraft,
    RetrievedPayload,
    SegmentDraft,
)
from ecobiome.knowledge_acquisition.source import SourceType

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
    }
)
YOUTU_BE_HOSTS = frozenset({"youtu.be", "www.youtu.be"})
_YTDLP_IMPORT_LOCK = threading.Lock()


class YouTubeAcquisitionError(AcquisitionError):
    """YouTube acquisition produced no usable result."""


class YouTubeMetadataUnavailable(YouTubeAcquisitionError):
    """yt-dlp metadata extraction failed."""


class YouTubeTranscriptUnavailable(YouTubeAcquisitionError):
    """Transcript retrieval failed with a structured diagnostic code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class MetadataSnapshot:
    """Serializable YouTube metadata returned by the metadata client."""

    data: dict[str, object]
    tool_version: str


@dataclass(frozen=True, slots=True)
class TimedTranscriptSnippet:
    """One authoritative transcript snippet as returned by the provider."""

    text: str
    start: float
    duration: float


@dataclass(frozen=True, slots=True)
class TimedTranscript:
    """Selected transcript plus availability/provenance metadata."""

    language: str
    language_code: str
    is_generated: bool
    snippets: tuple[TimedTranscriptSnippet, ...]
    available: tuple[dict[str, object], ...]
    tool_version: str


class MetadataClient(Protocol):
    """Metadata retrieval boundary, injectable for no-network tests."""

    def fetch(
        self,
        *,
        video_id: str,
        canonical_url: str,
    ) -> MetadataSnapshot:
        """Return bounded-serialization-ready metadata."""
        ...


class TranscriptClient(Protocol):
    """Transcript retrieval boundary, injectable for no-network tests."""

    def fetch(
        self,
        *,
        video_id: str,
        preferred_languages: tuple[str, ...],
    ) -> TimedTranscript:
        """Return one selected timed transcript."""
        ...


def extract_youtube_video_id(locator: str) -> str:
    """Extract one strict YouTube video ID from an allowlisted URL."""
    candidate = locator.strip()
    if not candidate:
        raise ValueError("YouTube locator is empty.")

    try:
        parts = urllib.parse.urlsplit(candidate)
    except ValueError as exc:
        raise ValueError("YouTube URL could not be parsed.") from exc

    if parts.scheme.lower() not in {"http", "https"}:
        raise ValueError("YouTube adapter accepts HTTP(S) URLs only.")

    host = (parts.hostname or "").lower().rstrip(".")
    video_id = ""

    if host in YOUTU_BE_HOSTS:
        video_id = parts.path.strip("/").split("/", 1)[0]
    elif host in YOUTUBE_HOSTS:
        path_parts = [item for item in parts.path.split("/") if item]
        if parts.path in {"", "/watch"}:
            values = urllib.parse.parse_qs(parts.query).get("v", [])
            if len(values) == 1:
                video_id = values[0]
        elif len(path_parts) >= 2 and path_parts[0] in {
            "embed",
            "shorts",
            "live",
        }:
            video_id = path_parts[1]
    else:
        raise ValueError("URL host is not an allowlisted YouTube host.")

    if not VIDEO_ID_RE.fullmatch(video_id):
        raise ValueError("YouTube URL does not contain a valid video ID.")
    return video_id


def canonical_youtube_url(video_id: str) -> str:
    """Return the single canonical watch URL used for logical identity."""
    if not VIDEO_ID_RE.fullmatch(video_id):
        raise ValueError("Invalid YouTube video ID.")
    return f"https://www.youtube.com/watch?v={video_id}"


def _selected_metadata(data: dict[str, object]) -> dict[str, object]:
    """Retain useful, reproducible yt-dlp fields without format URLs."""
    keys = (
        "id",
        "title",
        "description",
        "duration",
        "timestamp",
        "release_timestamp",
        "upload_date",
        "release_date",
        "uploader",
        "uploader_id",
        "channel",
        "channel_id",
        "channel_url",
        "webpage_url",
        "language",
        "categories",
        "tags",
        "availability",
        "live_status",
        "age_limit",
        "view_count",
        "like_count",
        "comment_count",
        "extractor",
        "extractor_key",
    )
    return {
        key: data[key]
        for key in keys
        if key in data and data[key] is not None
    }


class YtDlpMetadataClient:
    """Metadata client using yt-dlp with media download and plugins disabled."""

    def fetch(
        self,
        *,
        video_id: str,
        canonical_url: str,
    ) -> MetadataSnapshot:
        """Retrieve metadata only from the canonical YouTube watch URL."""
        if canonical_url != canonical_youtube_url(video_id):
            raise ValueError("Metadata client requires canonical YouTube URL.")

        previous_no_plugins = os.environ.get("YTDLP_NO_PLUGINS")
        try:
            with _YTDLP_IMPORT_LOCK:
                os.environ["YTDLP_NO_PLUGINS"] = "1"
                import yt_dlp  # type: ignore[import-untyped]
        except Exception as exc:
            raise YouTubeMetadataUnavailable(
                f"Unable to import yt-dlp: {exc}"
            ) from exc
        finally:
            if previous_no_plugins is None:
                os.environ.pop("YTDLP_NO_PLUGINS", None)
            else:
                os.environ["YTDLP_NO_PLUGINS"] = previous_no_plugins

        options: dict[str, object] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "retries": 1,
            "extractor_retries": 1,
            "cachedir": False,
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(canonical_url, download=False)
                sanitized = ydl.sanitize_info(info)
        except Exception as exc:
            raise YouTubeMetadataUnavailable(
                f"yt-dlp metadata extraction failed: {exc}"
            ) from exc

        if not isinstance(sanitized, dict):
            raise YouTubeMetadataUnavailable(
                "yt-dlp returned non-dictionary metadata."
            )

        try:
            version = importlib.metadata.version("yt-dlp")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"

        selected = _selected_metadata(
            {str(key): value for key, value in sanitized.items()}
        )
        selected["ecobiome_metadata_profile"] = "youtube-v1"
        selected["video_id"] = video_id
        return MetadataSnapshot(data=selected, tool_version=version)


def _timeout_session() -> Any:
    """Return a requests session with mandatory default request timeouts."""
    import requests

    session: Any = requests.Session()
    original_request = session.request

    def request_with_timeout(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", (5.0, 30.0))
        return original_request(*args, **kwargs)

    session.request = request_with_timeout
    session.trust_env = False
    return session


class YouTubeTranscriptApiClient:
    """Transcript client using youtube-transcript-api's current instance API."""

    def fetch(
        self,
        *,
        video_id: str,
        preferred_languages: tuple[str, ...],
    ) -> TimedTranscript:
        """List, select, and fetch one transcript without translation."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                AgeRestricted,
                InvalidVideoId,
                IpBlocked,
                NoTranscriptFound,
                PoTokenRequired,
                RequestBlocked,
                TranscriptsDisabled,
                VideoUnavailable,
                VideoUnplayable,
            )
        except Exception as exc:
            raise YouTubeTranscriptUnavailable(
                "transcript_client_unavailable",
                f"Unable to import youtube-transcript-api: {exc}",
            ) from exc

        try:
            api = YouTubeTranscriptApi(
                http_client=_timeout_session()
            )
            transcript_list = api.list(video_id)
            available_objects = tuple(transcript_list)
        except (IpBlocked, RequestBlocked) as exc:
            raise YouTubeTranscriptUnavailable(
                "rate_limited",
                str(exc),
            ) from exc
        except TranscriptsDisabled as exc:
            raise YouTubeTranscriptUnavailable(
                "no_transcript",
                str(exc),
            ) from exc
        except (
            AgeRestricted,
            InvalidVideoId,
            PoTokenRequired,
            VideoUnavailable,
            VideoUnplayable,
        ) as exc:
            raise YouTubeTranscriptUnavailable(
                "video_unavailable",
                str(exc),
            ) from exc
        except Exception as exc:
            raise YouTubeTranscriptUnavailable(
                "transcript_failed",
                f"Transcript listing failed: {exc}",
            ) from exc

        if not available_objects:
            raise YouTubeTranscriptUnavailable(
                "no_transcript",
                "YouTube exposes no transcript for this video.",
            )

        available = tuple(
            {
                "language": str(item.language),
                "language_code": str(item.language_code),
                "is_generated": bool(item.is_generated),
                "is_translatable": bool(item.is_translatable),
            }
            for item in available_objects
        )

        selected: Any = None
        languages = tuple(
            language.strip()
            for language in preferred_languages
            if language.strip()
        )
        if languages:
            try:
                selected = transcript_list.find_transcript(languages)
            except NoTranscriptFound:
                selected = None

        if selected is None:
            manual = tuple(
                item
                for item in available_objects
                if not bool(item.is_generated)
            )
            selected = manual[0] if manual else available_objects[0]

        try:
            fetched = selected.fetch()
        except (IpBlocked, RequestBlocked) as exc:
            raise YouTubeTranscriptUnavailable(
                "rate_limited",
                str(exc),
            ) from exc
        except Exception as exc:
            raise YouTubeTranscriptUnavailable(
                "transcript_failed",
                f"Transcript fetch failed: {exc}",
            ) from exc

        snippets = tuple(
            TimedTranscriptSnippet(
                text=str(item.text),
                start=float(item.start),
                duration=float(item.duration),
            )
            for item in fetched
        )
        try:
            version = importlib.metadata.version("youtube-transcript-api")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"

        return TimedTranscript(
            language=str(fetched.language),
            language_code=str(fetched.language_code),
            is_generated=bool(fetched.is_generated),
            snippets=snippets,
            available=available,
            tool_version=version,
        )


class YouTubeAdapter:
    """Acquire YouTube metadata and timed transcripts without media download."""

    name = "youtube"
    version = "1"
    priority = 200

    def __init__(
        self,
        *,
        metadata_client: MetadataClient | None = None,
        transcript_client: TranscriptClient | None = None,
    ) -> None:
        self._metadata_client = metadata_client or YtDlpMetadataClient()
        self._transcript_client = (
            transcript_client or YouTubeTranscriptApiClient()
        )

    def match(self, request: AcquisitionRequest) -> AdapterMatch | None:
        """Match strict allowlisted YouTube video URLs only."""
        try:
            extract_youtube_video_id(request.locator)
        except ValueError:
            return None
        return AdapterMatch(
            priority=self.priority,
            reason="allowlisted_youtube_video_url",
        )

    def canonicalize(self, request: AcquisitionRequest) -> CanonicalSource:
        """Canonicalize without network access."""
        video_id = extract_youtube_video_id(request.locator)
        return CanonicalSource(
            source_type=SourceType.YOUTUBE.value,
            canonical_locator=canonical_youtube_url(video_id),
            title=video_id,
            language=request.language,
            metadata={"video_id": video_id, "adapter": self.name},
        )

    @staticmethod
    def _stage_bytes(
        *,
        context: AcquisitionContext,
        filename: str,
        raw: bytes,
    ) -> Path:
        """Write bounded bytes into the private acquisition staging area."""
        if len(raw) > context.maximum_input_bytes:
            raise ValueError(
                f"YouTube staged payload exceeds maximum_input_bytes: "
                f"{len(raw)} > {context.maximum_input_bytes}"
            )
        context.staging_directory.mkdir(parents=True, exist_ok=True)
        path = context.staging_directory / (
            f"{uuid4().hex}-{filename}"
        )
        path.write_bytes(raw)
        return path

    @staticmethod
    def _json_bytes(payload: object) -> bytes:
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")

    def acquire(
        self,
        request: AcquisitionRequest,
        context: AcquisitionContext,
    ) -> AcquisitionResult:
        """Acquire metadata and transcript independently, preserving partials."""
        canonical = self.canonicalize(request)
        video_id = str(canonical.metadata["video_id"])
        canonical_url = canonical.canonical_locator

        payloads: list[RetrievedPayload] = []
        representations: list[RepresentationDraft] = []
        diagnostics: list[AcquisitionDiagnostic] = []

        metadata_snapshot: MetadataSnapshot | None = None
        transcript: TimedTranscript | None = None

        try:
            metadata_snapshot = self._metadata_client.fetch(
                video_id=video_id,
                canonical_url=canonical_url,
            )
        except YouTubeMetadataUnavailable as exc:
            diagnostics.append(
                AcquisitionDiagnostic(
                    severity="warning",
                    code="metadata_failed",
                    message=str(exc),
                )
            )

        preferred_languages = request.preferred_languages
        if not preferred_languages and request.language:
            preferred_languages = (request.language,)
        if not preferred_languages:
            preferred_languages = ("fr", "en")

        try:
            transcript = self._transcript_client.fetch(
                video_id=video_id,
                preferred_languages=preferred_languages,
            )
        except YouTubeTranscriptUnavailable as exc:
            diagnostics.append(
                AcquisitionDiagnostic(
                    severity="warning",
                    code=exc.code,
                    message=str(exc),
                    details={
                        "preferred_languages": list(preferred_languages),
                    },
                )
            )

        if metadata_snapshot is None and transcript is None:
            raise YouTubeAcquisitionError(
                "YouTube metadata and transcript acquisition both failed."
            )

        source_metadata: dict[str, object] = {
            "video_id": video_id,
            "adapter": self.name,
        }
        title = video_id
        author = ""
        language = request.language

        if metadata_snapshot is not None:
            metadata = dict(metadata_snapshot.data)
            title = str(metadata.get("title") or video_id)
            author = str(
                metadata.get("channel")
                or metadata.get("uploader")
                or ""
            )
            language = str(metadata.get("language") or language)
            for key in (
                "channel_id",
                "uploader_id",
                "duration",
                "upload_date",
                "timestamp",
                "availability",
                "live_status",
            ):
                if key in metadata:
                    source_metadata[key] = metadata[key]

            metadata_raw = self._json_bytes(
                {
                    "tool": "yt-dlp",
                    "tool_version": metadata_snapshot.tool_version,
                    "video_id": video_id,
                    "metadata": metadata,
                }
            )
            metadata_path = self._stage_bytes(
                context=context,
                filename="youtube-metadata.json",
                raw=metadata_raw,
            )
            payloads.append(
                RetrievedPayload(
                    logical_key="youtube-metadata",
                    staged_path=metadata_path,
                    media_type="application/json",
                    original_locator=request.locator,
                    canonical_locator=canonical_url,
                    protocol="youtube-tool-output",
                    response_metadata={
                        "tool_name": "yt-dlp",
                        "tool_version": metadata_snapshot.tool_version,
                        "media_downloaded": False,
                    },
                )
            )
            representations.append(
                RepresentationDraft(
                    logical_key="youtube-metadata-json",
                    staged_path=metadata_path,
                    representation_kind="youtube_metadata_json",
                    media_type="application/json",
                    language="",
                    parent_payload_key="youtube-metadata",
                    derivation_method="yt_dlp_metadata_selection",
                    tool_name="yt-dlp",
                    tool_version=metadata_snapshot.tool_version,
                    derivation_parameters={
                        "profile": "youtube-v1",
                        "download": False,
                    },
                    metadata={"video_id": video_id},
                )
            )

            description = str(metadata.get("description") or "")
            if description:
                description_raw = description.encode("utf-8")
                description_path = self._stage_bytes(
                    context=context,
                    filename="youtube-description.txt",
                    raw=description_raw,
                )
                representations.append(
                    RepresentationDraft(
                        logical_key="youtube-description",
                        staged_path=description_path,
                        representation_kind="youtube_description",
                        media_type="text/plain; charset=utf-8",
                        language=language,
                        parent_payload_key="youtube-metadata",
                        derivation_method="extract_description",
                        tool_name=self.name,
                        tool_version=self.version,
                        derivation_parameters={
                            "field": "description",
                        },
                        metadata={"video_id": video_id},
                        text=description,
                    )
                )

        if transcript is not None:
            language = transcript.language_code or language
            transcript_payload = {
                "tool": "youtube-transcript-api",
                "tool_version": transcript.tool_version,
                "video_id": video_id,
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "available_transcripts": list(transcript.available),
                "snippets": [
                    {
                        "text": item.text,
                        "start": item.start,
                        "duration": item.duration,
                    }
                    for item in transcript.snippets
                ],
            }
            transcript_json = self._json_bytes(transcript_payload)
            transcript_json_path = self._stage_bytes(
                context=context,
                filename="youtube-transcript.json",
                raw=transcript_json,
            )
            payloads.append(
                RetrievedPayload(
                    logical_key="youtube-transcript",
                    staged_path=transcript_json_path,
                    media_type="application/json",
                    original_locator=request.locator,
                    canonical_locator=canonical_url,
                    protocol="youtube-tool-output",
                    response_metadata={
                        "tool_name": "youtube-transcript-api",
                        "tool_version": transcript.tool_version,
                        "language_code": transcript.language_code,
                        "is_generated": transcript.is_generated,
                    },
                )
            )

            pieces: list[str] = []
            segments: list[SegmentDraft] = []
            character_cursor = 0
            for source_index, snippet in enumerate(transcript.snippets):
                if not snippet.text:
                    continue
                if snippet.start < 0 or snippet.duration < 0:
                    raise YouTubeAcquisitionError(
                        "Transcript returned a negative time anchor."
                    )
                if pieces:
                    pieces.append("\n")
                    character_cursor += 1
                start_char = character_cursor
                pieces.append(snippet.text)
                character_cursor += len(snippet.text)
                end_char = character_cursor
                segments.append(
                    SegmentDraft(
                        text=snippet.text,
                        start_char=start_char,
                        end_char=end_char,
                        start_seconds=snippet.start,
                        end_seconds=snippet.start + snippet.duration,
                        metadata={
                            "source_index": source_index,
                            "duration_seconds": snippet.duration,
                            "is_generated": transcript.is_generated,
                        },
                    )
                )

            if segments:
                normalized_text = "".join(pieces)
                transcript_text_path = self._stage_bytes(
                    context=context,
                    filename="youtube-transcript.txt",
                    raw=normalized_text.encode("utf-8"),
                )
                representations.append(
                    RepresentationDraft(
                        logical_key="youtube-timed-transcript",
                        staged_path=transcript_text_path,
                        representation_kind="youtube_timed_transcript",
                        media_type="text/plain; charset=utf-8",
                        language=transcript.language_code,
                        parent_payload_key="youtube-transcript",
                        derivation_method="normalize_timed_transcript",
                        tool_name="youtube-transcript-api",
                        tool_version=transcript.tool_version,
                        derivation_parameters={
                            "separator": "\\n",
                            "translation_requested": False,
                        },
                        metadata={
                            "video_id": video_id,
                            "language": transcript.language,
                            "language_code": transcript.language_code,
                            "is_generated": transcript.is_generated,
                            "snippet_count": len(segments),
                        },
                        text=normalized_text,
                        segments=tuple(segments),
                    )
                )
            else:
                diagnostics.append(
                    AcquisitionDiagnostic(
                        severity="warning",
                        code="empty_transcript",
                        message=(
                            "Transcript was available but contained no "
                            "non-empty text snippets."
                        ),
                    )
                )

        enriched_source = CanonicalSource(
            source_type=SourceType.YOUTUBE.value,
            canonical_locator=canonical_url,
            title=title,
            author=author,
            language=language,
            metadata=source_metadata,
        )

        outcome = "succeeded" if not diagnostics else "partial"
        return AcquisitionResult(
            canonical_source=enriched_source,
            payloads=tuple(payloads),
            representations=tuple(representations),
            diagnostics=tuple(diagnostics),
            outcome=outcome,
        )
