# PASSATION ECOBIOME — SEMANTIC CONTRACT V2.8 CANDIDATE v1

Date: 2026-08-12
Branch expected: `feature/collector-cli-baseline`
HEAD expected: `feac99c11e4174178a88e2cba9038310776d0dfa`

## Decision

V2.8 is a conservative contract-closure layer over the frozen V2.7 semantic
relation registry. V2.7 must remain byte-for-byte unchanged.

### Relation/type contract

- 63 relations total.
- 18 V2.7 relations already have explicit `semantic_types_allowed`; preserve
  those mappings exactly.
- 3 historically evidenced singleton mappings are accepted for the V2.8
  contract:
  - `decreased -> measurement_trend`
  - `lasted -> experiment_duration`
  - `not_well_understood -> knowledge_gap`
- 42 remaining relations have no accepted historical relation/type evidence.
  They are explicitly `unresolved_blocked` with
  `semantic_types_allowed: []`.
- Empty allowed lists are intentional fail-closed state, not evidence that the
  relation itself is invalid.

### Grounding role closure

The 11 V2.7 ontology roles below are added to V1.2 opaque/source-grounded role
coverage:

`context`, `entity_a`, `entity_b`, `mechanism`, `mediator`, `response`,
`state`, `subject`, `target_state`, `taxon`, `temporal_scope`.

They inherit the existing opaque-text policy:
- source surface must be present;
- no semantic equivalence is inferred;
- no canonical entity resolution is performed;
- no scientific credit is awarded from grounding alone.

The frozen V1.1 grounding policy object and its canonical SHA-256 must remain
unchanged.

## Evidence

- Same-source Qwen A/B ZIP:
  `619ee1335c134198ecc9f03314153f97e381950fda5d221ae2e62448d1a5be73`
- Contract Closure Audit V1:
  `a5ce057da7b49512bcb186dd88b6ea1377ad51d0e076e7ad8f9df9b04b1dfa48`
- Relation/Type Evidence Matrix Audit V1:
  `687bd3b49559e8bdb4c8d5b947364929b7e046a63f9ed2f403947b24f6786528`
- Singleton Evidence Review Audit V1:
  `99cc4dd9c8e3fa0c2ec4de07a0703dbae4ba30839116482835e9a848a464f281`

## Expected posthoc behavior on the frozen B output

With V2.8 applied locally to the already-frozen 19 B proposals:

- accepted relation/type pairs: 0
- explicit relation/type incompatibilities: 2
- unresolved-blocked relation/type pairs: 17
- grounding-blocking proposals after the 11-role closure: 1
- remaining grounding blocker: candidate 18 (`had_level`, false day extraction)
- no provider rerun is part of this integration.

This is expected. V2.8 intentionally prefers abstention/blocking over guessed
compatibility.

## Files in candidate integration

Modified existing file:
- `src/ecobiome/knowledge_acquisition/semantic_grounding.py`

New files:
- `src/ecobiome/knowledge_acquisition/semantic_contract_v2_8.py`
- `tests/fixtures/collector_semantic_v2_8/SEMANTIC_RELATION_TYPE_CONTRACT_V2_8.json`
- `tests/fixtures/collector_semantic_v2_8/SOURCE_GROUNDING_ROLE_EXTENSION_V1_2.json`
- `tests/test_collector_semantic_contract_v2_8.py`
- `docs/handoffs/PASSATION_ECOBIOME_SEMANTIC_CONTRACT_V2_8_v1.md`

## Acceptance criteria

1. V2.7 registry SHA remains
   `cdc0debb45a5ac4182ff441ff1b7811e2571c03dc02b4bcdcf8b61ebbfd131db`.
2. Frozen grounding V1.1 canonical SHA remains
   `e7c566d78ec3eefbd30b9b424f92e35e25430933921f9a57f1c84efff232b6bf`.
3. V2.8 relation contract covers all 63 relations explicitly:
   18 existing + 3 reviewed + 42 unresolved-blocked.
4. All 45 V2.7 ontology argument roles are classified by runtime grounding.
5. The 11 new roles remain opaque/source-grounded and never scientifically
   scoreable from grounding alone.
6. Frozen B posthoc replay gives 2 incompatible + 17 unresolved-blocked and
   only candidate 18 remains grounding-blocking.
7. Targeted tests, full pytest, mypy, and Ruff pass.
8. Repository state differs from pre-integration only by the six intended
   paths above.
9. Staging remains empty.
10. No Git write, provider call, network call, YouTube acquisition, database
    write, semantic import, or Fixture #4 use occurs.

## Risks

- V2.8 will deliberately block many provider proposals until more relation/type
  evidence is reviewed. This is a safety feature, but it reduces immediate
  semantic throughput.
- The three singleton mappings are contract decisions supported by historical
  Goldens/tests; they are not precision/recall or generalization claims.
- Opaque source grounding proves textual provenance only, not semantic
  equivalence.

## Open questions

- Which of the 42 unresolved relations should be reviewed next, and from which
  independent evidence corpus?
- Should future provider JSON Schema exclude unresolved relations entirely, or
  keep them schema-visible and block them posthoc?
- Should `temperature_tolerance` be split when one source span also carries pH
  tolerance, rather than allowing mixed-domain free text under one semantic
  type?

## Do not implement without authorization

Do not commit, push, merge, rebase, modify PR metadata, persist semantic output,
or perform a new provider replay without explicit authorization.
