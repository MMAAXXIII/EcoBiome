# EcoBiome — Stable EvidenceAssessment Policy Shadow Projection V1

Status: PASS on disposable Scientific Foundation V6 copy
Gate: RATE-2S

Projection payload SHA-256:

```text
b32312fdcb51e1408cb9a8ce6a1d3dc31735335f11fe5e72bd5605d73220da7d
```

## Stable policy projection

RATE-2S rebuilds the reviewed ammonia-to-nitrite evidence chain on a fresh
disposable V6 copy and persists exactly two EvidenceAssessment rows using:

```text
policy_version = ecobiome-evidence-assessment-1
```

No row using the candidate policy identity is persisted.

The assessment IDs and all reviewed scientific fields remain unchanged from
RATE-2N/RATE-2O. Only the policy identity and authorized persistence metadata
are projected.

## Independence semantics

Per-link value:

```text
independence_status = unresolved
```

Pairwise reviewed relation:

```text
partially_independent
```

The pairwise relation is not copied to either individual EvidenceAssessment.

```text
independent_support_origin_count = null
```

## Shadow deltas

```text
evidence_assessments +2
source_lineage_edges +0
knowledge_syntheses  +0
```

## KnowledgeSynthesis boundary

The accepted RATE-2R aggregation policy is fail-closed. Because the current
pairwise relation is `partially_independent`, no exact integer can be supplied
to the required `independent_support_origin_count`.

Therefore:

```text
KnowledgeSynthesis materializable = false
KnowledgeSynthesis created        = false
```

## Real Scientific Foundation

The real V6 remains byte-for-byte unchanged:

```text
76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
```

## Next gate

```text
RATE-2T — Evidence Foundation Persistence Boundary Design
```

RATE-2T should decide the durable destination of this reviewed evidence chain
without mutating the frozen V6 by default.
