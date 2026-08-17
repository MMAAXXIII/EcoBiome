# EcoBiome — G4 Provider Retention Bridge V1

**Status:** implementation candidate for feature publication  
**Gate:** `ECOBIOME_G4_PROVIDER_RETENTION_BRIDGE_V1`

## Goal

Close the operational G4 seam on top of the existing Scientific Foundation V6
without creating Schema V7.

The bridge proves this chain:

```text
Collector source request
→ V6 Claim/Evidence snapshot verification
→ request CAS
→ provider-run audit
→ response CAS
→ V2.9 admission
→ validated-output CAS
→ V2.11 canonical candidate
→ candidate Evidence links
→ provider proposal origins
→ append-only completed run
```

## Exact product scope

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_persistence/contracts.py`
3. `src/ecobiome/knowledge_persistence/sqlite_store.py`
4. `src/ecobiome/knowledge_acquisition/semantic_provider_retention_v1.py`
5. `tests/test_semantic_provider_retention_g4.py`
6. `docs/handoffs/PASSATION_ECOBIOME_G4_PROVIDER_RETENTION_V1.md`

## Design

### No schema migration

Scientific Foundation V6 already contains all required tables and indexes.
G4 adds only two read methods to the provenance repository:

- `get_source_evidence(evidence_id)`
- `get_segment(segment_id)`

These allow the bridge to verify the Collector request against canonical V6
rows before writing audit artifacts.

### Collector compatibility

`retain_collector_provider_run_v1(...)` calls the existing
`build_semantic_extraction_request(...)` on the real `CollectorStore`.

Only reviewed, non-rejected source Claims may be retained. The bridge compares:

- effective Claim text;
- effective Claim SHA-256;
- effective Claim review status;
- Evidence ID;
- segment ID;
- Evidence text;
- Evidence SHA-256;
- V6 segment integrity.

Any Claim/Evidence drift fails before request/response/validated CAS writes.

### Provider-neutral retention

The bridge accepts already-returned provider bytes/output. It performs no
network call.

The actual request bytes and response bytes are stored unchanged in the V6 CAS.
The validated compact output is stored as deterministic provider-domain JSON.

The provider run records exact identities for:

- provider and adapter;
- model;
- V2.10 relation registry;
- provider output schema;
- source request;
- request body;
- safe configuration;
- request fingerprint.

### V2.9 → V2.11

The bridge uses existing frozen logic:

- V2.9 source-scope / relation-type / grounding admission;
- V2.11 canonical candidate construction.

Provider proposals are evaluated by original proposal index. Every surviving
provider proposal receives an origin row. If duplicate proposals collapse into
one canonical candidate, all proposal origins remain preserved.

### Append-only / replay

G4 tests install SQLite triggers that abort every UPDATE/DELETE on provider-run
and candidate tables.

The first retention inserts the run, events, one deduplicated candidate and all
origins.

Exact replay uses immutable identity checks and inserts no duplicate rows.

### Abstention

`{"p": []}` remains a valid audited provider run with zero candidates and zero
origins.

### Scientific safety

`automatic_scientific_acceptance` remains false throughout.

Human Semantic Candidate review remains a separate G2 gate.

## Acceptance criteria

- no SQLite schema change;
- no real provider/network call in G4 tests;
- Collector source request built through the production Collector function;
- stale Collector/V6 Claim snapshot rejected before CAS write;
- request/response/validated output CAS references verified;
- provider lifecycle exactly:
  `provider_response_received → validated → completed`;
- duplicate provider proposals retain separate origins;
- canonical candidate deduplicates;
- exact replay is idempotent;
- zero-proposal abstention succeeds;
- anti-UPDATE/DELETE triggers pass;
- Ruff PASS;
- mypy PASS;
- targeted pytest PASS;
- full pytest PASS;
- exact six-path boundary;
- feature branch only;
- remote `main` unchanged.

## Explicit non-goals

- do not change `semantic-openai` into a live persisted provider command yet;
- do not call OpenAI or any other provider;
- do not add a new table or Schema V7;
- do not auto-review candidates;
- do not auto-project candidates into Scientific Assertions;
- do not delete or rewrite historical audit rows.

## Next gate after merge

G5 may proceed to the entity-resolution operator workflow. A later provider
adapter may call this retention bridge once a live V2.10 wire adapter is
separately reviewed.
