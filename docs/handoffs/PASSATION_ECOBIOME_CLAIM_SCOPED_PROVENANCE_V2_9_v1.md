# PASSATION ECOBIOME — CLAIM-SCOPED PROVIDER PROVENANCE V2.9 v1

Date: 2026-08-12
Branch expected: `feature/collector-cli-baseline`
HEAD expected: `feac99c11e4174178a88e2cba9038310776d0dfa`

## Decision

V2.9 adds a source-independent, claim-scoped provider provenance layer on top
of the accepted local V2.8 semantic contract.

V2.8 relation/type behavior must remain unchanged:
- 21 resolved provider-eligible relation/type branches;
- 42 unresolved relations remain fail-closed.

V2.9 does not hard-code the 15 Claims or 81 Evidence IDs from the observed live
batch into repository code or fixtures. Runtime Claim/Evidence ownership is
derived from the current `source_request`.

## Failure that motivated V2.9

Frozen V2.8 replay:
- 12 proposals;
- all 12 claimed Claim 8;
- all 12 used foreign-parent Evidence;
- 0/24 string argument occurrences grounded in the claimed Claim;
- 5 exact duplicate groups;
- 0 V2.8 relation/type violations;
- 0 unresolved-blocked relation emissions.

The failure therefore belongs to provider provenance and Claim locality, not to
the V2.8 relation/type contract.

## Wire contract

Provider proposal shape:

```json
{
  "s": {
    "c": "<Claim ID>",
    "e": ["<Evidence IDs owned by that Claim>"]
  },
  "x": {
    "t": "<semantic type>",
    "m": {
      "r": "<relation>",
      "a": {}
    }
  }
}
```

The contract is factorized:
- `s`: one Claim-scoped branch per runtime Claim;
- `x`: resolved semantic branches inherited from the V2.8 provider schema.

Do not build the 15 × 21 Cartesian product.

## Admission order

1. validate provider wire shape;
2. validate Claim/Evidence parent ownership;
3. validate relation/type against V2.8;
4. run deterministic argument grounding against the selected parent Claim only;
5. canonical exact deduplication, keep first deterministically.

Zero surviving proposals is a valid fail-safe abstention.

Passing these gates does not constitute automatic scientific acceptance.

## Source independence

The repository policy fixture contains no live Claim IDs or Evidence IDs.
Finite runtime identifiers are generated from each `source_request`.

This is required to avoid source-specific leakage into the reusable contract.

## Files in this local integration candidate

New files only:
- `src/ecobiome/knowledge_acquisition/provider_provenance_v2_9.py`
- `tests/fixtures/collector_semantic_v2_9/CLAIM_SCOPED_PROVENANCE_POLICY_V2_9.json`
- `tests/test_collector_provider_provenance_v2_9.py`
- `docs/handoffs/PASSATION_ECOBIOME_CLAIM_SCOPED_PROVENANCE_V2_9_v1.md`

No V2.8 file is modified.

## Acceptance criteria

1. Pre-integration repository state exactly matches the accepted V2.9 design
   audit checkpoint.
2. All 100 pre-existing dirty paths remain byte-identical.
3. Staging remains empty.
4. Exactly four new paths are added.
5. The runtime schema builder reproduces the frozen design-audit candidate
   schema byte-for-byte under canonical JSON for the frozen 15-Claim source.
6. Positive Claim-local source-scope replay passes 15/15.
7. Frozen bad V2.8 proposals are rejected 12/12 at source-scope provenance.
8. Their V2.8 semantic assertions remain independently valid, preserving the
   diagnostic boundary.
9. Deterministic dedup replay remains 12 -> 7 with five duplicate groups.
10. Targeted py_compile, Ruff and pytest pass.
11. Full pytest and mypy `src` pass.
12. No provider call, network call, YouTube acquisition, DB write, semantic
    import, Git write, or Fixture #4 use occurs.

## Risks / open questions

- The exact nested factorized JSON Schema has not yet been exercised against
  Ollama Structured Output. Local integration does not prove provider grammar
  compatibility.
- Provider output may still select a Claim-local Evidence set while emitting
  foreign open-text arguments; deterministic Claim-local grounding remains
  required.
- The 42 V2.8 unresolved relations still limit semantic coverage. V2.9 must not
  relax them merely to increase proposal count.
- Exact deduplication removes only byte-equivalent normalized proposals; it does
  not perform semantic near-duplicate resolution.

## Next step after successful local integration

Review the integration bundle first. Do not run Qwen again without explicit
authorization after review.

A future bounded replay, if authorized, must:
- reuse the same frozen 15 Claims / 81 Evidence IDs;
- perform exactly one local Qwen call;
- use the V2.9 factorized schema;
- retain V2.8 relation/type fail-closed behavior;
- apply V2.9 admission and dedup post-provider;
- make no precision/recall/generalization claim without a human Golden.

## Codex instruction

Do not implement anything beyond the files and behavior listed above without
explicit authorization. Do not commit, push, merge, rebase, persist semantic
output, use Fixture #4, or run a provider.
