# PASSATION — EcoBiome Collector OpenAI Semantic Provider v1

Date: 2026-08-11
Status: guarded local integration candidate
Git add/commit/push/merge authorized: NO
Live OpenAI request during installer: NO
Automatic scientific acceptance: NO
Automatic semantic persistence: NO

## Context

Semantic Extraction Harness v1 is locally validated:
- 108 targeted Collector tests;
- Ruff;
- mypy over 189 source files;
- 132 full repository tests;
- provider-independent SemanticExtractor protocol;
- frozen Medaka lexical line-zero benchmark;
- benchmark-only outputs rejected by trusted persistence.

## Objective

Add the first real bounded provider implementation behind SemanticExtractor
without allowing it to persist or accept scientific Claims.

The provider uses the OpenAI Responses API through the already-present
`requests` dependency. No OpenAI Python SDK dependency is added.

Default model for the first benchmark:
- `gpt-5-mini`.

## Provider boundary

`OpenAIResponsesSemanticExtractor`:
- receives only the existing bounded semantic extraction request;
- reads the API key only from `OPENAI_API_KEY` or an internal constructor
  argument used by tests;
- uses a fixed HTTPS endpoint:
  `https://api.openai.com/v1/responses`;
- disables environment proxies with `Session.trust_env = False`;
- refuses redirects;
- applies connect/read timeouts;
- caps decoded response bytes;
- explicitly sets `store = false`;
- enables no tools;
- requests strict JSON Schema output;
- sends source material as untrusted data under developer instructions;
- uses no web search or external knowledge tool;
- never accepts model-supplied Evidence text or hashes.

The model returns only:
- `source_claim_id`;
- proposition text;
- semantic type;
- existing Evidence IDs.

EcoBiome itself restores the source Claim effective-text SHA-256 from the
trusted request and injects provider metadata.

## Epistemic / persistence invariant

Every OpenAI proposal receives:

`benchmark_only = true`

Trusted persistence already rejects that qualifier. Therefore this milestone
cannot persist OpenAI-generated Claims even if its JSON is manually passed to
`ingest-atomic-claims`.

No confidence score is accepted or generated.
No automatic scientific acceptance is possible.
No knowledge-registry insertion is performed.

## Empty extraction

Semantic Claim Contract v1 now permits an empty `proposals` array.

This is a conservative safety requirement: an extractor must be able to
abstain completely when every supplied statement is ambiguous, corrupted or
incomplete.

The maximum-proposal bound remains in place.

## CLI

New command:

```text
collector semantic-openai   --database <db>   --claim-id <id> [--claim-id <id> ...]   [--model gpt-5-mini]   [--output <candidate.json>]   [--diagnostics-output <diagnostics.json>]
```

`OPENAI_API_KEY` is never accepted as a CLI argument, avoiding shell-history
exposure.

The command does not persist the candidate output.

## Diagnostics

Optional diagnostics include:
- provider;
- fixed endpoint;
- requested/returned model;
- OpenAI response ID;
- request ID;
- response status;
- token usage when returned;
- proposal count;
- `store = false`;
- tools disabled.

The API key and raw Authorization header are never written to diagnostics.

## Validation before installer packaging

In the isolated reconstructed Collector tree:
- new provider/contract tests: 10/10 PASS;
- complete targeted Collector suite: 118/118 PASS;
- Python syntax: PASS;
- changed Python lines <= 88 characters: PASS.

The real repository installer must additionally pass:
- `git diff --check`;
- Ruff;
- mypy;
- full pytest.

## Not performed by this installer

- live OpenAI request;
- API billing;
- provider benchmark against the Medaka golden fixture;
- persistence of provider output;
- scientific confidence scoring;
- scientific acceptance;
- schema migration;
- Git add/commit/push/merge;
- production GC deletion.

## Expected gate

`COLLECTOR_OPENAI_SEMANTIC_PROVIDER_VALIDATED_LOCAL`

## Next step after review

Run one bounded, non-persisting live OpenAI benchmark on a copy of the validated
Medaka Claims smoke database. Evaluate the provider output against the frozen
12-proposition reference and compare it with lexical line-zero:

- exact F1: 0.384615;
- mean Evidence Jaccard: 0.680556.

The first live provider run must remain benchmark-only regardless of score.
Do not permit provider output persistence without a later explicit milestone.
## V2 correction after first guarded repository run

The V1 repository run validated:

- 118/118 targeted Collector tests;
- `git diff --check`;
- exact repository rollback after the gate failure;
- no Git write;
- no network acquisition.

V1 stopped on exactly two Ruff `PYI034` findings in
`tests/test_collector_semantic_openai.py`.

Both fake context-manager classes returned their concrete class name from
`__enter__`. V2 imports `typing.Self` and annotates both methods as
`-> Self`, matching Ruff's required typing convention.

No OpenAI provider behavior, HTTP behavior, endpoint, timeout, JSON
schema, benchmark-only protection, persistence behavior, semantic
extraction logic, or scientific acceptance policy changes.

V2 must still pass Ruff, mypy and the complete pytest suite in the real
EcoBiome repository before Sprint F is accepted.
## V3 correction after second guarded repository run

The V2 repository run validated:

- 118/118 targeted Collector tests;
- `git diff --check`;
- Ruff over `src tests`;
- exact repository rollback after gate failure;
- no Git write;
- no network acquisition.

V2 stopped on one mypy `arg-type` diagnostic at the requests transport
boundary. The provider payload was annotated `dict[str, object]`, while the
`requests` type stubs require a JSON-compatible heterogeneous value type.

V3 changes only the transport/request payload typing to `dict[str, Any]`
and aligns the fake transport signatures in tests. This is a typing-boundary
correction only; the runtime JSON payload, endpoint, timeouts, redirect
policy, proxy policy, Structured Output schema, benchmark-only behavior,
persistence rules, and scientific acceptance policy are unchanged.

V3 must still pass mypy and the complete repository gate chain in the real
EcoBiome environment before Sprint F is accepted.
