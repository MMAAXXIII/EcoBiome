from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pytest

from ecobiome.knowledge_acquisition.acquisition import (
    AcquisitionRequest,
    AdapterRegistry,
)
from ecobiome.knowledge_acquisition.adapters.local_file import LocalFileAdapter
from ecobiome.knowledge_acquisition.adapters.youtube import (
    MetadataSnapshot,
    TimedTranscript,
    TimedTranscriptSnippet,
    YouTubeAcquisitionError,
    YouTubeAdapter,
    YouTubeMetadataUnavailable,
    YouTubeTranscriptUnavailable,
    canonical_youtube_url,
    extract_youtube_video_id,
)
from ecobiome.knowledge_acquisition.collector_acquire import (
    acquire_source,
    default_adapter_registry,
)
from ecobiome.knowledge_acquisition.collector_cli import _preferred_languages
from ecobiome.knowledge_acquisition.persistence import CollectorStore

VIDEO_ID = "A1VKJkJVqC8"
WATCH_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


@dataclass
class _FakeMetadataClient:
    fail: bool = False

    def fetch(
        self,
        *,
        video_id: str,
        canonical_url: str,
    ) -> MetadataSnapshot:
        assert video_id == VIDEO_ID
        assert canonical_url == WATCH_URL
        if self.fail:
            raise YouTubeMetadataUnavailable("metadata unavailable")
        return MetadataSnapshot(
            data={
                "id": VIDEO_ID,
                "title": "Medaka varieties",
                "description": "Longfin medaka observations.",
                "channel": "Fixture Channel",
                "channel_id": "channel-fixture",
                "duration": 120.5,
                "upload_date": "20260801",
            },
            tool_version="fixture-ytdlp",
        )


@dataclass
class _FakeTranscriptClient:
    fail_code: str | None = None
    is_generated: bool = False

    def fetch(
        self,
        *,
        video_id: str,
        preferred_languages: tuple[str, ...],
    ) -> TimedTranscript:
        assert video_id == VIDEO_ID
        assert preferred_languages == ("fr", "en")
        if self.fail_code is not None:
            raise YouTubeTranscriptUnavailable(
                self.fail_code,
                "fixture transcript failure",
            )
        return TimedTranscript(
            language="French",
            language_code="fr",
            is_generated=self.is_generated,
            snippets=(
                TimedTranscriptSnippet(
                    text="Premier segment.",
                    start=1.25,
                    duration=2.5,
                ),
                TimedTranscriptSnippet(
                    text="Deuxieme segment.",
                    start=3.0,
                    duration=2.75,
                ),
            ),
            available=(
                {
                    "language": "French",
                    "language_code": "fr",
                    "is_generated": self.is_generated,
                    "is_translatable": True,
                },
                {
                    "language": "English",
                    "language_code": "en",
                    "is_generated": True,
                    "is_translatable": True,
                },
            ),
            tool_version="fixture-transcript-api",
        )


def _registry(
    *,
    metadata_fail: bool = False,
    transcript_fail_code: str | None = None,
) -> AdapterRegistry:
    return AdapterRegistry(
        (
            YouTubeAdapter(
                metadata_client=_FakeMetadataClient(metadata_fail),
                transcript_client=_FakeTranscriptClient(
                    transcript_fail_code
                ),
            ),
            LocalFileAdapter(),
        )
    )


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (WATCH_URL, VIDEO_ID),
        (f"https://youtu.be/{VIDEO_ID}", VIDEO_ID),
        (f"https://www.youtube.com/shorts/{VIDEO_ID}", VIDEO_ID),
        (f"https://m.youtube.com/watch?v={VIDEO_ID}", VIDEO_ID),
        (f"https://www.youtube.com/embed/{VIDEO_ID}", VIDEO_ID),
        (f"https://www.youtube.com/live/{VIDEO_ID}", VIDEO_ID),
    ],
)
def test_extract_youtube_video_id_allowlisted_forms(
    url: str,
    expected: str,
) -> None:
    assert extract_youtube_video_id(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        f"https://youtube.com.evil.example/watch?v={VIDEO_ID}",
        f"https://example.com/watch?v={VIDEO_ID}",
        f"ftp://www.youtube.com/watch?v={VIDEO_ID}",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/playlist?list=fixture",
    ],
)
def test_extract_youtube_video_id_rejects_non_video_or_non_allowlisted(
    url: str,
) -> None:
    with pytest.raises(ValueError):
        extract_youtube_video_id(url)


