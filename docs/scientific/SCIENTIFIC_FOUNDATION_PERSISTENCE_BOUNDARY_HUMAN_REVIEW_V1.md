# EcoBiome — Evidence Foundation Persistence Boundary Human Review V1

Status: human review completed
Gate: RATE-2U

## Human decisions

```text
snapshot boundary = accept
manifest contract = revise
```

Boundary decision SHA-256:

```text
796d7f2e2130efada77a914a7fd85f243b38788e06c0e283b479d0909981f990
```

Manifest decision SHA-256:

```text
17ed6f4d14f504f331c15a3b1b5c32bcdb3e649aa18da695756483a11bc2f0b5
```

Revised manifest contract SHA-256:

```text
67b73c0a1cc4d514c146b7d09a042720721a4c1e68074f0c7e7680bd08fa7b74
```

Effective review package SHA-256:

```text
f6a29e569b5b73a9862b126a3805fc915d0dc77c6910c519d916c228e3ea3fff
```

## Accepted snapshot boundary

The RATE-2T architecture is accepted unchanged:

```text
immutable parent snapshot
-> isolated staging copy
-> reviewed replay
-> validation
-> immutable content-addressed derived snapshot
-> canonical sidecar manifest
-> separately-authorized optional active pointer
```

The frozen Scientific Foundation V6 remains immutable.

A data-only promotion using physical Schema V6 remains Schema V6.

Live-network refetch is not an accepted durable promotion input; reviewed
source bytes must be supplied from frozen external CAS/data storage by exact
SHA-256.

## Revised manifest lineage

The revised manifest explicitly distinguishes:

```text
parent_kind = legacy_root
parent_kind = derived_snapshot
```

For the frozen historical V6 root:

```text
parent_kind                 = legacy_root
parent_database_sha256      = required
parent_manifest_sha256      = null
```

For any derived snapshot descended from another derived snapshot:

```text
parent_kind                 = derived_snapshot
parent_database_sha256      = required
parent_manifest_sha256      = required
```

Inventing a synthetic parent manifest for the legacy V6 root is forbidden.

## Runtime and persistence identity

Every durable snapshot manifest must now record:

```text
sqlite_version
python_version
persistence_schema_design_sha256
promotion_engine_identity
```

`promotion_engine_identity` binds at minimum:

```text
name
version_or_gate
source_repo_head
code_identity_sha256
```

These fields explain which persistence implementation produced the immutable
snapshot. They do not create a false requirement for byte-for-byte database
reproduction across different SQLite/Python runtimes.

## Authorization boundary

RATE-2U records human review only:

```text
derived snapshot creation = false
active pointer update     = false
real V6 write             = false
schema migration          = false
KnowledgeSynthesis        = none
numeric RateModel         = false
remote write              = false
```

## Next gate

```text
RATE-2V — First Derived Snapshot Promotion Plan + CAS Preflight Design
```
