# Passation EcoBiome — Scientific Assertion Projection Contract V1 — Phase B v1

## Status

Local implementation candidate only.

This phase implements the fail-closed projection boundary from a validated
Semantic Candidate V2.11 to a canonical Scientific Foundation V1.1 assertion
payload. It does not write SQLite, does not implement Schema V5, and does not
persist assertion rows.

## Frozen basis

- main base SHA: `e80f86684079e24fc6f12ff8acbc83f4f82ff0d2`
- Semantic Candidate contract: V2.11
- Scientific Foundation canonical assertion serialization: V1.1
- Persistence physical schema: V4, unchanged
- provider persistence / `semantic_candidates` durable table: not implemented
- automatic scientific acceptance: forbidden at the V2.11 boundary

## Implemented contract

Target module:

`src/ecobiome/knowledge_acquisition/scientific_assertion_projection_v1.py`

The contract performs deterministic validation and projection only.

It requires, fail-closed:

1. a structurally and canonically valid V2.11 candidate;
2. the linked source Claim to exist and be `claim_layer="atomic"`;
3. at least one human Claim review event;
4. the latest Claim review not to be rejected;
5. the candidate effective-text SHA to equal the effective atomic-Claim text
   after append-only corrections;
6. every candidate Evidence ID to be linked to that same atomic Claim;
7. every candidate Evidence row and backing Segment to exist;
8. no candidate Evidence Segment to have an effective rejected review state;
9. an exact reviewed projection mapping for semantic type + relation;
10. exact numeric roles to remain deterministically resolved;
11. controlled literals to remain deterministically resolved;
12. every required entity role to have a human-reviewed mapping tied to the
    SHA-256 of that exact V2.11 argument;
13. no extra role/entity/context reconstruction outside the candidate;
14. no cross-Claim argument completion.

## Atomic Claim effective-text rule

`SourceClaimsRow.source_claim_effective_text_sha256` on an atomic Claim is not
treated as the SHA of the atomic Claim's own reviewed text.

In the current V4 compatibility path, that field can preserve the effective
text identity of the upstream source/parent Claim at atomization time.

Therefore Phase B computes the effective atomic-Claim text identity from:

- the immutable atomic `claim_text` / `claim_text_sha256`;
- append-only `claim_review_events`;
- the latest correction text, if any.

The candidate's
`source.source_claim_effective_text_sha256`
must match that computed atomic effective-text SHA.

This avoids conflating lineage staleness with the atomic Claim's own correction
history.

## Human-reviewed entity mapping

Entity resolution is not implemented automatically.

The caller supplies `ReviewedEntityArgumentV1` values containing:

- role;
- SHA-256 of the exact V2.11 argument being mapped;
- scientific entity ID and revision;
- mapping status;
- mapping review status;
- reviewer.

Projection requires:

- mapping status `exact` or `synonym`;
- mapping review status `reviewed_confirmed`;
- a non-empty reviewer;
- argument SHA equality.

Thus a mapping cannot be silently reused after candidate argument drift.

## Projection registry

Phase B intentionally does not generalize all V2.10 relations.

The only frozen mapping in this first tranche is:

`experimental_condition / maintained_at`
→ `measurement / maintained_at`

Role classes:

- `variable` → `ENTITY_ARGUMENT`
- `value` → `EXACT_NUMERIC_ARGUMENT`
- `unit` → `CONTROLLED_LITERAL_ARGUMENT`

All other semantic type/relation pairs fail closed with:

`no exact Scientific Assertion Projection V1 mapping exists`

New mappings require a later reviewed code change.

## Canonical assertion mapping

For `maintained_at`, the projection emits a Scientific Foundation V1.1 payload:

- assertion kind: `measurement`
- predicate: `maintained_at`
- participant:
  - role `variable`
  - reviewed `entity_ref`
- value:
  - `kind="measurement"`
  - exact typed decimal `amount`
  - controlled `unit`
- qualifier:
  - V2.11 semantic type

The canonical assertion SHA uses the existing
`canonical_assertion_payload()` + `canonical_sha256()` implementation.

Source Claim IDs, Evidence IDs, candidate IDs, provider IDs and review IDs are
not included in the scientific assertion canonical identity. They remain in
the projection trace/provenance output.

## Claim-link proposal

The contract returns an unpersisted provenance proposal:

- stance: `supports`
- support mode: `unknown`
- scope alignment: `exact`
- semantic alignment: `exact`
- `requires_persistence_review=true`

This phase does not insert `assertion_claim_links`.

## Persistence boundary

No database write occurs.

This phase does NOT:

- add or modify a SQLite table;
- modify Schema V4 identity;
- implement Schema V5;
- create `semantic_candidates`;
- persist a `scientific_assertions` row;
- persist a `scientific_assertion_revisions` row;
- persist an `assertion_claim_links` row;
- persist provider runs;
- resolve entities automatically;
- stage, commit or push files.

## Tests

Target:

`tests/test_scientific_assertion_projection_v1.py`

Coverage includes:

- exact `maintained_at` measurement projection;
- deterministic, float-free canonical output;
- mandatory human Claim review;
- latest rejected Claim rejection;
- corrected Claim accepted only after candidate rebuild;
- stale candidate rejection after correction;
- atomic-Claim-only projection;
- Claim-local Evidence link enforcement;
- exact missing-Evidence-Segment diagnostic binding;
- rejected Evidence Segment rejection;
- mandatory human-reviewed entity mapping;
- stale entity-mapping SHA rejection;
- extra/cross-Claim reconstruction rejection;
- fail-closed behavior when no exact projection mapping exists.

## Validation gates

Targeted:

- `uv lock --check`
- compileall target module/test
- Ruff target module/test
- mypy target module
- pytest target tests

Canonical Python CI:

- `ruff check src tests`
- `mypy src`
- `pytest -q`

## Acceptance gate

Successful local completion must end with:

`ECOBIOME_SCIENTIFIC_ASSERTION_PROJECTION_V1_PHASE_B_LOCAL_IMPLEMENTATION_COMPLETED`

## Next sensitive boundary

After successful local validation, perform a read-only review of the exact
three new Phase B files.

Staging requires a separate explicit authorization.

Do not implement Schema V5 or persistence writes without separate authorization.
