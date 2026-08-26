# EcoBiome — Primary Source CAS Materialization Human Review V1

Status: human review completed
Gate: RATE-2Y

## Decisions

```text
materialization plan    = accept
local recovery contract = accept
network acquisition     = authorize
durable CAS write       = authorize conditionally
```

Canonical identities:

```text
plan decision       aa1a8b35d0da3b009b09f5c977c7db71f45e3b75f9fe53cd9797d297acefa63c
recovery decision   c35397c486c3915321a89c3e4c8e77b915ae21647bc0192851a76773483ead6d
execution auth      f95193d6f37085b86623c28f732d7003fc64b5bc4f07c619313f7913a0a4fcb3
review package      e024fed918d25bd7ea9d4827e37f54ead68d5657b081c7a6bea6b07795b66561
```

## Bound RATE-2X observation

The authorization is based on the exact reviewed RATE-2X execution bundle:

```text
aded2f2d3a7c14a47e8024c093200e960e268f4954b7352974a2c6bdf39188c2
```

Its local-recovery result established:

```text
nature16459 exact local matches = 0
nature16461 exact local matches = 0
all required locally recoverable = false
network acquisition needed       = true
```

## RATE-2Z authorization

RATE-2Z may obtain candidate bytes for only:

```text
PMC4878690 / 10.1038/nature16459
expected SHA-256:
fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112

PMC5152751 / 10.1038/nature16461
expected SHA-256:
0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
```

A network response is candidate bytes only. HTTP success, DOI, PMCID, publisher
identity or filename cannot authorize admission.

The complete downloaded/recovered bytes must hash exactly to the frozen
identity before any CAS write.

No XML normalization, canonicalization or reserialization may occur before the
identity hash.

## CAS admission

Only an exact candidate may be passed to:

```text
FilesystemContentAddressedArtifactStore.put(bytes)
```

Admission then requires returned key/SHA and post-put `verify()` to match the
same frozen identity.

A mismatch or corrupt existing target fails closed.

## Explicitly still forbidden

```text
scientific snapshot creation = false
active pointer update        = false
real V6 mutation             = false
schema migration             = false
KnowledgeSynthesis           = false
numeric RateModel            = false
remote Git write             = false
```

## Next gate

```text
RATE-2Z — Primary Source CAS Materialization Execution
```