def test_default_registry_routes_youtube_without_network() -> None:
    adapter, match = default_adapter_registry().select(
        AcquisitionRequest(WATCH_URL)
    )
    assert adapter.name == "youtube"
    assert match.priority == 200
    assert match.reason == "allowlisted_youtube_video_url"


def test_youtube_adapter_acquires_metadata_transcript_and_timecodes(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"

    run = acquire_source(
        source=WATCH_URL,
        database=database,
        preferred_languages=("fr", "en"),
        registry=_registry(),
    )

    assert run.adapter_name == "youtube"
    assert run.result.outcome == "succeeded"
    assert run.result.diagnostics == ()
    assert run.result.canonical_source.canonical_locator == WATCH_URL
    assert run.result.canonical_source.title == "Medaka varieties"
    assert run.result.canonical_source.author == "Fixture Channel"
    assert run.result.canonical_source.language == "fr"

    payload_keys = {item.logical_key for item in run.receipt.payloads}
    assert payload_keys == {"youtube-metadata", "youtube-transcript"}

    result_by_key = {
        item.logical_key: item
        for item in run.result.representations
    }
    receipt_by_key = {
        item.logical_key: item
        for item in run.receipt.representations
    }

    timed = result_by_key["youtube-timed-transcript"]
    assert timed.text == "Premier segment.\nDeuxieme segment."
    assert len(timed.segments) == 2
    assert timed.segments[0].start_char == 0
    assert timed.segments[0].end_char == len("Premier segment.")
    assert timed.segments[0].start_seconds == 1.25
    assert timed.segments[0].end_seconds == 3.75

    second_start = len("Premier segment.\n")
    assert timed.segments[1].start_char == second_start
    assert timed.segments[1].end_char == (
        second_start + len("Deuxieme segment.")
    )
    # Time overlap is authoritative provider data and is preserved.
    assert timed.segments[1].start_seconds == 3.0
    assert timed.segments[1].end_seconds == 5.75

    persisted = receipt_by_key["youtube-timed-transcript"]
    assert len(persisted.segment_ids) == 2
    assert persisted.segment_review_statuses == ("pending", "pending")

    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            """
            SELECT
                segment_index,
                text_inline,
                representation_char_start,
                representation_char_end,
                start_seconds_decimal,
                end_seconds_decimal
            FROM segments
            WHERE representation_id = ?
            ORDER BY segment_index
            """,
            (str(persisted.representation_id),),
        ).fetchall()

    assert rows == [
        (
            1,
            "Premier segment.",
            0,
            len("Premier segment."),
            "1.25",
            "3.75",
        ),
        (
            2,
            "Deuxieme segment.",
            second_start,
            second_start + len("Deuxieme segment."),
            "3",
            "5.75",
        ),
    ]

    summary = CollectorStore(database).summary()
    assert summary["sources"] == 1
    assert summary["raw_artifacts"] == 2
    assert summary["retrievals"] == 2
    assert summary["representations"] == 3
    assert summary["segments"] == 3
    assert summary["documents"] == 2
    assert summary["acquisition_jobs"] == 1


