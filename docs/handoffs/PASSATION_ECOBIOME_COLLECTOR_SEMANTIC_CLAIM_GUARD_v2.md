# PASSATION — EcoBiome Collector Semantic Claim Guard v1

Date: 2026-08-11
Status: guarded local integration candidate
Git add/commit/push/merge authorized: NO
Network acquisition authorized: NO
Automatic scientific acceptance authorized: NO

## Context

The previous Collector milestones are locally validated through Sprint D and the
bounded Medaka Claims/Evidence smoke test. The smoke test demonstrated that
`source_statement` Claims preserve exact provenance but are not semantically
atomic: some are conversational fragments and some combine multiple assertions.
They must therefore never be inserted directly into the scientific knowledge
registry.

## Objective

Introduce a strict boundary between an untrusted future semantic extractor and
the trusted Collector persistence layer.

This milestone does **not** connect an LLM or any external semantic service.
Instead, it defines and validates the only JSON contract that a future semantic
engine may submit.

## Contract v1

A semantic batch contains:

- `schema_version = 1`;
- extractor `name` and `version`;
- 1–200 proposals.

Each proposal contains only:

- `source_claim_id` — canonical UUID of an existing `source_statement` Claim;
- `source_claim_effective_text_sha256` — optimistic-concurrency guard over the
  current human-reviewed effective source-statement text;
- `text` — proposed atomic proposition, maximum 500 characters;
- `semantic_type` — lower_snake_case classification token;
- `evidence_ids` — 1–50 UUIDs of Evidence already owned by that source Claim;
- optional scalar `qualifiers`.

Explicitly unsupported fields include model confidence, acceptance flags and
model-supplied evidence text. Unsupported keys are rejected.

## Trusted persistence rules

`CollectorStore.persist_atomic_claim_batch()`:

1. requires the parent Claim to exist and have `claim_kind=source_statement`;
2. rejects rejected parent Claims;
3. recomputes the effective parent text from append-only review history;
4. rejects stale semantic output if its SHA-256 no longer matches;
5. resolves every Evidence ID from SQLite itself;
6. requires every selected Evidence row to belong to the stated parent Claim;
7. rejects Evidence backed by a rejected Segment;
8. verifies the persisted parent Evidence SHA-256 before copying it;
9. copies Evidence text, SHA-256 and anchors from SQLite — never from semantic
   extractor output;
10. persists the new Claim only as `atomic_source_proposition` / `pending`;
11. sets `automatic_scientific_acceptance=false` in metadata;
12. stores parent Evidence IDs for an auditable derivation link;
13. deduplicates exact reproposals deterministically;
14. applies the complete batch in one SQLite transaction so any invalid later
    proposal rolls back earlier inserts from the same batch.

## Input hardening

The strict JSON loader additionally:

- rejects duplicate JSON object keys;
- rejects NaN/Infinity and non-finite qualifier numbers;
- rejects unsupported object keys;
- validates canonical UUIDs and lowercase SHA-256 digests;
- caps semantic input at 2 MiB;
- caps proposal, Evidence and qualifier cardinalities/lengths.

## CLI

New command:

```text
collector ingest-atomic-claims <input.json> --database <db> [--output <json>]
```

The command persists only contract-valid proposals and returns reviewable Claim
manifests with `automatic_scientific_acceptance=false`.

## Tests in this milestone

The semantic guard test suite verifies at least:

- strict valid-contract parsing;
- rejection of confidence/accepted/fabricated-evidence fields;
- duplicate Evidence rejection;
- duplicate JSON-key rejection;
- non-finite qualifier rejection;
- oversized-input rejection;
- exact parent Evidence copying;
- Evidence ownership enforcement;
- stale parent text rejection after human correction;
- rejected parent rejection;
- rejected Segment rejection;
- transaction rollback when a later proposal in the batch is invalid;
- exact semantic reproposal deduplication;
- accepted parent Claim never auto-accepts the atomic Claim;
- CLI ingestion produces a reviewable pending manifest.

## Non-goals / explicitly not implemented

- no LLM/provider integration;
- no prompt execution;
- no external network access;
- no scientific truth scoring;
- no automatic scientific confidence;
- no automatic review decision;
- no knowledge-registry insertion;
- no schema migration;
- no production GC deletion;
- no git add/commit/push/merge.

## Acceptance gate

The repository integration must pass:

1. targeted Collector tests including the semantic guard suite;
2. `git diff --check`;
3. Ruff over `src tests`;
4. mypy over `src`;
5. full pytest;
6. unchanged staging area;
7. exact payload hashes.

Expected gate:

`COLLECTOR_SEMANTIC_CLAIM_GUARD_VALIDATED_LOCAL`

## Next step after validation

Only after this gate is reviewed should EcoBiome add a semantic-extractor
provider. The provider must be treated as untrusted and may output only the
contract above. A first bounded Medaka semantic smoke should run on a copy of
the existing Claims smoke database and inspect a small number of proposed atomic
propositions before any knowledge-registry work.

Do not implement provider integration, automatic scientific acceptance,
knowledge-registry insertion, commit, push, or merge without explicit
authorization.
## V2 correction after first guarded repository run

The V1 repository run validated:

- 100/100 targeted Collector tests;
- `git diff --check`;
- Ruff over `src tests`;
- exact repository rollback after the gate failure;
- no Git write;
- no network acquisition.

V1 stopped on two mypy diagnostics in
`persist_atomic_claim_batch()`. Both came from one local variable name:
`evidence_id` first represented a contract-supplied string UUID and was
later reused for a newly generated `UUID` object.

V2 separates those roles explicitly:

- `parent_evidence_id`: existing Evidence identifier supplied by the
  semantic contract;
- `new_evidence_id`: UUID generated for the copied Evidence attached to
  the new atomic Claim.

No persistence semantics, SQL, Evidence ownership rule, atomicity,
deduplication, schema, CLI behavior, or scientific acceptance policy
changes.

V2 must still pass mypy and the complete repository gate chain in the
real EcoBiome environment before this milestone is accepted.
