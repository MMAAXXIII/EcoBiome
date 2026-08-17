# EcoBiome — G5 Entity-Resolution Operator V1

**Status:** implementation candidate for feature publication
**Gate:** `ECOBIOME_G5_ENTITY_RESOLUTION_OPERATOR_V1`

## Goal

Close G5 on top of Scientific Foundation V6 without changing the physical
schema.

The operator workflow turns one human-reviewed Semantic Candidate argument into
an append-only reviewed entity mapping that can already be consumed by
Scientific Assertion Projection V1.

## Exact product scope

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_persistence/contracts.py`
3. `src/ecobiome/knowledge_persistence/sqlite_store.py`
4. `src/ecobiome/knowledge_acquisition/semantic_candidate_entity_resolution_v1.py`
5. `src/ecobiome/knowledge_acquisition/semantic_candidate_entity_resolution_cli_v1.py`
6. `src/ecobiome/knowledge_acquisition/collector_cli.py`
7. `tests/test_semantic_candidate_entity_resolution_cli_g5.py`
8. `docs/handoffs/PASSATION_ECOBIOME_G5_ENTITY_RESOLUTION_OPERATOR_V1.md`

## Operator commands

### `semantic-candidate-entity-search`

Bounded read-only lookup of **reviewed entity revisions** by exact canonical
label.

No fuzzy matching or automatic semantic resolution is introduced.

### `semantic-candidate-entity-show`

Shows:

- the Semantic Candidate review status;
- every canonical argument;
- which arguments require entity resolution;
- append-only resolution history by role;
- latest resolution state.

### `semantic-candidate-entity-review`

Human write gate for one argument role.

The command requires the Semantic Candidate itself to have a latest G2
`accept` review.

#### Accept

`accept` requires an explicit reviewed `entity_id` + `entity_revision`.

The operator derives the exact source surface from V2.11, then resolves that
surface to exactly one candidate Evidence span. If the surface is ambiguous,
the command fails closed unless the operator supplies both:

- `--evidence-id`
- `--segment-char-start`

The command atomically creates/replays a
`ScientificEntityNameUsagesRow(mapping_review_status="reviewed_confirmed")`
anchored to the same source/segment/span and then appends the V6
entity-resolution event.

#### Reject

`reject` does not create a new reviewed name usage. It revokes the **latest
accepted mapping** for that role and reuses its exact entity/name-usage binding.

This avoids representing a rejected mapping as a newly
`reviewed_confirmed` name usage.

## Persistence changes

No table, index or Schema V7 change.

One read-only repository capability is added:

- bounded exact-label listing of reviewed entity revisions.

The existing entity-resolution event and name-usage writes remain unchanged.

All entity-resolution persistence integrity checks already present in V6 remain
authoritative.

## Safety invariants

- Semantic Candidate latest G2 review must be `accept`;
- only `grounded_opaque_unresolved` / `source_text` arguments may cross G5;
- entity revision must already be `reviewed_confirmed`;
- source surface must map to one exact Evidence span;
- ambiguous surfaces fail closed;
- name usage is source/segment/span anchored;
- resolution history remains append-only;
- exact event/name-usage replay is idempotent;
- latest reject blocks reviewed reconstruction;
- automatic scientific acceptance remains false;
- no provider call;
- no projection relation expansion in G5.

## Explicit non-goals

- no Schema V7;
- no fuzzy entity matching;
- no automatic entity selection;
- no new Scientific Assertion projection relations;
- no automatic candidate acceptance;
- no provider/network call.

## Next gate

After G5 publication and merge, G6 may extend Scientific Assertion Projection
relation-by-relation, with each mapping independently reviewed and tested.
