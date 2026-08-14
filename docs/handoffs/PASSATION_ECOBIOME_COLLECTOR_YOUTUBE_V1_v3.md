# PASSATION — EcoBiome Collector Sprint C — YouTubeAdapter v1

Date: 2026-08-11
Status: guarded local integration candidate
Implementation branch: `feature/collector-cli-baseline`
Git add/commit/push/merge authorized: NO

## Validated baseline

Sprint B reached:

`COLLECTOR_ACQUIRE_LOCALFILE_VALIDATED_LOCAL`

Real-repository gates already validated before Sprint C:

- 52/52 targeted Collector tests;
- `git diff --check`;
- Ruff;
- mypy on 184 source files;
- full pytest: 76 passed;
- no Git write;
- no network acquisition.

## Sprint C objective

Add the first network-capable acquisition adapter:

`collector acquire <youtube-url>`

Scope:

- strict YouTube video URL recognition;
- canonical video identity;
- metadata retrieval through yt-dlp with `download=False`;
- transcript/subtitle listing and retrieval through youtube-transcript-api;
- requested-language preference;
- manual transcript preference when available;
- fallback to any available transcript when preferred languages are absent;
- preservation of transcript language and generated/manual flag;
- exact provider `start` and `duration` values;
- persisted time anchors on schema-v2 `segments`;
- description text representation;
- partial acquisition when metadata or transcript is independently unavailable;
- no audio download;
- no STT/Whisper;
- no video/frame analysis.

## Current upstream API assumptions verified 2026-08-11

`youtube-transcript-api`:

- current instance API uses `YouTubeTranscriptApi().list(video_id)` and
  `fetch(video_id)`;
- fetched snippets expose `text`, `start`, and `duration`;
- transcript metadata exposes language/language code and `is_generated`;
- transcript-list selection prefers manually created transcripts over generated
  transcripts for matching requested languages;
- upstream can raise request/IP blocking failures because it uses undocumented
  YouTube web endpoints.

`yt-dlp`:

- Python embedding uses `YoutubeDL.extract_info(url, download=False)`;
- `YoutubeDL.sanitize_info()` is the supported way to obtain JSON-serializable
  metadata;
- this adapter sets `YTDLP_NO_PLUGINS=1` during the lazy yt-dlp import;
- media download is disabled in Sprint C.

## Security boundary

The user-provided locator is never passed directly to yt-dlp after matching.

The adapter first extracts an 11-character video ID from explicit allowlisted
hosts and paths, then reconstructs:

`https://www.youtube.com/watch?v=<video_id>`

Accepted host families:

- `youtube.com`;
- `www.youtube.com`;
- `m.youtube.com`;
- `music.youtube.com`;
- `youtu.be`;
- `www.youtu.be`.

Supported forms:

- `/watch?v=<id>`;
- `youtu.be/<id>`;
- `/shorts/<id>`;
- `/embed/<id>`;
- `/live/<id>`.

This prevents arbitrary user-controlled URLs from turning yt-dlp into a generic
Internet downloader.

The transcript client receives only the validated video ID.

Generic WebPageAdapter remains out of scope.

## Acquisition payloads

### `youtube-metadata`

Bounded JSON tool output containing selected useful yt-dlp metadata.

No media format URLs are persisted in v1.

### `youtube-transcript`

Bounded JSON containing:

- tool/version;
- selected language;
- manual/generated flag;
- available transcript metadata;
- exact snippet `text`;
- exact snippet `start`;
- exact snippet `duration`.

## Representations

### `youtube_metadata_json`

Structured metadata representation derived from `youtube-metadata`.

### `youtube_description`

Text representation of the YouTube description when present.

### `youtube_timed_transcript`

UTF-8 text joined with newline separators.

Each non-empty provider snippet becomes one explicit `SegmentDraft` with:

- exact snippet text;
- `start_char`;
- `end_char`;
- `start_seconds`;
- `end_seconds = start + duration`;
- source snippet index;
- original `duration_seconds`;
- generated/manual flag.

Provider time overlap is allowed and preserved.

No word-level timestamp is invented.

## Schema/persistence extension

`RepresentationDraft` gains optional explicit `segments`.

