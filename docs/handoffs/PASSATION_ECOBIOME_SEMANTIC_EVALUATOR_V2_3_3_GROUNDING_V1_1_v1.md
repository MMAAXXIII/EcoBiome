# PASSATION — EcoBiome Semantic Evaluator V2.3.3 + Grounding V1.1

Version: v1
Date: 2026-08-12
Status: local integration candidate; no provider certification

## Scope

This milestone integrates a new side-by-side evaluator stack without modifying
the existing V2.3.2 or V2.4 files:

- relation-first blind alignment;
- no alignment across different relations;
- `grounded_unresolved` and `grounding_failed` diagnostic states;
- global exact-duplicate diagnostics;
- Source-Independent Semantic Resolution / Numeric Grounding Policy V1.1;
- deterministic day/temperature/value+unit grounding;
- controlled unit normalization;
- conservative `temperature_scope` domain validation;
- opaque open-text source grounding with no semantic equivalence credit.

## Frozen dependencies

- Semantic Evaluator V2.3.3 grounded-alignment prototype audit:
  `91a1343b817b9716855bf3de5f6f9b23bf7d0179649aca7386404d64de244d04`
- V2.3.3 + source-grounding combined audit:
  `a37d181069e87b035594570f452cf207fa7498022549f138ccbf23ed0af09c5b`
- Semantic Resolution / Numeric Grounding Policy V1.1 hardening R2 audit:
  `fe7114078821351da7324fbc87fed52aef82031fbc853370f517cc59870a0d37`
- V1.1 policy canonical SHA-256:
  `e7c566d78ec3eefbd30b9b424f92e35e25430933921f9a57f1c84efff232b6bf`
- Existing V2.3.2 evaluator remains frozen:
  `16e1aae0621cc7671b32bacd86d33fccfdb953d87fc8fb5fcb79cf47651365df`
- Existing V2.4 registry remains frozen:
  canonical SHA-256
  `b35c944ff26739222d26af1feb31e2634693be6e7b32369dee090afbfd36980a`

## Decisions

1. V2.3.3 is integrated side-by-side as
   `semantic_benchmark_grounded.py`; V2.3.2 is not edited.
2. Grounding Policy V1.1 is frozen as a versioned artifact and copied into the
   implementation module.
3. Open-text source grounding does not imply semantic equivalence.
4. `grounded_unresolved` receives zero entailment credit.
5. Relation identity is required before blind alignment.
6. Exact duplicates are detected globally, including unexpected extras.
7. Value+unit grounding is joint: independent source hits cannot be combined.
8. `temperature_scope` accepts no semantic credit for rainfall/drought scopes.
9. Fixture #3 is regression-only after these post-hoc infrastructure changes.
10. A genuinely new Fixture #4 is required for the next generalization claim.

## Regression expectations

### Fixture #2 R4, V2.3.3 without grounding policy

Must preserve the frozen V2.3.2 scientific metrics:

- REQUIRED detected: 46/47
- entailed: 46
- contradicted: 0
- ambiguous: 0
- provenance sufficient: 46/46
- benchmark blocked only by `missing_required=1`.

### Fixture #3 R2, V2.3.3 with Grounding Policy V1.1

Expected diagnostic projection over the eight V2.4-representable REQUIRED atoms:

- aligned: 1/8 (`soil-g3r-01`)
- strict entailed: 0/8
- grounded_unresolved: 1/8
- contradicted: 0
- missing: 7/8
- global exact duplicates: 1 (#15 duplicates #14)
- semantic-role violations: 11
  - eight rainfall values used as `temperature_scope`;
  - three ungrounded free-text argument surfaces.

This replay must not rewrite the frozen official V2.3.2 score.

## Risks / limitations

- The resolver intentionally does not solve generic synonyms, taxa, tissues,
  analytes, locations, processes, conditions, outcomes, or other open-text
  equivalence.
- Controlled-unit normalization is intentionally small and versioned.
- Number-word parsing currently covers English zero through ninety-nine.
- `temperature_scope` validation is conservative and regex-based; ambiguous
  values abstain.
- V2.4 still has 28 frozen Fixture #3 registry gaps.
- No production provider certification follows from this integration.

## Acceptance criteria

- all pre-existing 73 dirty paths remain byte-identical;
- staging remains empty;
- only the six declared integration files are added;
- targeted Ruff passes;
- new targeted tests pass;
- mypy over `src` passes;
- full pytest suite passes;
- frozen Fixture #2 R4 regression passes;
- frozen Fixture #3 R2 diagnostic regression passes;
- no network, provider call, Git write, Golden change, V2.4 change, or
  automatic scientific acceptance occurs.

## Next step

After this integration is reviewed and explicitly accepted, the next separate
milestone may design a new registry version from the 28 frozen Fixture #3 gaps.

Do not implement registry extensions, modify the provider prompt/model, or
claim new generalization without explicit authorization.
