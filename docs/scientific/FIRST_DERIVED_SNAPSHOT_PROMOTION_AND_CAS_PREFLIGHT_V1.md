# EcoBiome — First Derived Snapshot Promotion Plan + CAS Preflight V1

Status: pending human review
Gate: RATE-2V

Promotion plan SHA-256:

```text
e7ed080b299b9da325ad056d31155a860fb9a03c64bc72420d2d113aa324cb7a
```

CAS preflight contract SHA-256:

```text
1319bcaf8cb599c5888b82a37dbd941bc483de1370fa802e9e69a1737241b1ac
```

## 1. Parent and target

The first durable snapshot is a derived data snapshot of the frozen V6 root:

```text
parent_kind             = legacy_root
parent_database_sha256  = 76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
parent_manifest_sha256  = null
schema_version           = 6
schema_migration         = false
```

The parent database remains byte-for-byte immutable.

The result, if later authorized, will also use physical Schema V6 and will be
identified by its own final database SHA-256.

## 2. Durable scientific-artifact CAS

RATE-2V proposes the logical root:

```text
EcoBiome-data/scientific-artifact-cas
```

using the repository's existing `FilesystemContentAddressedArtifactStore`
contract:

```text
artifact key:
sha256:<digest>

relative path:
sha256/<first 2>/<next 2>/<digest>.blob
```

The current local CAS inventory is deliberately **not committed** because
artifact presence and absolute paths are machine-local facts. It is captured
only in the RATE-2V audit bundle.

## 3. Required immutable source bytes

Snapshot promotion requires both exact raw XML artifacts:

```text
10.1038/nature16459
fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112

10.1038/nature16461
0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
```

A live re-download is not a substitute for CAS readiness.

A verified copy elsewhere under `EcoBiome-data` may be reported as a recovery
candidate, but it does not make the canonical CAS ready and is never copied by
RATE-2V.

## 4. Replay verification

The promotion engine must derive and verify the already-frozen representation,
segment, evidence and claim hashes from those source bytes before persistence.

No scientific content may be silently regenerated into a different canonical
identity.

## 5. Expected scientific delta

The first durable snapshot is expected to add the reviewed nitrite identity,
ammonia-to-nitrite assertion, two source/evidence chains, two claim reviews,
two reviewed assertion links and two stable-policy EvidenceAssessments.

It deliberately adds:

```text
source_lineage_edges = 0
knowledge_syntheses  = 0
```

The reviewed pairwise state remains:

```text
partially_independent
```

while each EvidenceAssessment remains:

```text
independence_status = unresolved
```

## 6. Promotion sequence

```text
verify parent + reviewed identities
verify frozen source bytes in durable CAS
copy parent -> isolated staging
transactional reviewed replay on staging
validate canonical replay identities
quick_check + FK check
full repo regression
close staging DB
compute final DB SHA-256
publish create-only snapshot directory
write canonical sidecar manifest
```

Updating `scientific-foundation-active.json` is not part of this promotion.

## 7. Current authorization

RATE-2V is design + read-only CAS preflight only:

```text
CAS creation/copy       = false
snapshot creation       = false
active pointer update   = false
real V6 write           = false
schema migration        = false
KnowledgeSynthesis      = false
numeric RateModel       = false
remote write            = false
```

## 8. Next gate

```text
RATE-2W — First Derived Snapshot Promotion + CAS Contract Human Review
```
