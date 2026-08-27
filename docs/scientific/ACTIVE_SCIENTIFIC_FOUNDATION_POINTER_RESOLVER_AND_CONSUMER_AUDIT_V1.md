# EcoBiome — Active Scientific Foundation Pointer / Resolver V1

Status:

```text
candidate pending human review
active pointer remains absent
```

RATE-3J decision:

```text
291334022d275d3107aaf5c6ffba42db7b83e2e66def61f58e546d10d5cef28b
```

## Contract

Pointer document:

```text
pointer_payload_sha256
pointer_payload
```

Pointer payload binds only immutable/content identities:

```text
snapshot database SHA
snapshot-manifest file SHA
snapshot-manifest payload SHA
parent database SHA
activation authorization SHA
activation timestamp
```

It contains no arbitrary database path.

## Resolver semantics

```text
pointer absent
    → verify frozen legacy database
    → legacy_fallback

pointer present and valid
    → verify pointer canonical SHA
    → derive content-addressed snapshot path from database SHA
    → verify DB + manifest + schema + quick_check + FK
    → active_snapshot

pointer present but malformed/corrupt
    → FAIL CLOSED
```

There is intentionally no persistent pointer writer in RATE-3K.

## Consumer audit

Consumer audit payload SHA-256:

```text
56064e2de369bc6f2a5cb24b6188d2cf22ffe512cf1ecab587f71451229dc6d1
```

Python files scanned:

```text
344
```

Runtime files with relevant references:

```text
20
```

Legacy-V6 fixed-path runtime references:

```text
["src/ecobiome/reasoning/nitrogen_vertical_runtime_v1.py", "src/ecobiome/ui/local_api.py"]
```

Active-pointer/resolver runtime references:

```text
[]
```

This audit is deliberately conservative.  RATE-3K does not migrate any runtime
consumer.  Activation readiness therefore remains:

```text
HOLD
```

## Safety boundary

RATE-3K must leave byte-identical:

```text
frozen V6
persistent CAS
persistent snapshot
```

and must leave:

```text
scientific-foundation-active.json
ABSENT
```
