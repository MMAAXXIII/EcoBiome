# EcoBiome — RATE-3N Human Review

Decision:

```text
ACCEPT_RATE_3M_TRUST_POLICY_AND_MIGRATION_PLAN
AND
AUTHORIZE_RATE_3O_TEMPORARY_CONSUMER_MIGRATION_INTEGRATION
WITHOUT_PERSISTENT_ACTIVE_POINTER
```

Decision SHA-256:

```text
c23a7a721ca671bf1ad8b9627671460496ec0f73626ed35129200b4d31fa9054
```

Authorized automatic read-consumer migration:

```text
src/ecobiome/reasoning/nitrogen_vertical_runtime_v1.py
src/ecobiome/ui/local_api.py
```

A centralized read-only runtime-config module may be added.

The real immutable snapshot may be read through a temporary policy/pointer
integration only.

Persistent active pointer and persistent runtime-policy publication remain
forbidden.
