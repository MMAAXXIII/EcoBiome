# PASSATION — EcoBiome G7A RATE-2F-B — Nitrite Entity Shadow Seed + Mechanism Assertion Dry-Run

Gate:
`ECOBIOME_G7A_RATE_2F_B_NITRITE_ENTITY_SHADOW_SEED_AND_MECHANISM_ASSERTION_DRY_RUN_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@7edf678c2cbf8e435086eab0ebabc2528afe4e98`

## Human decisions

Nitrite identity:

```text
accept
SHA dbfe7412571fd289e960e9b1b46db837973fc707473b6caa42ef9ff5405f1eca
```

Mechanism alignment:

```text
accept
SHA aec4200eff9a7ef672b788479a516623285a2e5174e9fc0b00972fc40f9f952e
```

## Shadow-only result

Nitrite entity and ammonia-to-nitrite assertion were both persisted
successfully on a byte-copy of V6.

Proposed assertion SHA:

```text
907c862992a0d11f50d8f4ccab3b123902e5330bc8066caa977b64b133fd7b96
```

Exact shadow deltas:

```text
knowledge_sources                 +1
scientific_entities               +1
scientific_entity_revisions       +1
scientific_entity_identifiers     +1
scientific_assertions             +1
scientific_assertion_revisions    +1
assertion_claim_links              0
```

## Real V6 boundary

```text
SHA 76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
write authorized = false
written          = false
```

## Scientific construction

```text
source_material = ammonia CID 222
target_material = nitrite CID 946
process_agent   = absent
semantic_type   = nitrogen_oxidation
```

This is consistent with the reviewed non-organism-exclusive mechanism and the
reviewed TAN-to-reactive-ammonia bridge.

## Remaining blocker

The two RATE-2B primary Nature sources are not yet materialized in the current
V6 evidence graph. No assertion-claim link was invented.

## Next gate

`RATE-2G — Mechanism Primary Evidence Ingestion Design`
