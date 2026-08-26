# EcoBiome — Reviewed EvidenceAssessment Shadow Materialization V1

Status: PASS on disposable Scientific Foundation V6 copy
Gate: RATE-2P

Payload SHA-256:

```text
0f992cec2aa0f6d84dd1739da5d231e1b8436edeeff5c58dff7d9cb0dd5c27a4
```

## Materialized shadow chain

RATE-2P reproduces the previously reviewed evidence chain through RATE-2L,
then materializes the two human-accepted RATE-2O EvidenceAssessment candidates
using the frozen V6 `SQLiteScientificAssessmentRepository`.

```text
evidence_assessments +2
source_lineage_edges +0
knowledge_syntheses  +0
```

The scientific assessment fields are preserved from RATE-2N. Only the
persistence metadata explicitly authorized by RATE-2O is projected:

```text
assessor   -> human_user_current_conversation
created_at -> shadow materialization time
```

The assessment IDs are preserved exactly; RATE-2P does not rename a reviewed
candidate during projection.

## Independence projection contract

Reviewed pairwise classification:

```text
partially_independent
```

Per-link persisted value:

```text
independence_status = unresolved
```

This is deliberate. `partially_independent` is a relation between the two
evidence origins; it is not silently copied into either individual
EvidenceAssessmentsRow.

The reviewed aggregation count remains:

```text
independent_support_origin_count = null
```

No `source_lineage_edge` is created because shared authorship / partial
independence is not a derivation relation.

Projection contract SHA-256:

```text
87df15ce0cd0201414fd39e9940af66249a67c48ef41ab19fdbf25b60ca1ce86
```

## Remaining blocker before real persistence

The accepted assessment rows still carry:

```text
policy_version = ecobiome-evidence-assessment-1-candidate
```

RATE-2P proves physical shadow materializability; it does not promote that
candidate policy or authorize real V6 writes.

## Real Scientific Foundation

The real V6 remains byte-for-byte unchanged:

```text
76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
```

## Next gate

```text
RATE-2Q — Evidence Assessment Policy Promotion
          + Independence Aggregation Design
```

RATE-2Q should define a stable non-candidate assessment-policy identity and
decide how, if at all, `partially_independent` contributes to the integer
`independent_support_origin_count` before any KnowledgeSynthesis is created.
