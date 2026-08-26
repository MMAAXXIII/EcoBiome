# EcoBiome — Assessment Policy + Independence Aggregation Human Review V1

Status: human review completed
Gate: RATE-2R

## Human decisions

```text
policy promotion = revise
aggregation       = accept
```

Policy decision SHA-256:

```text
1a438a4b9146cf6c5ef6167a0c1c4d0b574950affc2a822c598929861b609cdf
```

Aggregation decision SHA-256:

```text
e48fa7b41b3efae5cbff7e1fff438553f9a478e8ded6f60933d6b321f74a64e8
```

Reviewed replacement EvidenceAssessment policy SHA-256:

```text
ff95c9aa278772d7bf58a17dcd93fe386795dc6320f42a6f911873cc1128e59b
```

## Revised stable policy candidate

Stable identity retained:

```text
ecobiome-evidence-assessment-1
```

The reviewed scientific assessment rules from RATE-2Q are retained, except
for the independence semantics.

For V1:

```text
EvidenceAssessmentsRow.independence_status = unresolved
```

is the only admitted per-link value.

The relational states:

```text
dependent
partially_independent
independent
```

belong to the separate pairwise evidence-origin independence policy.

No pairwise relationship is silently projected onto an individual
EvidenceAssessment row.

## Aggregation policy accepted

The fail-closed integer aggregation is accepted:

```text
partially_independent -> no integer projection
unresolved            -> no integer projection

fractional counting   -> forbidden
rounding              -> forbidden
```

Therefore the current ammonia-to-nitrite evidence state remains:

```text
support_link_count               = 2
pairwise_status                  = partially_independent
independent_support_origin_count = null
KnowledgeSynthesis materializable = false
```

## Persistence boundary

RATE-2R records human review only:

```text
real V6 write                 = false
KnowledgeSynthesis created    = false
schema migration              = false
ProcessScientificSupportV1    = false
numeric RateModel             = false
remote write                  = false
```

The replacement stable policy candidate is authorized only for future
disposable-shadow materialization.

## Next gate

```text
RATE-2S — Stable EvidenceAssessment Policy Shadow Projection
```
