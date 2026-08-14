# PASSATION EcoBiome — Semantic Evaluator V2.3.2 integration v1

## Scope

Integrate the reviewed V2.3.2 structured semantic evaluator core without changing
the existing V2.2 evaluator, provider code, Golden fixtures, model configuration,
or scientific review policy.

## Decision

Provider-output defects are benchmark observations. They are recorded under
`candidate_contract.violations`, remain gate-blocking, and do not crash semantic
scoring when enough candidate structure remains to score safely.

Benchmark-asset corruption remains fatal:
- malformed Golden fixture;
- malformed semantic export;
- malformed evaluator-side candidate contract / ontology.

## Repository changes

Only these new files are introduced:
- `src/ecobiome/knowledge_acquisition/semantic_benchmark_structured.py`
- `tests/test_collector_semantic_benchmark_structured.py`
- `docs/handoffs/PASSATION_ECOBIOME_SEMANTIC_EVALUATOR_V2_3_2_v1.md`

The existing `semantic_benchmark.py` V2.2 implementation and all V2.2 fixtures
remain byte-for-byte unchanged.

## Provenance

Reviewed audit bundle:
`A_JOINDRE_ECOBIOME_SEMANTIC_EVALUATOR_V2_3_2_PROVIDER_ERRORS_SCOREABLE_20260812-051400.zip`

Audit ZIP SHA-256:
`ea068c318dc60c7f9280541bcc95e9a356b962faaf28717161866542ec1513cc`

Audited prototype SHA-256:
`8f9a20ba2196ebbfc151178fca7962f2965f9dd74afc76d03a3de0387b3cdbb0`

The integrated core is behavior-identical to the audited prototype. Only the
module docstring changes from “Prototype only” to the integrated V2.3.2 status.

## Validated behavior

The external audit established:
- 27/27 adversarial self-tests pass;
- Fixture #1 Qwen regression reproduces V2.3.1 exactly;
- Fixture #1 lexical baseline regression reproduces V2.3.1 exactly;
- Fixture #2 oracle: 47/47 REQUIRED, zero contract violations, gate PASS;
- frozen Qwen R3: 45/47 REQUIRED detected, 33 entailed, 12 ambiguous,
  0 contradicted, 5/5 admissible, 1 extra, 13 candidate-contract violations,
  gate BLOCKED;
- provider errors are scoreable and gate-blocking;
- corrupted benchmark assets remain fatal.

## Acceptance criteria for local integration

1. Branch remains `feature/collector-cli-baseline`.
2. HEAD remains `feac99c11e4174178a88e2cba9038310776d0dfa`.
3. Staging area remains empty.
4. All pre-existing dirty paths remain byte-for-byte unchanged.
5. Existing V2.2 benchmark files retain their frozen SHA-256 hashes.
6. The three declared files are the only repository changes introduced here.
7. Targeted V2.2 + V2.3.2 tests pass.
8. Ruff passes for the integrated files.
9. Mypy passes for `src`.
10. Full pytest suite passes.
11. No network request, provider call, Git add/commit/push/merge/rebase, or
    scientific auto-acceptance occurs.

## Risks

- V2.3.2 is a benchmark evaluator, not a production semantic provider.
- A scoreable contract violation still blocks the benchmark gate; tolerance
  must never be interpreted as acceptance.
- The evaluator does not measure scientific truth.
- Fixture #2 has limited Evidence-selection difficulty because its Claims
  generally expose one Evidence item each.
- Future provider integration must preserve the fatal/scoreable boundary.

## Open questions

- Whether a future stable public API should re-export
  `evaluate_structured_semantic_benchmark` from `semantic_benchmark.py` or a
  package-level API module.
- Whether Fixture #2 assets should later be integrated into the repository as a
  permanent regression corpus.
- Whether provider prompts should be improved to reduce argument-role mistakes
  before comparing alternative models or quantizations.

## Next step

After this integration is reviewed and validated, design the next milestone
without changing the provider/model automatically. Candidate next work is a
provider-output contract hardening experiment using the frozen Fixture #2
benchmark.

DO NOT IMPLEMENT PROVIDER CHANGES, MODEL CHANGES, GOLDEN CHANGES, OR SCIENTIFIC
AUTO-ACCEPTANCE WITHOUT EXPLICIT AUTHORIZATION.
