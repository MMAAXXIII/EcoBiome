# EcoBiome — First Derived Snapshot Promotion Execution Human Review V1

Status: human review completed
Gate: RATE-3B

## Decisions

```text
execution plan            = revise
promotion-engine contract = revise
```

Decision identities:

```text
execution-plan decision
c204071ea181d6387350841ff9ea8955b908396a44a8463decb9039988da4398

promotion-engine decision
cc960686dab49d96fa50cc0df6808a2646fcd86cf0bcd777448e1ac58ece608e

revision boundary
7e45dad9ee2e3f6601e6fc4d55052e5de52e9175514d06ac6c9241366066f2b2

review package
e9ea006f687ac1ae46e59871bc00a0a6bc25d6bc8fe49225bd7f3e2a467e6abb
```

## Mandatory revision 1 — exhaustive replay manifest

Before any staging database is created, EcoBiome must produce:

```text
FIRST_DERIVED_SNAPSHOT_REPLAY_MANIFEST_V1
```

Every promoted row must bind:

```text
table
row_id
canonical row payload SHA-256
provenance/review SHA-256
dependency IDs
```

Expected table deltas remain useful regression checks but are not scientific
identity.

## Mandatory revision 2 — separate code and Git identities

The execution contract must distinguish:

```text
scientific_input_repo_head
promotion_contract_repo_head
promotion_engine_repo_head
promotion_engine_code_identity_sha256
```

The final snapshot manifest must bind the exact engine implementation actually
executed.

## Mandatory revision 3 — atomic complete publication

Publication must use:

```text
execution-scoped temporary directory
    ↓
scientific-foundation.sqlite3
snapshot-manifest.json
    ↓
fsync both files
    ↓
fsync temporary directory
    ↓
verify complete pair
    ↓
atomic directory rename
    ↓
<final-database-sha256>/
```

A pre-existing partial or inconsistent final directory is fatal. It must never
be silently completed or overwritten.

## Mandatory revision 4 — row-by-row identity validation

After the replay transaction, the staging database must be re-read and every
promoted row must reproduce the canonical row SHA-256 recorded in the replay
manifest.

The following remain additional checks:

```text
exact table deltas
PRAGMA quick_check
PRAGMA foreign_key_check
full regression suite
```

## Preserved architecture

RATE-3B does not revise these decisions:

```text
parent_kind                  = legacy_root
Schema                       = V6
schema migration             = false
single scientific transaction = required
CAS exact bytes              = required
source_lineage_edges delta   = 0
KnowledgeSynthesis delta     = 0
active pointer update        = false
real V6 write                = false
numeric RateModel            = false
```

## Authorization boundary

RATE-3B is review-only:

```text
staging DB creation    = false
snapshot creation      = false
active pointer update  = false
real V6 write          = false
remote write           = false
```

## Next gate

```text
RATE-3C — Replay Manifest + Promotion Engine Candidate
```

RATE-3C must build the exhaustive replay manifest, revised contracts and a
reviewable promotion-engine candidate whose code identity can be frozen.
It must still not create a staging database or scientific snapshot.
