# EcoBiome — RATE-3O Consumer Migration Candidate

RATE-3N decision:

```text
c23a7a721ca671bf1ad8b9627671460496ec0f73626ed35129200b4d31fa9054
```

Automatic read consumers migrated:

```text
src/ecobiome/reasoning/nitrogen_vertical_runtime_v1.py
src/ecobiome/ui/local_api.py
```

Central runtime configuration:

```text
src/ecobiome/knowledge_persistence/active_foundation_runtime_config_v1.py
```

Semantics:

```text
default pre-activation read
→ code-reviewed pre-activation policy
→ persistent active pointer absent
→ verified frozen V6 fallback

future active read
→ separately supplied runtime-policy document
+ independently configured expected policy SHA
→ resolver
→ immutable content-addressed snapshot
```

Explicit legacy path override remains explicit and V6-only.

No write/admin persistence path is migrated.

RATE-3O contains no persistent pointer writer and no persistent runtime-policy
publisher.
