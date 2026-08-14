# PASSATION — EcoBiome Collector Semantic Extraction Harness v1

Date: 2026-08-11
Status: guarded local integration candidate
Git add/commit/push/merge authorized: NO
Network acquisition authorized: NO

## Context

The Semantic Claim Guard v2 is locally validated. The bounded Medaka semantic
reference smoke is also validated on a copy of the real YouTube-derived Claims
database:

- 12 human-authored atomic reference propositions;
- 22 exact Evidence links;
- every derived Claim remains `pending`;
- 22/22 copied Evidence rows preserve parent Evidence text, SHA-256 and anchors;
- exact re-ingestion is idempotent;
- SQLite integrity is `ok`;
- no foreign-key violation;
- no review decision;
- no automatic scientific acceptance;
- original source smoke database and repository remain unchanged.

The reference intentionally excludes incomplete or corrupted transcript
fragments. It is a golden benchmark fixture, not scientific ground truth.

## Objective

Introduce a provider-independent semantic-extraction harness before connecting
any LLM or external semantic service.

The harness must keep the semantic extractor untrusted. The extractor receives
only a bounded immutable view of existing `source_statement` Claims and their
persisted Evidence. It may return only Semantic Claim Contract v1 JSON.

## New extraction request

`build_semantic_extraction_request()` exports at most 50 explicit source Claim
IDs.

Each exported source Claim includes:

- Claim ID;
- current review status;
- effective text;
- effective-text SHA-256;
- whether human correction changed the effective text;
- only non-rejected persisted Evidence;
- Evidence ID, Segment ID/index, exact text and SHA-256;
- time/page/frame anchors;
- source provenance.

The request explicitly states:

- atomic propositions only;
- Evidence IDs must come from the parent Claim;
- do not invent Evidence;
- skip ambiguous/incomplete statements;
- automatic scientific acceptance is false.

Rejected source Claims and duplicate input Claim IDs are rejected before
extraction.

## SemanticExtractor protocol

The provider-independent protocol exposes:

- `name`;
- `version`;
- `extract(request) -> object`.

`run_semantic_extractor()`:

1. builds the trusted bounded request;
2. invokes the extractor as an untrusted producer;
3. parses the output through Semantic Claim Contract v1;
4. rejects extractor name/version spoofing;
5. returns a validated batch without persistence.

Persistence remains a separate explicit action through the already validated
Semantic Claim Guard.

## Benchmark-only baseline

A deliberately limited `ConservativeFrenchLexicalExtractorV1` is included only
to establish a reproducible line-zero benchmark.

Its output carries:

`benchmark_only = true`

The trusted persistence layer now explicitly rejects any semantic proposal with
that qualifier. Therefore the lexical baseline can be exported/evaluated but
cannot enter the Collector database even if someone manually passes its JSON to
`ingest-atomic-claims`.

This baseline is not a general semantic model and must never be presented as
one.

## Golden Medaka baseline result

Against the validated 12-proposition Medaka reference fixture, the lexical
baseline produced:

- candidate proposals: 14;
- reference proposals: 12;
- aligned reference items: 12;
- exact Evidence-set matches: 5;
- exact precision: 0.357143;
- exact recall: 0.416667;
- exact F1: 0.384615;
- mean aligned Evidence Jaccard: 0.680556;
- mean aligned text-token Jaccard: 0.989583.

The two extra candidates are useful failures: the baseline extracts cold/hot
temperature assertions from a source-statement window ending in an incomplete
fragment (`... à des`). A production extractor should learn to abstain there.

These metrics measure reference alignment only. They do NOT measure scientific
correctness.

## Evaluation

`evaluate_semantic_batch()` compares a validated candidate batch with a
validated reference batch.

Strict exact match requires:

- same parent `source_claim_id`;
- same `semantic_type`;
- exact same Evidence ID set.

A secondary diagnostic alignment reports Evidence Jaccard and normalized token
Jaccard. The report explicitly states that scientific correctness is not
measured.

## CLI

New commands:

```text
collector semantic-export --database <db> --claim-id <id> [...] [--output <json>]
collector semantic-baseline --database <db> --claim-id <id> [...] [--output <json>]
collector semantic-evaluate <candidate.json> <reference.json> [--output <json>]
```

`semantic-baseline` does not persist.

## Security / epistemic invariants

This milestone performs no:

- LLM/provider network call;
- prompt execution against an external service;
- automatic Claim persistence from the benchmark extractor;
- scientific confidence scoring;
- automatic scientific acceptance;
- knowledge-registry insertion;
- schema migration;
- Git write;
- production GC deletion.

The existing Semantic Claim Guard remains the only persistence authority for
future production semantic extractors.

## Tests before installer packaging

In the isolated reconstructed Collector tree:

- new Sprint E tests: 8/8 PASS;
- complete targeted Collector suite: 108/108 PASS;
- Python syntax: PASS;
- modified-file line length <= 88: PASS.

Ruff, mypy and full repository pytest remain mandatory gates in the real
EcoBiome environment.

## Acceptance gate

Expected final gate:

`COLLECTOR_SEMANTIC_EXTRACTION_HARNESS_VALIDATED_LOCAL`

Do not connect a production LLM/provider, commit, push or merge before this gate
has been reviewed.

## Next step after validation

Implement one bounded semantic provider adapter behind `SemanticExtractor`,
then evaluate it on the exact golden Medaka fixture before allowing any
persistence. The first provider run must remain non-persisting and must beat the
lexical baseline while reducing false positives on incomplete transcript
fragments.
