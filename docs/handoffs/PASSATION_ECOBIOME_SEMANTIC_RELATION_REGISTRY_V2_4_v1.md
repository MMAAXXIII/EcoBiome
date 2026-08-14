# PASSATION — EcoBiome Semantic Relation Registry V2.4 v1

## Statut

Milestone: **V2.4 source-independent relation registry — frozen benchmark infrastructure**

This handoff freezes the exact registry candidate reviewed by the offline audit
`COLLECTOR_SEMANTIC_RELATION_REGISTRY_V2_4_SOURCE_INDEPENDENCE_AUDIT_COMPLETED`.

It does **not** certify a production semantic provider.

## Frozen assets

- Registry relations: **45**
- Argument roles: **34**
- Semantic types: **35**
- Argument categorical enums: **0**
- Registry canonical SHA-256:
  `b35c944ff26739222d26af1feb31e2634693be6e7b32369dee090afbfd36980a`
- Wire schema canonical SHA-256:
  `d7365f5b68806046e85dc0e5f8a007b658100281c45c2d83966f997aad8ae8a8`
- Reviewed audit ZIP SHA-256:
  `22742e4f96213c25cf8775890791f816bec74db3b44b1b792153003aa25f8c9a`

The integrated JSON snapshots are byte-for-byte copies of the reviewed audit
artifacts.

## Decision

Freeze **relation structure**, not source values:

- relation identifier -> exact argument-role names;
- role -> scalar type only (`string`, `integer`, `number`);
- categorical values remain source-derived non-empty strings;
- numeric values remain typed;
- missing/extra roles remain provider-contract violations;
- provider-output violations are scoreable, while registry corruption is fatal.

## Evidence supporting this freeze

The reviewed audit demonstrated:

- frozen Fixture #2 R4: **51/51** proposals remain structurally conforming;
- frozen Fixture #2 R3: the same **13/51** role/key defects remain rejected;
- Fixture #1 projection: **16/16** REQUIRED/ADMISSIBLE structures accepted;
- self-tests: **219/219 PASS**;
- removing **27** source-specific enum fields / **39** distinct categorical
  values did not erase the R3/R4 structural distinction.

## Assumptions

- The 45-relation vocabulary is sufficient only for the scientific structures
  exercised so far; global completeness is not claimed.
- Scalar typing is intentionally conservative.
- Source-local evidence and no-cross-Claim rules remain evaluator/provider
  responsibilities outside this registry utility.

## Risks

- Fixture #3 may require a genuinely new relation or role.
- A too-broad string role may permit semantically poor values even when the
  structural schema is valid.
- Extending the registry after inspecting a Fixture #3 Golden would contaminate
  a blind generalisation measurement.

## Fixture #3 protocol

1. Freeze this V2.4 snapshot **before** selecting or authoring Fixture #3 Golden.
2. Select a genuinely different scientific source/domain or experimental form.
3. Acquire and freeze source Claims/Evidence.
4. Run provider extraction using this frozen registry/schema without Golden
   exposure.
5. Freeze provider output.
6. Author/review Fixture #3 Golden separately.
7. Score with Semantic Evaluator V2.3.2.
8. If a new relation is objectively required, record it as registry coverage
   debt and propose a separately reviewed V2.4.x/V2.5 change. Do not patch V2.4
   during the same blind benchmark.

## Acceptance criteria

- Frozen registry/schema hashes remain exact.
- Zero argument categorical enums.
- Existing V2.2 and V2.3.2 regressions remain green.
- New registry tests remain green.
- Ruff and mypy remain green for integrated source.
- Full pytest remains green.
- No model, Golden, provider, network, or scientific acceptance change occurs.

## Explicit prohibition

**Do not implement or certify a production semantic provider, alter scientific
Goldens, tune this registry against Fixture #3 expected answers, commit, push,
merge, rebase, or otherwise perform remote/irreversible Git operations without
explicit authorization.**
