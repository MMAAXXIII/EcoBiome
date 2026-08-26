# EcoBiome — Primary Source CAS Materialization Plan + Local Recovery Preflight V1

Status: pending human review
Gate: RATE-2X

Materialization plan SHA-256:

```text
929799c55b5efd4c185cf9455e0515e087347d2ebd73ad6437734af478916c81
```

Local recovery contract SHA-256:

```text
32ba23f44abc1e6a6942c7c34b140e07ba7ff247d93007f7327c1cf788156bbd
```

## 1. Goal

The reviewed snapshot promotion is blocked because the canonical durable CAS is
not ready.

Before acquiring anything from the network, RATE-2X searches the user's
EcoBiome-specific local history for the **exact already-reviewed source bytes**.

Required byte identities:

```text
10.1038/nature16459
fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112

10.1038/nature16461
0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
```

## 2. Local recovery first

The RATE-2X execution bundle contains a machine-local read-only inventory.

It hashes relevant files under:

```text
EcoBiome-data
EcoBiome-operations
Downloads
```

and also streams eligible entries inside historical EcoBiome ZIP bundles.

A match is accepted as a recovery candidate **only** when the complete bytes
have the exact frozen SHA-256.

Filename, DOI text, PMCID, timestamp or bundle name alone are insufficient.

## 3. CAS admission

A future authorized materialization gate must pass the candidate bytes to:

```text
FilesystemContentAddressedArtifactStore.put(bytes)
```

and then require:

```text
returned key       = sha256:<expected digest>
returned SHA-256   = expected digest
post-put verify    = PASS
CAS get bytes hash = expected digest
```

No hand-crafted CAS filepath copy is preferred over the repository's own CAS
implementation.

## 4. Network fallback

Only if an exact local copy is unavailable should EcoBiome acquire candidate
bytes from a public archival full-text repository for the reviewed PMCID.

Network acquisition remains a **separate human authorization**.

An HTTP 200, matching DOI, matching PMCID, or publisher identity does not make
the bytes admissible. Only the already-frozen SHA-256 can do that.

If a network source now returns different bytes, the candidate is rejected and
the existing reviewed scientific chain is not silently rebound.

## 5. Snapshot boundary

CAS materialization and scientific snapshot creation remain distinct.

Even after both blobs are admitted successfully:

```text
snapshot creation      = still separate authorization
active pointer update  = still separate authorization
real V6 write          = forbidden
KnowledgeSynthesis     = none
numeric RateModel      = unauthorized
```

## 6. Next gate

```text
RATE-2Y — Primary Source CAS Materialization Human Review
```

RATE-2Y will use the actual RATE-2X local-recovery result to decide whether
materialization can be local-only or whether network acquisition must also be
authorized.
