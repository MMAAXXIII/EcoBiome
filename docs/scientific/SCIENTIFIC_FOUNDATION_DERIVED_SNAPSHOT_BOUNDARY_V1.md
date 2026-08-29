# EcoBiome — Scientific Foundation Derived Snapshot Boundary V1

Status: pending human review
Gate: RATE-2T

Boundary design SHA-256:

```text
7cc40c48504639d13b9f1b20596a55796b73f93a75e10ff581b5a078b57e808a
```

Snapshot manifest contract SHA-256:

```text
8675774056188fce62c7c29cf816238d155871bf69aaa79ee85e8b1567b2cf20
```

## 1. Problem

RATE-2S proves that the reviewed ammonia-to-nitrite evidence chain can be
materialized under the stable EvidenceAssessment policy.

The real Scientific Foundation V6 is still an immutable reference:

```text
database SHA-256
76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f

schema version
6

schema design SHA-256
e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181
```

The next persistence step must not turn that frozen reference into a mutable
working database.

## 2. Recommended boundary

Use an **immutable derived snapshot series**.

Each durable promotion:

1. starts from an exact immutable parent snapshot;
2. creates an isolated copy;
3. replays only reviewed and authorized scientific mutations;
4. validates the resulting database;
5. freezes it under its own database SHA-256;
6. records a canonical sidecar manifest;
7. leaves the parent byte-for-byte unchanged.

A data-only promotion using Schema V6 remains **Schema V6**. It must not be
called Schema V7 merely because more reviewed rows exist.

## 3. Storage model

Recommended logical layout:

```text
EcoBiome-data/
  scientific-foundation-v6/
    scientific-foundation-v6.sqlite3        # frozen reference

  scientific-foundation-snapshots/
    <database-sha256>/
      scientific-foundation.sqlite3         # immutable derived snapshot
      snapshot-manifest.json                # canonical provenance/validation

  scientific-foundation-active.json         # optional pointer only
```

The active pointer is operational metadata, not scientific content. Updating
it is a separate authorization from creating a snapshot.

## 4. Promotion must be offline with respect to reviewed source bytes

The durable replay must consume frozen source artifacts by SHA-256 from the
external CAS/data store. It must **not** re-fetch a live URL and merely hope the
publisher returns identical bytes.

Required primary artifacts for this vertical:

```text
10.1038/nature16459
fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112

10.1038/nature16461
0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
```

If those exact bytes are not present in durable external CAS, snapshot
promotion remains blocked until they are materialized and verified there.

## 5. First G7A durable snapshot scope

A first derived snapshot would contain, in addition to the V6 parent state:

```text
reviewed nitrite entity
reviewed ammonia -> nitrite assertion
two Nature source/evidence chains
two human claim reviews
two reviewed assertion-claim links
two EvidenceAssessments using ecobiome-evidence-assessment-1
```

It would deliberately contain:

```text
KnowledgeSynthesis            = none
independent_support_origin_count = unresolved/null at policy level
ProcessScientificSupportV1    = none
numeric RateModel             = none
```

The accepted `partially_independent` relation is preserved outside the
mandatory integer KnowledgeSynthesis count.

## 6. Reproducibility model

Scientific replay must be logically exact against reviewed canonical payloads.

Byte-for-byte recreation of a derived database is not required because
authorized materialization timestamps can differ. Once created, however, each
published snapshot is immutable and identified by its own exact database
SHA-256.

## 7. Git boundary

Git stores:

```text
policies
review decisions
snapshot manifest contracts
small canonical manifests / hashes
handoffs
```

Git does not store by default:

```text
SQLite snapshot bytes
primary article XML/full text
large CAS artifacts
```

## 8. No authorization yet

RATE-2T is design-only:

```text
derived snapshot creation    = NOT authorized
active pointer update        = NOT authorized
real V6 mutation             = forbidden
schema migration             = NOT authorized
numeric RateModel            = NOT authorized
remote write                 = false
```

## 9. Next gate

```text
RATE-2U — Evidence Foundation Persistence Boundary Human Review
```
