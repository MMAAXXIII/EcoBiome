# EcoBiome — Evidence Assessment + Independence Human Review V1

Status: human review completed
Gate: RATE-2O

## Human decisions

```text
assessment 1: accept
assessment 2: accept
independence: accept partially_independent
independent_support_origin_count: null
```

### van Kessel

Decision SHA-256:

```text
5987f2b7cd5855084271610e90739b7e220a12fc85350b5893d43f0a410b219d
```

Accepted scientific classification:

```text
study_design =
experimental_enrichment_culture_multimodal

evidence_directness =
direct_functional_support_with_intermediate_inference

independence_status =
unresolved
```

### Daims

Decision SHA-256:

```text
bf3f28e41a21666e504f4e4473402f2d37ff6a0ff9c53de4abd2350eb806ebbe
```

Accepted scientific classification:

```text
study_design =
experimental_enrichment_culture_multimodal

evidence_directness =
direct_functional_support

independence_status =
unresolved
```

### Pairwise independence

Decision SHA-256:

```text
322403f8a55f1557326fdd2c5e8a71c47aff9d8b0faa2d3b45893ed7b4b4db34
```

Accepted pairwise classification:

```text
partially_independent
```

The independent-support count remains deliberately unset:

```text
independent_support_origin_count = null
```

## Projection boundary

The accepted pairwise classification is not automatically copied into both
per-link `EvidenceAssessmentsRow.independence_status` fields.

Those fields remain:

```text
unresolved
```

until a dedicated pairwise-to-per-link projection policy is defined and
validated. This prevents a relational property from being silently encoded as
an intrinsic property of each evidence row.

## Persistence metadata

The RATE-2N candidate rows used placeholder metadata:

```text
assessor   = rate-2n-automation-pre-human-review
created_at = candidate-not-persisted
```

Future shadow materialization must preserve the scientific fields exactly but
project persistence metadata to:

```text
assessor   = human_user_current_conversation
created_at = actual materialization timestamp
```

## Boundaries

```text
evidence_assessments inserted = 0
source_lineage_edges inserted = 0
knowledge_syntheses inserted  = 0
real V6 write                 = false
ProcessScientificSupportV1    = false
numeric RateModel             = false
remote write                  = false
```

## Next gate

```text
RATE-2P — Reviewed EvidenceAssessment Shadow Materialization
          + Independence Projection Contract
```
