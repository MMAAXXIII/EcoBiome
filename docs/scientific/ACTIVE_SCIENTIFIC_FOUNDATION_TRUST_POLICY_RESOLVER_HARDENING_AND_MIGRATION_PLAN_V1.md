# EcoBiome — Active Foundation Trust Policy / Resolver Hardening

Status:

```text
candidate pending human review
active pointer remains absent
runtime migration = none
```

## Trust model

The mutable pointer is not trusted by itself.

A present pointer is accepted only when all of its target identities match a
separately supplied runtime-policy document whose canonical SHA exactly equals
the caller-provided reviewed SHA.

Runtime-policy contract SHA-256:

```text
6005177695e1495e887a986e4db2686badd64655cbe06b5974720afc3db9885f
```

## Missing-pointer semantics

```text
pre activation:
  pointer_required = false
  missing pointer -> verified V6 fallback

post activation:
  pointer_required = true
  missing pointer -> FAIL CLOSED
```

## Consumer roles

Role-aware audit SHA-256:

```text
e675d2b6a2194cb59af93e00056173b48ba7af90f4ce190ba070ac380b83e494
```

Automatic read-consumer migration allow-list:

```text
["src/ecobiome/reasoning/nitrogen_vertical_runtime_v1.py", "src/ecobiome/ui/local_api.py"]
```

Runtime files by role:

```json
{
  "administrative_migration": [
    "src/ecobiome/knowledge_acquisition/migration_v2.py",
    "src/ecobiome/knowledge_persistence/snapshot_promotion_v1.py"
  ],
  "explicit_read_override": [
    "src/ecobiome/cli/nitrogen_demo.py"
  ],
  "persistence_infrastructure": [
    "src/ecobiome/knowledge_persistence/__init__.py",
    "src/ecobiome/knowledge_persistence/active_foundation_v1.py",
    "src/ecobiome/knowledge_persistence/collector_compat.py",
    "src/ecobiome/knowledge_persistence/config.py",
    "src/ecobiome/knowledge_persistence/contracts.py",
    "src/ecobiome/knowledge_persistence/errors.py",
    "src/ecobiome/knowledge_persistence/sqlite_schema.py",
    "src/ecobiome/knowledge_persistence/sqlite_store.py"
  ],
  "runtime_read_consumer": [
    "src/ecobiome/reasoning/nitrogen_vertical_runtime_v1.py",
    "src/ecobiome/ui/local_api.py"
  ],
  "scientific_reference_only": [
    "src/ecobiome/reasoning/nitrogen_vertical_demonstration_v1.py"
  ],
  "write_capable_acquisition": [
    "src/ecobiome/knowledge_acquisition/collector_acquire.py",
    "src/ecobiome/knowledge_acquisition/collector_cli.py",
    "src/ecobiome/knowledge_acquisition/persistence.py",
    "src/ecobiome/knowledge_acquisition/retention.py",
    "src/ecobiome/knowledge_acquisition/semantic_provider_retention_v1.py"
  ],
  "write_capable_review_administration": [
    "src/ecobiome/knowledge_acquisition/semantic_candidate_entity_resolution_cli_v1.py",
    "src/ecobiome/knowledge_acquisition/semantic_candidate_review_cli_v1.py"
  ]
}
```

Migration plan SHA-256:

```text
a580cc8d0ac8b95142c327b64abdc6d0336ba5295725b82413391f48d933ccab
```

No migration is performed by RATE-3M.

## Windows path hardening

The resolver rejects:

```text
symlink
junction
generic FILE_ATTRIBUTE_REPARSE_POINT
```

## Persistent boundary

RATE-3M must leave unchanged:

```text
frozen V6
persistent CAS
persistent snapshot
```

and leave:

```text
scientific-foundation-active.json = ABSENT
```
