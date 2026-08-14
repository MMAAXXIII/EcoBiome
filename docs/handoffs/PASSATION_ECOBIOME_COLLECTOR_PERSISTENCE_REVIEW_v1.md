# PASSATION - EcoBiome Collector Persistence and Review v1

## Status

Local implementation stage only.

This milestone turns the canonical transcript-import seed into a durable
Collector foundation without changing the legacy `ecobiome import-transcript`
behavior.

## Scope

Implemented:

- versioned SQLite Collector schema;
- durable sources and provenance;
- immutable raw transcript documents addressed by SHA-256;
- deterministic document and passage persistence;
- collection job lifecycle including durable failures;
- claims and evidence schema foundations;
- append-only human review decisions;
- accept / correct / reject review workflow;
- corrections preserve original source passages;
- new `ecobiome collector` CLI namespace;
- local smoke coverage for import, queue, and review.

Tables:

- `schema_migrations`
- `sources`
- `documents`
- `passages`
- `claims`
- `evidence`
- `collection_jobs`
- `review_decisions`

## Scientific safety

- Imported passages start as `pending`.
- No candidate is promoted automatically to canonical scientific knowledge.
- Corrections are stored as review decisions; original evidence text is not
  overwritten.
- Raw documents are content-addressed and checksum-verified.
- This milestone does not fabricate scientific values or confidence scores.
- No AI extraction is implemented in this milestone.

## Compatibility

The existing semi-manual command remains available:

`ecobiome import-transcript`

The durable workflow is additive:

`ecobiome collector init`
`ecobiome collector import-transcript`
`ecobiome collector status`
`ecobiome collector pending`
`ecobiome collector review`

## Deferred next milestones

1. Bolt Collector review UI.
2. Automatic YouTube transcript adapter with timestamps and raw transcript.
3. Structured scientific candidate extraction.
4. Exact evidence spans and video timecodes.
5. Deterministic source/document duplicate handling beyond exact hashes.
6. Source corroboration and explainable reliability scoring.
7. Optional audio transcription fallback.
8. Visual video-frame evidence extraction.

## Governance

This implementation must be validated locally before any commit or push.

Do not merge, rebase, force-push, delete the branch, or begin automatic
video-analysis work from this operation.
