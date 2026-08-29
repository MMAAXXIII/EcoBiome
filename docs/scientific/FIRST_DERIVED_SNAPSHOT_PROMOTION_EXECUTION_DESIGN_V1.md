# EcoBiome — First Derived Snapshot Promotion Execution Design V1

Status: pending human review
Gate: RATE-3A

Execution plan SHA-256:

```text
e538a2627336969b86aeeed0d0dabf2773fe71be1135dec7b09b5eb4d464d052
```

Promotion-engine contract SHA-256:

```text
21917d539e76222e50a1af3fdf9a013b1ea3de13dc9b34419b45ea55ea8128ac
```

## 1. Readiness

RATE-2Z R4 removed the durable-source blocker.

Both source artifacts are currently verified from the canonical CAS:

```text
nature16459
sha256:fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112
153875 bytes

nature16461
sha256:0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
194672 bytes
```

The frozen V6 parent remains the immutable legacy root:

```text
database SHA-256 = 76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
schema version   = 6
schema migration = false
```

## 2. Execution model

A future authorized execution must use:

```text
frozen V6 parent
      ↓ copy
isolated temporary staging DB
      ↓
single transactional reviewed replay
      ↓
quick_check / FK / exact deltas / regression
      ↓ close DB
final database SHA-256
      ↓
create-only content-addressed snapshot
      ↓
canonical sidecar manifest
      ↓
read-only final verification
```

The parent database is never opened writable.

## 3. Exact scientific scope

The first snapshot contains only the already-reviewed nitrogen evidence scope:

```text
nitrite entity                         +1
ammonia-to-nitrite assertion           +1
Nature source chains                   +2
claim reviews                          +2
reviewed assertion links               +2
stable-policy EvidenceAssessments      +2
```

No `KnowledgeSynthesis` and no `source_lineage_edges` are created.

Per-link independence remains `unresolved`; the reviewed pairwise
`partially_independent` state remains relational and external to the individual
EvidenceAssessment rows.

## 4. Publication semantics

The final snapshot directory is:

```text
EcoBiome-data/scientific-foundation-snapshots/<final-database-sha256>/
```

with:

```text
scientific-foundation.sqlite3
snapshot-manifest.json
```

Publication is immutable/create-only.

Because the parent is `legacy_root`:

```text
parent_database_sha256 = 76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
parent_manifest_sha256 = null
```

The manifest must also bind Python, SQLite, Schema V6 design identity and the
exact promotion-engine code identity.

## 5. Authorization boundary

RATE-3A performs no database copy/replay/publication:

```text
snapshot creation      = false
active pointer update  = false
real V6 write          = false
schema migration       = false
KnowledgeSynthesis     = false
numeric RateModel      = false
remote write           = false
```

## 6. Next gate

```text
RATE-3B — First Derived Snapshot Promotion Execution Human Review
```

RATE-3B may accept or revise this exact execution contract. Actual snapshot
creation still requires an explicit authorization after the execution engine
identity is frozen.
