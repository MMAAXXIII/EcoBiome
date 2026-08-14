# Passation — EcoBiome Collector Semantic Robustness V2.7 + Seam Stream V2.2

Status: local integration candidate R2. No production-provider certification.

## R1 failure and R2 repair

R1 failed only at targeted Ruff after `py_compile` passed. No provider or
network call occurred, rollback restored the exact 86-path state, and staging
remained empty.

Frozen R1 failed integration ZIP SHA-256:
`de3e7cb7f60619da0ebb6422410c76e4e2b992f884320105d889fb11e234a36c`

R2 changes only Ruff-compliance details in the implementation/test payloads:
- remove one self-assignment (`PLW0127`);
- use `TypeError` for invalid input types (`TRY004`);
- replace two unnecessary `set(generator)` forms with set comprehensions
  (`C401`);
- apply Ruff import ordering/spacing in the two new test modules (`I001`).

No scientific policy, Seam Stream V2.2 contract, registry relation signature,
provider schema semantics, live regression expectation, or acceptance criterion
is changed by R2.

## Frozen prerequisites

- Seam Stream V2.2 audit ZIP SHA-256:
  `a159aa4fde2c16a08a689adbd383ef1edca6cf99dc001a015f52fc2c2e3c8476`
- Seam Stream V2.2 policy canonical SHA-256:
  `8a5d530298ff4b3134def7b194609b1524167df04223c4969443695bb7cb6fde`
- Semantic Robustness V2.7 candidate audit ZIP SHA-256:
  `331a129a2b6ef8c68433fc15e4b3ea9f8c68e6890e77eb09e47f9ef30f553680`
- Multilingual Coordination V1.1:
  `c58ebe6b2b2a2114bfd2cd03a2bec7de0665fc63333356a2f82fa6a87825b872`
- Legacy Epistemic Coverage V1:
  `801615c06ac5ce2f40a7938033c89d0fbb139f2483c17996d3a9dc127f1d389b`
- Provider Provenance Constraint V1.1:
  `328a34a1ac913dc99bd2079f6a9f2676795c04a9da56a397c6f7d8a59895cef0`
- Registry V2.6 remains frozen and byte-unchanged.
- Fixture #4 remains unused.

## Integration decisions

1. `build_source_statement_candidates` keeps its public API and the historical
   extractor identifier `source-statement-window-v1`, but its implementation
   becomes Seam Stream V2.2.
2. Seam Stream V2.2 uses a monotonic source cursor, bounded forward extension,
   exact partial-Segment Evidence spans, trim+carry, and provider-ineligible
   unresolved source regions.
3. Forward-extension source text is consumed exactly once. The next candidate
   resumes after the consumed character boundary.
4. No non-whitespace source character may be duplicated or silently lost in
   the processed stream prefix.
5. Rejected Segments are hard stream boundaries. An incomplete prefix before a
   rejected Segment is withheld rather than persisted as a source-statement
   Claim.
6. Human-corrected Segment text remains atomic unless a character-level
   correction mapping exists; raw Evidence remains the original Segment.
7. The existing V2.6 registry and `semantic_epistemic.py` are not modified.
   V2.7 is side-by-side.
8. Registry V2.7 adds only machine-readable epistemic classes to the 45 legacy
   relations; relation IDs and argument signatures remain unchanged.
9. Multilingual coordination detects source-language coordination but never
   automatically splits, merges, cross-products, or grants entailment credit.
10. Provider provenance schema constrains Claim/Evidence IDs to the finite
    current batch; same-parent Evidence ownership remains a blocking
    deterministic post-validator.
11. No semantic provider output is persisted automatically.

## Expected local delta

Modified existing paths:

- `src/ecobiome/knowledge_acquisition/claim_candidates.py`
- `tests/test_collector_claims.py`

New paths:

- `src/ecobiome/knowledge_acquisition/semantic_robustness_v2_7.py`
- `tests/fixtures/collector_semantic_v2_7/SOURCE_STATEMENT_SEAM_STREAM_POLICY_V2_2.json`
- `tests/fixtures/collector_semantic_v2_7/MULTILINGUAL_COORDINATION_POLICY_V1_1.json`
- `tests/fixtures/collector_semantic_v2_7/LEGACY_EPISTEMIC_COVERAGE_V1.json`
- `tests/fixtures/collector_semantic_v2_7/PROVIDER_PROVENANCE_CONSTRAINT_V1_1.json`
- `tests/fixtures/collector_semantic_v2_7/SEMANTIC_RELATION_REGISTRY_V2_7.json`
- `tests/test_collector_claims_seam_stream_v2_2.py`
- `tests/test_collector_semantic_robustness_v2_7.py`
- `docs/handoffs/PASSATION_ECOBIOME_COLLECTOR_SEMANTIC_ROBUSTNESS_V2_7_SEAM_STREAM_V2_2_v1.md`

Starting from the frozen 86-path worktree, successful integration therefore
still has 86 old dirty paths plus 9 new paths = **95 dirty paths**.

## Acceptance criteria

- exact prerequisite ZIP/manifests/gates verified;
- current branch/HEAD and exact 86-path worktree verified before writes;
- staging empty before and after;
- only the two declared existing files are modified;
- exactly nine declared new paths are added;
- no Git write, provider call, or network call;
- Python compile passes;
- targeted Ruff passes;
- existing Collector Claims tests plus new Seam Stream tests pass;
- V2.6 semantic tests plus new V2.7 robustness tests pass;
- mypy `src` passes;
- full pytest passes;
- frozen live 1057-Segment transcript regenerated deterministically without
  YouTube or Qwen:
  - 15 provider-eligible source Claims;
  - actions: 4 safe / 8 forward extension / 3 trim+carry;
  - 1 provider-ineligible unresolved region;
  - exact Claim text/Evidence spans match the frozen V2.2 simulation;
- exact reproposal remains deterministic/deduplicated;
- existing V2.6 registry and policy hashes remain unchanged;
- rollback restores the exact 86-path pre-integration state on any failure.

## Risks

- ASR punctuation can remain noisy; Seam Stream V2.2 is deterministic and
  conservative but is not a sentence-understanding model.
- Partial transcript-Segment Evidence inherits the enclosing Segment's timing
  bounds; character offsets are the exact text provenance.
- English/French coordination packs are initial language coverage, not a claim
  of universal multilingual support.
- Legacy epistemic classes are relation-level guards, not an entailment oracle.
- This integration is authored after the live YouTube observation. The frozen
  live batch is regression/A-B material only.

## Next step after successful integration

Regenerate the same frozen live source batch locally with the integrated
Collector, without network or provider. After reviewing that deterministic
regeneration, one Qwen A/B replay on the same source may be performed.

Do not use Fixture #4, claim new generalization, enable automatic provider
persistence, or certify a production provider without explicit authorization.
