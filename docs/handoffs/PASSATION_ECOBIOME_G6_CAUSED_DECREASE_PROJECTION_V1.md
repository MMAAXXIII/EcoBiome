# EcoBiome — G6 Caused-Decrease Projection V1

**Date:** 2026-08-17
**Base:** `main@f20177a979e231791ad0f8e9c1e7746eba04794c`
**Gate:** G6 partial — third relation/type projection extension

## Scope

This slice adds exactly one reviewed Scientific Assertion Projection mapping:

`caused_decrease / biological_effect`

It also adds one new projection builder:

`spec_binary_entity_relation_v1`

The builder does not infer relation semantics. It only materializes an exact
ProjectionSpec that already declares:

- assertion kind;
- predicate;
- exactly two role names;
- both role classes as `ENTITY_ARGUMENT`.

## Why this mapping

The V1.3 relation-design audit selected `caused_decrease` for focused review:

- epistemic class: `explicit_causal_result`;
- signature: `exposure, variable`;
- both roles are source-grounded open text;
- `variable` already has an entity-resolution projection precedent;
- existing upstream tests already forbid upgrading study-purpose text into
  `caused_decrease`.

## Builder design correction

The preliminary design used the name `ordered_binary_entity_relation_v1`.

That name is intentionally **not** published.

`canonical_assertion_payload()` canonicalizes participant order during
serialization. Therefore the product builder is named:

`spec_binary_entity_relation_v1`

It uses the exact roles declared by the spec, while the final participant order
and assertion identity remain governed by canonical serialization.

Normalized text is generated from the canonicalized payload participants.

## Entity-resolution boundary

`exposure` is **not** automatically promoted to a ScientificEntity.

Projection passes only when a human-reviewed exact/synonym entity mapping is
supplied for `exposure` and `variable`.

If an exposure cannot be represented by an existing reviewed scientific
entity, projection fails closed.

## Projection contract identity

Contract version:

`1.4`

Canonical contract SHA-256:

`c6fe1e0262fb08c4ad21d161e713f5fe6eb3f222cecb773db9b8d329452e3e0f`

Automatic persistence remains false.

## Scientific guardrails

This slice does not:

- infer causality from study purpose;
- infer causality from association;
- auto-resolve coordinated exposures;
- auto-create ScientificEntities;
- auto-accept scientific assertions;
- automatically persist assertions;
- add any other V2.10 mapping.

Existing epistemic tests that block study-purpose -> causal upgrades remain in
the targeted validation suite.

## Persistence and schema

No SQLite DDL is changed.

No Schema V7 is required.

No provider is called.

## Exact product paths

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_acquisition/scientific_assertion_projection_v1.py`
3. `tests/test_scientific_assertion_projection_v1_1.py`
4. `tests/test_scientific_assertion_projection_g6.py`
5. `tests/test_scientific_assertion_projection_g6_caused_decrease.py`
6. `docs/handoffs/PASSATION_ECOBIOME_G6_CAUSED_DECREASE_PROJECTION_V1.md`

## Validation

Required:

- `uv sync --locked`
- Ruff
- mypy
- Projection V1 / V1.4 regression tests
- dedicated caused-decrease tests
- V2.10 provider-schema tests
- epistemic overclaim tests
- grounded benchmark epistemic tests
- complete pytest suite

Expected after this slice:

- targeted suite: 40 passed
- full suite: 448 passed, 1 skipped

## Roadmap state

G6 remains **in progress** after this third slice.

## Next decision

After merge and local convergence, re-audit Projection V1.4.

Do not infer a fourth mapping automatically.
