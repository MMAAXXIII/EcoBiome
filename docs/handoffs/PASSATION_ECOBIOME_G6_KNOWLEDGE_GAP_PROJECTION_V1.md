# EcoBiome — G6 Knowledge Gap Projection V1

**Date:** 2026-08-17
**Base:** `main@7db0079fd76432ea67b543ef9577845ca7682470`
**Gate:** G6 partial — second relation/type projection extension

## Scope

This slice adds exactly one reviewed Scientific Assertion Projection mapping:

`adversely_affects / knowledge_gap`

It does not generalize projection automatically.

## Why this mapping

V2.10 already permits both:

- `adversely_affects / health_effect`
- `adversely_affects / knowledge_gap`

Projection V1.2 already supports the first pair with:

- assertion kind `relational`;
- predicate `adversely_affects`;
- `cause=ENTITY_ARGUMENT`;
- `target=ENTITY_ARGUMENT`;
- builder `binary_entity_relation_v1`.

The V1.2 next-slice audit proved that `knowledge_gap` is the only remaining
valid-but-unmapped semantic type whose relation is already projected.

## Projection contract identity

Contract version:

`1.3`

Canonical contract SHA-256:

`e17859fb66e49343a564ccf756e7f12e3b879d68af7b1a9fcd60fe5c63cb3fa3`

Automatic persistence remains false.

## Fail-closed boundaries preserved

This slice does **not** add:

- `studied / study_subject`;
- any of the other 42 remaining valid-but-unmapped V2.10 pairs;
- a generic projection fallback;
- automatic scientific acceptance;
- automatic assertion persistence.

The pre-existing generic Projection V1 test continues to prove that
`studied / study_subject` fails closed without an exact mapping.

## Persistence and schema

No SQLite DDL is changed.

No Schema V7 is required.

No provider is called.

## Exact product paths

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_acquisition/scientific_assertion_projection_v1.py`
3. `tests/test_scientific_assertion_projection_v1_1.py`
4. `tests/test_scientific_assertion_projection_g6.py`
5. `docs/handoffs/PASSATION_ECOBIOME_G6_KNOWLEDGE_GAP_PROJECTION_V1.md`

## Required validation

- `uv sync --locked`
- Ruff
- mypy
- Projection V1 core tests
- Projection V1.2/V1.3 historical binary relation tests
- G6 projection tests
- V2.10 provider-schema tests
- complete pytest suite

## Roadmap state

G6 remains **in progress** after this second slice.

## Next decision

After merge and post-merge convergence, re-audit the remaining 43
valid-but-unmapped pairs. Do not infer a third mapping automatically.
