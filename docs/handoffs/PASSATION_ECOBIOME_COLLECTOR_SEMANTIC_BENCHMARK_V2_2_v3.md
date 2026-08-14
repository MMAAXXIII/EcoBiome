# PASSATION — Collector Semantic Benchmark V2.2

Version: v3\
Scope: local repository integration only\
Status: corrected after two guarded local integration attempts; no remote Git operation is authorised.

## Integration retry note

The first local integration attempt on 2026-08-12 was intentionally rolled
back after repository validation found 20 Ruff violations in the newly added
`semantic_benchmark.py`:

- 18 `TRY004` findings: invalid runtime types raised `ValueError` instead of
  `TypeError`;
- 2 `B023` findings: a local ranking function captured loop variables.

That first attempt still passed the targeted benchmark tests (8/8) and the full
test suite (150/150), and its rollback restored the exact pre-integration dirty
worktree fingerprint (57 paths), Git status, unstaged diff and empty staged
diff.

Revision R2 corrected those Ruff findings. Its guarded integration attempt then
passed:

- targeted benchmark tests: 8/8;
- full test suite: 150/150;
- Ruff: all checks passed.

Mypy then found exactly two typing errors in one fixture-index construction
block. A local variable named `key` had already been inferred as
`tuple[str, str, str]` for REQUIRED/ADMISSIBLE semantic keys and was then
reused as `tuple[str, str]` for EXCLUDED keys. R2 therefore rolled back as
designed. The rollback again restored the exact 57-path dirty fingerprint, Git
status, unstaged diff and empty staged diff.

Revision v3 changes only that local variable to `excluded_key`. No fixture,
candidate, semantic rule, benchmark result, gate condition, production CLI
path or provider behavior is changed.

## Decision

Integrate the reviewed **Golden Fixture V2.1** and the deterministic
**Semantic Benchmark Evaluator V2.2** as benchmark/regression infrastructure,
without replacing the existing V1 semantic evaluator and without integrating
an Ollama/Qwen provider.

The production CLI command `collector semantic-evaluate` remains unchanged.
V2.2 is intentionally isolated in
`ecobiome.knowledge_acquisition.semantic_benchmark`.

## Why this shape

The previous evaluator aligned candidates mainly through parent Claim,
semantic type and Evidence overlap. That could credit a polarity inversion or
an Evidence selection that omitted the predicate/negation needed to support
the proposition.

V2.2 separates:

1. strict REQUIRED coverage;
2. explicit reviewed minimal Evidence provenance;
3. deterministic entailment/polarity checks;
4. ADMISSIBLE review-only fragmentary readings;
5. EXCLUDED policy-violating readings;
6. a strict single-fixture `benchmark_gate`.

A single Medaka fixture can block a candidate provider. It can never certify a
provider for production use.

## Frozen benchmark provenance

Source benchmark gate:
`COLLECTOR_OLLAMA_QWEN36_LIVE_BENCHMARK_V2_COMPLETED`

Source benchmark ZIP SHA-256:
`e54f8231988169a027447d8b6ed9f7d75f20d9a4e16c193958dfbf375ca95bdd`

Reviewed Golden V2.1:
- REQUIRED: 13
- ADMISSIBLE: 3
- EXCLUDED: 1

Important reviewed Evidence corrections:
- rice fields: segments 37 + 38;
- mosquito control: segments 43 + 44;
- large volume: segments 56 + 57 + 58.

## Frozen regression expectations

Qwen3.6 V2:
- REQUIRED coverage: 12/13;
- sufficient provenance: 5/12;
- entailed: 4;
- contradicted: 4;
- insufficient Evidence: 4;
- ADMISSIBLE detected: 3/3;
- forbidden policy violations: 0;
- gate: BLOCKED.

Expected Qwen blocking reasons:
- `missing_required=1`
- `required_provenance_insufficient=7`
- `critical_contradictions=4`

Lexical baseline:
- REQUIRED coverage: 13/13;
- sufficient provenance: 7/13;
- entailed: 7;
- contradicted: 0;
- insufficient Evidence: 6;
- forbidden pH cross-Claim inference: 1;
- gate: BLOCKED.

Expected lexical blocking reasons:
- `required_provenance_insufficient=6`
- `forbidden_inference_policy_violations=1`

## Assumptions

- The branch remains `feature/collector-cli-baseline`.
- The committed HEAD remains
  `feac99c11e4174178a88e2cba9038310776d0dfa` during this isolated integration.
- Existing dirty/untracked Collector work is intentional and must be preserved.
- No target file created by this integration exists before execution.

## Risks

- The evaluator contains fixture-aware French lexical rules. It is benchmark
  infrastructure, not a general NLI engine.
- Passing this fixture is not scientific correctness.
- Passing this fixture is not production-provider certification.
- The fixture is intentionally narrow and must later be complemented by
  independent fixtures covering other taxa, domains, negations, quantities,
  causal assertions and noisy transcripts.

## Acceptance criteria

The integration is accepted locally only if:

- every payload file is written with its expected SHA-256;
- the existing dirty worktree outside the target paths is preserved;
- targeted V2.2 tests pass;
- the complete Python test suite passes;
- Ruff passes with the repository's configured rules;
- mypy passes;
- no network request is made by the integration script;
- no Git commit, push, merge, rebase, reset, checkout or remote mutation occurs;
- the final log and review ZIP are generated.

On validation failure, the integration script removes only the files it created
and verifies restoration of the pre-integration repository state.

## Open questions

1. How many independent fixtures are required before a provider-qualification
   protocol can be designed?
2. Should benchmark fixtures eventually live in a dedicated `benchmarks/`
   package rather than under tests?
3. Should a future benchmark CLI consume this evaluator, or should it remain a
   test/research API?
4. Which next fixture should target quantitative claims and units?

## Explicit next-step guardrail

**Do not implement or persist an `OllamaSemanticExtractor` in production
without explicit user authorisation after this integration has been reviewed.**

Do not grant provider certification from this fixture alone.
