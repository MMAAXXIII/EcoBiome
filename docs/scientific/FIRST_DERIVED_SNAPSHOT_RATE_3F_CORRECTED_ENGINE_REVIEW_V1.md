# EcoBiome — RATE-3F Corrected Engine Review

Human decision:

```text
ACCEPT_CORRECTED_PROMOTION_ENGINE_CANDIDATE
AND
AUTHORIZE_RATE_3G_DISPOSABLE_REAL_V6_DRY_RUN
```

Reviewed at:

```text
2026-08-27T02:24:47+02:00
```

Decision SHA-256:

```text
43d79a6d9f1c727b2cef0d554f6bde7c5bbd0a72947406bbeb302a8a6746a339
```

Execution authorization SHA-256:

```text
905e56a76dff794933c3fade8a181d726e2d291a15301a08b324575b0ad1c96d
```

The authorization is explicitly disposable-only.

Allowed:

```text
read frozen real V6
read persistent raw CAS
write execution-temp CAS
write execution-temp snapshot
execute reviewed 32-row replay
```

Forbidden:

```text
write real V6
write persistent CAS
publish persistent scientific snapshot
update active pointer
remote write
```
