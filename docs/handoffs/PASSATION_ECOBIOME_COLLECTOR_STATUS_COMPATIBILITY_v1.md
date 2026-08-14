# PASSATION — EcoBiome Collector status compatibility v1

Date: 2026-08-11
Status: guarded local hardening candidate
Git add/commit/push/merge authorized: NO
Network acquisition authorized: NO

## Trigger

The first real YouTube live smoke acquisition succeeded and persisted:

- 1 Source;
- 1 AcquisitionJob;
- 2 Retrievals;
- 2 RawArtifacts;
- 3 Representations;
- 1,059 Segments.

The compatibility `status` field nevertheless reported `documents: 0`
because `CollectorStore.summary()` counted only representations whose kind
was exactly `transcript`.

The v2 acquisition architecture now has other reviewable textual
representation kinds, including `youtube_description` and
`youtube_timed_transcript`.

## Decision

The historical compatibility alias `documents` now means:

> number of distinct representations that own at least one Segment.

This keeps the old transcript behavior intact while making the compatibility
counter source-agnostic.

For the validated live YouTube acquisition this means:

- `representations = 3`;
- `documents = 2` (description + timed transcript);
- `passages = 1,059`.

Metadata-only representations remain excluded because they own no segments.

## Scope

Changed code:

- `src/ecobiome/knowledge_acquisition/persistence.py`

Regression coverage:

- `tests/test_collector_youtube.py` explicitly requires `documents == 2`
  for one metadata + description + timed-transcript acquisition.

No schema migration is required.

## Live smoke evidence motivating the fix

The live acquisition for `A1VKJkJVqC8` completed successfully with:

- French auto-generated transcript;
- 1,057 timed transcript segments;
- no acquisition diagnostics;
- SQLite integrity check OK;
- foreign-key check empty;
- CAS SHA-256 and sizes verified;
- repository state unchanged.

## Acceptance criteria

1. Targeted Collector tests pass.
2. `git diff --check` passes.
3. Ruff passes.
4. mypy passes.
5. Full pytest passes.
6. No staging changes.
7. No Git writes.
8. No network acquisition by the installer.
9. Final gate:
   `COLLECTOR_STATUS_COMPATIBILITY_VALIDATED_LOCAL`.

Do not implement claim extraction and do not commit/push until this gate has
been reviewed.
