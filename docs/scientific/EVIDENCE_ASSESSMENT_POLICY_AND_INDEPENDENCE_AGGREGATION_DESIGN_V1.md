# EcoBiome — Evidence Assessment Policy + Independence Aggregation Design V1

Status: pending human review
Gate: RATE-2Q

## 1. RATE-2P basis

```text
RATE-2P materialization payload
0f992cec2aa0f6d84dd1739da5d231e1b8436edeeff5c58dff7d9cb0dd5c27a4

RATE-2P independence projection contract
87df15ce0cd0201414fd39e9940af66249a67c48ef41ab19fdbf25b60ca1ce86
```

RATE-2P proved that both reviewed EvidenceAssessment candidates can be
materialized in a disposable V6 copy while preserving:

```text
pairwise status              = partially_independent
per-link independence_status = unresolved
independent support count    = null
```

## 2. Proposed stable EvidenceAssessment policy

Promotion candidate SHA-256:

```text
508e273824f6e0b58765b6034c8e1a993c93d57ed8359a72a482d7e559a42ad1
```

Proposed stable identity:

```text
ecobiome-evidence-assessment-1
```

This is a policy-identity promotion only. It does not authorize changes to the
reviewed scientific fields.

The existing candidate rows use:

```text
ecobiome-evidence-assessment-1-candidate
```

A future stable materialization may change only that policy identity after
explicit human approval.

## 3. Independence aggregation

Aggregation design SHA-256:

```text
f44bc14c91ace946836a0b11d5480244664133ab95449910a15498dfb0c2c75f
```

The frozen KnowledgeSynthesis contract requires:

```text
independent_support_origin_count: int
```

and the physical V6 column is a NOT NULL INTEGER.

Therefore the reviewed state:

```text
partially_independent
```

cannot be represented faithfully as:

```text
0
1
2
```

without an additional policy assumption.

RATE-2Q proposes the fail-closed rule:

```text
partially_independent -> NO INTEGER PROJECTION
unresolved            -> NO INTEGER PROJECTION
```

No fractional count and no rounding are allowed.

## 4. Current consequence

For the two ammonia-to-nitrite support origins:

```text
support_link_count                 = 2
pairwise relationship              = partially_independent
independent_support_origin_count   = null
KnowledgeSynthesis materializable  = false
```

This is intentional. A mandatory integer field is not a reason to manufacture
an integer.

## 5. Exact-count cases

An integer can be produced only when the origin structure is discrete:

```text
0 origins -> 0
1 origin  -> 1
all pairwise fully independent -> number of origins
explicit reviewed same-origin equivalence -> number of equivalence classes
```

Any partially-independent or unresolved relation blocks synthesis.

## 6. No persistence

```text
stable assessment policy adopted = false
knowledge_synthesis created       = false
schema migration                  = false
real V6 write                     = false
ProcessScientificSupportV1        = false
numeric RateModel                 = false
remote write                      = false
```

## 7. Human boundary

RATE-2Q proposes two decisions for explicit review:

```text
1. promote ecobiome-evidence-assessment-1-candidate
   -> ecobiome-evidence-assessment-1

2. accept fail-closed independence aggregation:
   partially_independent/unresolved -> block KnowledgeSynthesis
```

## 8. Next gate

```text
RATE-2R — Assessment Policy + Independence Aggregation Human Review
```