When explicit segments are provided:

- Collector persistence does not re-split the text;
- all authoritative anchors are persisted;
- exact re-acquisition validates text, anchors and segment metadata;
- existing review status is preserved.

Representations without explicit segments continue to use deterministic passage
splitting exactly as Sprint B.

No schema version change is required.

## Partial outcomes

Examples:

- metadata succeeds + no transcript -> `partial / no_transcript`;
- metadata succeeds + transcript IP blocked -> `partial / rate_limited`;
- metadata fails + transcript succeeds -> `partial / metadata_failed`;
- both unavailable -> acquisition job fails.

No missing transcript is fabricated.

## CLI

New optional argument:

`--languages fr,en`

This is a descending preference list for transcript selection.

Existing `--language` remains as a single language hint and LocalFileAdapter
compatibility option.

The JSON manifest now surfaces explicit timed segment anchors when adapters
provide them.

## No-network automated tests

Sprint C automated gates must NOT call YouTube.

Network clients are injected behind protocols and mocked.

Tests cover:

- accepted YouTube URL forms;
- hostile lookalike host rejection;
- deterministic YouTube adapter routing;
- metadata + timed transcript;
- overlapping provider time spans;
- exact persisted time/character anchors;
- exact re-acquisition and review preservation;
- no-transcript partial result;
- metadata-only failure with transcript success;
- both-client failure;
- bounded staged outputs;
- preferred language parsing;
- raw transcript duration preservation;
- complete Sprint A/B non-regression.

## Live smoke test

A live smoke test is NOT part of the guarded installer acceptance gate because:

- YouTube availability is external;
- IP blocking/rate limiting can occur;
- transcript availability varies by video.

Only after the local gate is validated should the user run a separate live test.

Target first live source:

`https://www.youtube.com/watch?v=A1VKJkJVqC8`

No transcript copy/paste is required.

## Acceptance gate

Required:

1. targeted Collector tests;
2. `git diff --check`;
3. Ruff;
4. mypy;
5. full pytest;
6. no Git write.

Expected gate:

`COLLECTOR_YOUTUBE_V1_VALIDATED_LOCAL`

Do not commit/push/merge or start audio/STT fallback without separate
authorization.


## V2 correction after first guarded repository run

The first Sprint C integration attempt validated:

- 73/73 targeted Collector/YouTube tests;
- `git diff --check`;
- Ruff;
- repository rollback after gate failure.

It stopped only on mypy in `adapters/youtube.py`.

V2 corrections:

1. Replace the dynamic `_TimeoutSession.__new__` subclass wrapper with
   `_timeout_session()`, which creates a normal `requests.Session`,
   captures its bound `request` method, injects a default timeout through
   an instance-level wrapper, disables `trust_env`, and returns it.
   This preserves runtime behavior while avoiding an invalid subclass
   override signature in static typing.
2. Remove the duplicate local annotation of `selected` in the
   `NoTranscriptFound` branch; the existing `selected: Any = None`
   declaration remains the single annotation.
3. Remove the now-unused `cast` import.

No change to:

- YouTube URL allowlist;
- canonical URL reconstruction;
- metadata fields;
- transcript selection policy;
- timecode persistence;
- partial/failure semantics;
- media-download prohibition;
- schema v2;
- acquisition persistence;
- network behavior of the installer (still no live acquisition).

V2 must pass targeted tests, `git diff --check`, Ruff, mypy, and full
pytest before Sprint C is accepted.
## V3 correction after second guarded repository run

The V2 repository run validated:

- 73/73 targeted Collector/YouTube tests;
- `git diff --check`;
- rollback after gate failure;
- no Git write;
- no network acquisition.

V2 stopped on one Ruff B010 finding in
`src/ecobiome/knowledge_acquisition/adapters/youtube.py`.

V3 changes only the local typing/assignment form used to install the
default-timeout request wrapper:

- `session: Any = requests.Session()`;
- direct `session.request = request_with_timeout` assignment.

No YouTube acquisition semantics, timeout values, transcript selection,
provenance, persistence, security policy, or CLI behavior changes.

V3 must still pass Ruff, mypy and the complete pytest suite in the real
EcoBiome environment before Sprint C is accepted.
