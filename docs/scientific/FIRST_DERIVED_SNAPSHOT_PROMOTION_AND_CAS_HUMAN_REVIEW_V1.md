# EcoBiome — First Derived Snapshot Promotion + CAS Human Review V1

Status: human review completed
Gate: RATE-2W

## Human decisions

```text
promotion plan = accept
CAS contract   = accept
```

Promotion-plan decision SHA-256:

```text
8f0ee6980f1bdd4a14659f0ce47aa3df9395898305837c7f688eb0c75fecf986
```

CAS-contract decision SHA-256:

```text
487b6efbbcf9c79ad4ec55a332f90eb598d1343c635a42dfb31d3fd0b7e06acd
```

Review-package SHA-256:

```text
6ecff9702dc5c66ef5dfe840ec4c3501b29de7193f01964ef684d4ab4d061d9d
```

## Accepted promotion boundary

The first durable scientific snapshot remains a data-only derivative of the
frozen V6 legacy root:

```text
parent_kind            = legacy_root
parent_manifest_sha256 = null
schema_version          = 6
schema_migration        = false
```

The parent V6 database may never be modified by this promotion.

The reviewed replay remains isolated and transactional on a staging copy before
any immutable snapshot publication.

## Accepted CAS contract

Canonical durable CAS:

```text
EcoBiome-data/scientific-artifact-cas
```

Artifact identity:

```text
sha256:<64-lowercase-hex>
```

Filesystem placement:

```text
sha256/<aa>/<bb>/<digest>.blob
```

Both primary-source raw XML artifacts are mandatory:

```text
10.1038/nature16459
fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112

10.1038/nature16461
0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
```

A missing artifact, a symlink, or a SHA-256 mismatch blocks snapshot promotion.

A live network response is only a candidate byte source. It becomes eligible
for promotion only after the bytes match the already-reviewed SHA-256 and are
admitted to the canonical durable CAS.

## Current readiness

RATE-2V observed:

```text
canonical CAS ready = false
promotion blocked   = true
```

That local readiness observation is not silently converted into scientific
state and is not persisted into V6.

## Authorization boundary

RATE-2W accepts policy/plan only:

```text
durable CAS write        = false
network acquisition      = false
snapshot creation        = false
active pointer update    = false
real V6 write            = false
schema migration         = false
KnowledgeSynthesis       = false
numeric RateModel        = false
remote write             = false
```

## Next gate

```text
RATE-2X — Primary Source CAS Materialization Plan
```

RATE-2X must define how candidate source bytes can be recovered/acquired,
verified against the frozen hashes, and admitted create-only to the canonical
CAS. It still must not create the scientific snapshot.
