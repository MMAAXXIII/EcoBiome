# EcoBiome — Persistence V5 local implementation

Gate: `ECOBIOME_PERSISTENCE_V5_LOCAL_IMPLEMENTATION_VALIDATED`

Date: 2026-08-15

## Physical persistence contract

- Collector compatibility schema: **2** (unchanged)
- physical SQLite schema: **5**
- tables: **33**
- explicit named indexes: **43**
- COMPLETE_DDL SHA-256: `59f0ff868d229bf6bd029db272fedc39ead83e8153b63fd8d1a2e3925c00d6f2`
- INDEX_ADDENDUM SHA-256: `60b2c279941c0473d22052ac2295f0857cf90c410c3a8517b80f374ab926a9ce`
- runtime schema identity v2 SHA-256: `d13f146dfd6f394ebb660e420c09305a6daca6c0d34232713c9b91b21879310e`
- candidate review policy SHA-256: `cb68231ccb26d398ce3c42c9cae33c8470325390b8e3c524f9d9a1b5a1bc8f61`

## Scope

Schema V5 adds durable append-only semantic provider audit, canonical Semantic
Candidate V2.11 persistence, exact Candidate/Evidence ownership, Candidate human
review events, correction lineage, and provider-to-candidate origins.

Projection V1 now requires the latest deterministic Candidate human review to be
`accept` before the existing Claim/Evidence/entity projection gates run.

Retention protects V5 provider request/response/validated-output CAS references.

## Safety

- fresh-database only;
- no V4 -> V5 automatic migration/adoption;
- no sidecar canonical database;
- no provider/model/network call during implementation validation;
- staging intentionally remains empty;
- no commit/push performed.

## Next boundary

Only after independent review: exact allowlisted staging of the validated V5
implementation. Staging, commit, and push each require their own authorization.
