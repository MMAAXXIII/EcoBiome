# EcoBiome — G6 Industry Impact Projection V1

**Date:** 2026-08-17
**Base:** `main@68175025607a1daaef0bbeac59afd5bd8ea640e3`
**Gate:** G6 partial — first relation-by-relation projection extension

## Scope

This slice adds exactly one reviewed Scientific Assertion Projection mapping:

`poses_significant_threat_to / industry_impact`

It does not generalize projection automatically.

## Why this mapping first

V2.10 already permits both:

- `poses_significant_threat_to / risk_factor`
- `poses_significant_threat_to / industry_impact`

The Projection contract already supports the first pair with:

- assertion kind `relational`;
- predicate `poses_significant_threat_to`;
- `cause=ENTITY_ARGUMENT`;
- `target=ENTITY_ARGUMENT`;
- builder `binary_entity_relation_v1`.

The new pair therefore reuses an already reviewed relation signature and
builder. No new role class or assertion construction rule is introduced.

## Projection contract identity

Contract version:

`1.2`

Canonical contract SHA-256:

`628dacf8a2a21c94d62d0374e9f0872ea9e1d547272fcb2600bc037786316526`

Automatic persistence remains false.

## Fail-closed boundaries preserved

This slice does **not** add:

- `adversely_affects / knowledge_gap`;
- `studied / study_subject`;
- any of the other valid-but-unmapped V2.10 pairs;
- a generic projection fallback;
- automatic scientific acceptance;
- automatic assertion persistence.

`adversely_affects / knowledge_gap` is explicitly regression-tested as still
fail-closed.

## Persistence and schema

No SQLite DDL is changed.

No Schema V7 is required.

No provider is called.

## Exact product paths

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_acquisition/scientific_assertion_projection_v1.py`
3. `tests/test_scientific_assertion_projection_v1_1.py`
4. `tests/test_scientific_assertion_projection_g6.py`
5. `docs/handoffs/PASSATION_ECOBIOME_G6_INDUSTRY_IMPACT_PROJECTION_V1.md`

## Required validation

- `uv sync --locked`
- Ruff
- mypy
- G6 dedicated projection tests
- existing Projection V1 tests
- V2.10 provider-schema tests
- complete pytest suite

## Roadmap state

G6 remains **in progress** after this slice. It is not complete until further
relation/type mappings are individually reviewed and integrated.

## Next decision

After merge and post-merge convergence, review the next projection mapping
independently. Do not implement another mapping without a new reviewed scope.