def test_exact_youtube_reacquisition_preserves_timed_segment_review(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"
    registry = _registry()

    first = acquire_source(
        source=WATCH_URL,
        database=database,
        preferred_languages=("fr", "en"),
        registry=registry,
    )
    timed_first = next(
        item
        for item in first.receipt.representations
        if item.logical_key == "youtube-timed-transcript"
    )
    first_segment = timed_first.segment_ids[0]

    store = CollectorStore(database)
    store.record_review_decision(
        target_type="passage",
        target_id=first_segment,
        decision="accept",
    )

    second = acquire_source(
        source=f"https://youtu.be/{VIDEO_ID}",
        database=database,
        preferred_languages=("fr", "en"),
        registry=registry,
    )
    timed_second = next(
        item
        for item in second.receipt.representations
        if item.logical_key == "youtube-timed-transcript"
    )

    assert second.receipt.source_id == first.receipt.source_id
    assert timed_second.representation_id == timed_first.representation_id
    assert timed_second.duplicate
    assert timed_second.segment_ids == timed_first.segment_ids
    assert timed_second.segment_review_statuses == ("accepted", "pending")

    summary = store.summary()
    assert summary["sources"] == 1
    assert summary["raw_artifacts"] == 2
    assert summary["retrievals"] == 4
    assert summary["acquisition_jobs"] == 2


def test_no_transcript_is_partial_metadata_acquisition(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"

    run = acquire_source(
        source=WATCH_URL,
        database=database,
        preferred_languages=("fr", "en"),
        registry=_registry(transcript_fail_code="no_transcript"),
    )

    assert run.result.outcome == "partial"
    assert [item.code for item in run.result.diagnostics] == [
        "no_transcript"
    ]
    assert {item.logical_key for item in run.receipt.payloads} == {
        "youtube-metadata"
    }
    assert {
        item.logical_key for item in run.receipt.representations
    } == {
        "youtube-metadata-json",
        "youtube-description",
    }

    summary = CollectorStore(database).summary()
    assert summary["failed_jobs"] == 0
    assert summary["job_diagnostics"] == 1


def test_metadata_failure_can_still_persist_timed_transcript(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"

    run = acquire_source(
        source=WATCH_URL,
        database=database,
        preferred_languages=("fr", "en"),
        registry=_registry(metadata_fail=True),
    )

    assert run.result.outcome == "partial"
    assert [item.code for item in run.result.diagnostics] == [
        "metadata_failed"
    ]
    assert run.result.canonical_source.title == VIDEO_ID
    assert run.result.canonical_source.language == "fr"
    assert {item.logical_key for item in run.receipt.payloads} == {
        "youtube-transcript"
    }


def test_youtube_both_clients_fail_records_failed_job(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"

    with pytest.raises(
        YouTubeAcquisitionError,
        match="metadata and transcript acquisition both failed",
    ):
        acquire_source(
            source=WATCH_URL,
            database=database,
            preferred_languages=("fr", "en"),
            registry=_registry(
                metadata_fail=True,
                transcript_fail_code="rate_limited",
            ),
        )

    summary = CollectorStore(database).summary()
    assert summary["failed_jobs"] == 1
    assert summary["raw_artifacts"] == 0
    assert summary["retrievals"] == 0


def test_youtube_metadata_payload_is_bounded(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"

    with pytest.raises(ValueError, match="maximum_input_bytes"):
        acquire_source(
            source=WATCH_URL,
            database=database,
            preferred_languages=("fr", "en"),
            maximum_input_bytes=20,
            registry=_registry(),
        )

    summary = CollectorStore(database).summary()
    assert summary["failed_jobs"] == 1
    assert summary["raw_artifacts"] == 0


def test_preferred_languages_parser() -> None:
    assert _preferred_languages("fr,en") == ("fr", "en")
    assert _preferred_languages(" fr , en ") == ("fr", "en")
    assert _preferred_languages("") == ()

    with pytest.raises(ValueError, match="duplicate"):
        _preferred_languages("fr,fr")


def test_canonical_youtube_url_is_stable() -> None:
    assert canonical_youtube_url(VIDEO_ID) == WATCH_URL


def test_transcript_raw_payload_preserves_provider_duration(
    tmp_path: Path,
) -> None:
    database = tmp_path / "collector.sqlite3"

    run = acquire_source(
        source=WATCH_URL,
        database=database,
        preferred_languages=("fr", "en"),
        registry=_registry(),
    )

    raw_receipt = next(
        item
        for item in run.receipt.payloads
        if item.logical_key == "youtube-transcript"
    )
    payload = json.loads(raw_receipt.stored_path.read_text(encoding="utf-8"))

    assert payload["snippets"][0] == {
        "duration": 2.5,
        "start": 1.25,
        "text": "Premier segment.",
    }
    assert payload["is_generated"] is False
