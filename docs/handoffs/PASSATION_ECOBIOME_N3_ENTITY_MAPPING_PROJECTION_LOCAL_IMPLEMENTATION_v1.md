# PASSATION — EcoBiome N3 Entity Mapping + Projection local implementation V1

Date: 2026-08-15

## Gate

`ECOBIOME_N3_ENTITY_MAPPING_PROJECTION_LOCAL_IMPLEMENTATION_VALIDATED`

## Canonical base

- branch: `main`
- base HEAD: `37638881fa171ff4926db3327837cfa0d1c9a036`
- physical Scientific Foundation schema: V6
- Collector compatibility schema: 2
- schema tables/indexes: 34 / 45
- runtime schema identity: `e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181`

## Durable entity-resolution seam

New append-only table: `semantic_candidate_entity_resolution_events`.

It binds one exact Semantic Candidate argument to a reviewed source name usage
and an exact reviewed `entity_id + entity_revision`. Source Claim, candidate
Evidence containment, exact offsets and NFC/case-sensitive source surfaces are
validated before insertion.

Entity-resolution policy V1 SHA-256:
`c2e31ae42c25610e4b6c299269bf50f05476b71772d1a0aefe01ff88329e329e`

## Projection V1.1

Projection contract SHA-256:
`3c4e468391a25b6df826da960d71b8af014ba501721c6bfec2c51edc97e7d4ce`

Exact mappings:
1. `experimental_condition / maintained_at`
2. `health_effect / adversely_affects`
3. `risk_factor / poses_significant_threat_to`

All other relation/type combinations remain fail-closed.

## Safety

- no automatic entity matching or fuzzy/embedding equivalence
- no cross-Claim reconstruction
- no implicit latest entity revision
- no automatic Scientific Assertion persistence
- no V5→V6 migration/adoption
- Collector compatibility remains 2
- staging remains empty
- no commit or push performed

## Next boundary

Exact allowlisted staging of the validated N3 implementation. Do not stage,
commit, push, merge or mutate GitHub without explicit authorization.
