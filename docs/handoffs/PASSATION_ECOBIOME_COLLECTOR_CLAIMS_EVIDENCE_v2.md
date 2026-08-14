# PASSATION — EcoBiome Collector Claims + Evidence v1

Date: 2026-08-11
Status: guarded local integration candidate
Git add/commit/push/merge authorized: NO
Network acquisition authorized: NO

## Context

Collector v2, LocalFile acquisition, YouTube v1, the live YouTube smoke test,
and the status-compatibility hardening are already validated locally.

The next milestone is to turn persisted review Segments into explicit candidate
Claims that remain traceable to exact Evidence.

## Decisions

1. New automatically proposed Claims use `claim_kind = source_statement`.
2. Every new Claim starts with `review_status = pending`.
3. Segment acceptance never implies Claim acceptance.
4. Rejected Segments are excluded from proposal windows.
5. Corrected Segment text may be used as candidate Claim wording, but Evidence
   always preserves the exact original Segment text and anchors.
6. Timed transcript segments keep their authoritative start/end seconds.
7. One candidate Claim may cite multiple consecutive Segment Evidence rows.
8. Exact reproposal is deduplicated.
9. Claim review remains append-only through `review_decisions`.
10. `claim-show` returns the Claim, exact Evidence, source provenance, and Claim
    review history.
11. No scientific confidence score is generated.
12. No Claim is copied into the scientific knowledge registry automatically.

## Deterministic baseline extractor

`source-statement-window-v1` groups consecutive non-rejected Segments and
flushes a window when:

- the configured character limit would be exceeded;
- a timed gap exceeds 2.5 seconds;
- the configured timed window would be exceeded;
- a Segment ends in terminal punctuation.

This extractor identifies source statements only. It does not classify them as
scientific facts and does not evaluate truth.

## CLI

Propose pending source statements:

`ecobiome collector propose-claims --database <db> --representation-id <uuid>`

Inspect one Claim with Evidence and provenance:

`ecobiome collector claim-show <claim-id> --database <db>`

Existing Claim review remains:

`ecobiome collector review claim <claim-id> accept|correct|reject ...`

## Safety invariants

- original source Segment text is immutable;
- Evidence text must match its Segment character anchor;
- Evidence time/page/frame anchors must remain inside Segment bounds;
- candidate Claim status is always `pending`;
- no network access is required by this milestone;
- no Git write is performed by the installer.

## Acceptance criteria

1. Targeted Collector tests pass, including Claims/Evidence tests.
2. `git diff --check` passes.
3. Ruff passes.
4. mypy passes.
5. Full pytest passes.
6. Staging remains empty.
7. No Git write occurs.
8. No network acquisition occurs.
9. Final gate:
   `COLLECTOR_CLAIMS_EVIDENCE_VALIDATED_LOCAL`.

## Next step after review

Run a bounded proposal smoke test against the already acquired YouTube
transcript, for example the first 10–20 source-statement candidates, then inspect
their exact Evidence before considering semantic/atomic scientific claim
extraction.

Do not implement automatic scientific acceptance and do not commit/push until
this gate has been reviewed.
## V2 correction after first guarded repository run

The V1 repository run validated:

- 82/82 targeted Collector tests;
- `git diff --check`;
- rollback after the gate failure;
- no Git write;
- no network acquisition.

V1 stopped on one Ruff I001 finding in
`src/ecobiome/knowledge_acquisition/claim_candidates.py`.

V2 changes only the import-block formatting required by Ruff
(two blank lines before the first top-level dataclass).

No claim generation, Evidence anchoring, review semantics,
persistence, schema, CLI behavior, or scientific acceptance policy changes.

V2 must still pass Ruff, mypy and the full pytest suite in the real
EcoBiome repository before Sprint D is accepted.
