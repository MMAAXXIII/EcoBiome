# EcoBiome — G6 Affected Gene Expression Projection V1

**Date:** 2026-08-18
**Base:** `main@a7ec87841f384a036bc9fa749b0960b1fa9f3cc1`
**Gate:** G6 partial — fourth relation/type projection extension

## Scope

This slice adds exactly one reviewed Scientific Assertion Projection mapping:

`affected_gene_expression_in / combined_effect`

It reuses the existing projection builder:

`spec_binary_entity_relation_v1`

No new builder is introduced.

## Why this mapping

Projection V1.4 builder-reuse audit identified the pair as structurally
compatible but held publication until the `pathway` role crossed the
ScientificEntity boundary safely.

The focused audits proved:

- epistemic class: `explicit_causal_result`;
- signature: `exposure, pathway`;
- both roles are source-grounded open text;
- `exposure` already has a reviewed entity-resolution precedent;
- `pathway` can be represented by the existing generic ScientificEntity model
  as a reviewed `scientific_concept`;
- no Schema V7 or pathway-specific ontology/table is required.

## E2E compatibility proof

A disposable Scientific Foundation V6 database proved that:

1. `Heat exposure` can be persisted and reloaded as a reviewed
   `scientific_concept`;
2. `MAPK pathway` can be persisted and reloaded as a reviewed
   `scientific_concept`;
3. V2.10 reconstructs exact `exposure,pathway` arguments;
4. a spec-binary relation materializes the reviewed entity references;
5. predicate remains `affected_gene_expression_in`;
6. semantic type remains `combined_effect`;
7. omitting the pathway mapping fails closed.

## Entity-resolution boundary

Projection does not create pathway entities.

Both roles require human-reviewed exact/synonym entity mappings.

The Projection layer does not add an `entity_kind` enum and does not claim
that every pathway surface is automatically a ScientificEntity.

If the source pathway cannot be mapped to a reviewed ScientificEntity,
projection fails closed.

## Projection contract identity

Contract version:

`1.5`

Canonical contract SHA-256:

`b6db1e8c939a78bde7e9929cd5387b2f7bb63f9a5760aa6f1f42372e50079987`

Automatic persistence remains false.

## Scientific guardrails

This slice does not:

- infer causality from study purpose;
- infer causality from association;
- auto-create ScientificEntities;
- auto-create pathway ontology entries;
- auto-accept scientific assertions;
- automatically persist assertions;
- add any other V2.10 mapping.

## Persistence and schema

No SQLite DDL is changed.

Scientific Foundation remains Schema V6.

No Schema V7 is required.

No provider is called.

## Exact product paths

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_acquisition/scientific_assertion_projection_v1.py`
3. `tests/test_scientific_assertion_projection_v1_1.py`
4. `tests/test_scientific_assertion_projection_g6.py`
5. `tests/test_scientific_assertion_projection_g6_caused_decrease.py`
6. `tests/test_scientific_assertion_projection_g6_affected_gene_expression.py`
7. `docs/handoffs/PASSATION_ECOBIOME_G6_AFFECTED_GENE_EXPRESSION_PROJECTION_V1.md`

## Validation

Required:

- `uv sync --locked`
- Ruff
- mypy
- Projection V1 / V1.5 regression tests
- dedicated caused-decrease tests
- dedicated affected-gene-expression tests
- V2.10 provider-schema tests
- epistemic overclaim tests
- grounded benchmark epistemic tests
- complete pytest suite

Expected after this slice:

- targeted suite: 43 passed
- full suite: 451 passed, 1 skipped

## Roadmap state

G6 remains **in progress** after this fourth slice.

## Next decision

After merge and local convergence, re-audit Projection V1.5.

Do not infer a fifth mapping automatically.
