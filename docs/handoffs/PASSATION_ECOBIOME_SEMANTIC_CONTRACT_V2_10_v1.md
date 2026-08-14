# Passation EcoBiome — Semantic Contract V2.10 v1

## Status

Local integration of the reviewed V2.10 relation/type extension.

No provider certification and no automatic scientific acceptance are granted.

## Frozen basis

- base registry: V2.7
- base relation/type contract: V2.8
- Claim-scoped provenance: V2.9
- human-review freeze: V2.10 Historical Golden Matrix Human Review Freeze V1
- architecture design: V2.10 Contract Extension 45 Resolved / 18 Blocked Design Audit V1

## Change

V2.10 applies 24 provider-blind historical-Golden reviewed relation/type
resolutions on top of the V2.8 merged runtime registry.

Coverage becomes:

- 63 total relations
- 45 resolved relation/type contracts
- 18 `unresolved_blocked`

The V2.7 registry, V2.8 contract/helper, and V2.9 provenance implementation are
not modified.

## Provider architecture

V2.9 source-scope provenance is reused unchanged:

`Claim -> only Evidence IDs owned by that Claim`

V2.10 semantic branches are now generated directly from the V2.10 runtime
registry rather than copied from the old 21-branch V2.8 provider schema.

For the frozen 15-Claim source this yields:

- 15 Claim/Evidence source branches
- 45 semantic relation/type branches
- 675 Cartesian branches avoided
- 60 factorized branches

The 21 pre-existing V2.9 semantic branches remain structurally identical.

## Relations intentionally still fail-closed

Negative-only historical evidence:

- `derived_from_arithmetic`
- `evaluative_conclusion`
- `forbidden_join`
- `purpose_not_result`

Historically unobserved:

- `does_not_live_in`
- `does_not_occur_in`
- `does_not_originate_from`
- `does_not_tolerate`
- `easy_to_keep`
- `effective_against`
- `is_not_robust`
- `is_robust`
- `lives_in`
- `not_easy_to_keep`
- `not_effective_against`
- `occurs_in`
- `originates_from`
- `tolerates`

Do not open these from the already-observed Medaka replay.

## Validation boundary

The integration must pass:

- V2.10 targeted Ruff
- V2.10 targeted pytest
- full pytest
- mypy on `src`
- exact pre-existing dirty-tree preservation

No provider call is part of the integration.

## Next gate

After successful integration, run an explicit local Ollama Structured Output
grammar smoke against the exact 45-semantic-branch V2.10 schema.

Do not perform another semantic replay until that grammar smoke passes.

## Implementation guardrail

Do not implement additional semantic relations, provider persistence, Fixture #4,
or a new replay without explicit authorization.
