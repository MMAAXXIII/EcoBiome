# EcoBiome — RATE-3E Promotion Engine Corrections

Status: candidate pending human review

RATE-3D human decision:

```text
b29915795b57f36c62a3a883d1599065bf0a8a3bccc4f03c3e6e5080723e2598
```

Unchanged scientific replay identity:

```text
26f7a1f7b8cef2a6e7ad7e0f861a65fd12de89bace4270202447fe3b821e801a
32 rows
knowledge_sources +3
```

Corrected engine source SHA-256 before commit:

```text
8831fdc239c01ee311ad5cfe39a48f6a92e0625fb7db14906d650e6a4054c3ee
```

## Corrections

### A — CAS missing vs corruption

The engine now catches only:

```text
ArtifactMissingError
```

for an absent derived representation.

`ArtifactCorruptionError` is never reclassified as "missing" and fails closed.

### B — replay-manifest SHA

The replay payload and its reviewed canonical SHA are distinct execution
inputs. The SHA is checked before effects and is explicitly embedded into the
future snapshot manifest.

### C — reviewed authorization / identity binding

A future execution must provide an authorization payload whose SHA is already
frozen by the invoking reviewed gate.

Before any CAS or filesystem effect, the engine verifies:

```text
authorization SHA
authorization canonical payload
identity-binding canonical payload
replay-manifest canonical payload
scientific_input_repo_head
promotion_contract_repo_head
promotion_engine_repo_head
promotion_engine_code_identity_sha256
```

### D — Windows durability

The invalid directory `FlushFileBuffers` claim is removed.

Windows publication uses:

```text
DB fsync
manifest fsync
MoveFileExW(source_dir, final_dir, MOVEFILE_WRITE_THROUGH)
```

for the same-volume publication rename.

POSIX retains directory `fsync` + atomic rename + parent-directory `fsync`.

### E — execution-path tests

RATE-3E adds tests for:

```text
missing derived CAS artifact / unauthorized
missing derived CAS artifact / authorized synthetic materialization
CAS corruption fail-closed
unreviewed authorization SHA
replay SHA drift
identity-binding drift
synthetic complete promotion
snapshot-manifest identity binding
partial existing final directory
inconsistent existing final directory
Windows write-through path through the synthetic E2E test
```

The complete synthetic promotion uses only pytest temporary files and an
in-memory CAS. It is not a Scientific Foundation staging execution.

## Boundary

```text
real V6 replay = false
persistent CAS write = false
persistent scientific snapshot = false
remote write = false
```
