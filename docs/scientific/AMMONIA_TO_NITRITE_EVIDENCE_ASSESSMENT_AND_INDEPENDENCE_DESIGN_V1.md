# EcoBiome — Evidence Assessment + Independence Design V1

Status: design candidate
Gate: RATE-2M

Canonical plan SHA-256:

```text
835663847237dce5da6b928ff98e862536f3901ea1b06fbe6621b8f832546e90
```

## 1. Starting point

RATE-2L proved that the two human-reviewed assertion/claim link shapes can be
materialized on a disposable Scientific Foundation V6 copy.

RATE-2M deliberately does **not** infer evidence quality from that success.

The current reviewed links are:

```text
van Kessel:
supports / author_interpretation / source_broader / exact

Daims:
supports / author_interpretation / source_broader / compatible_partial
```

`EvidenceAssessmentsRow` is a separate persistence contract. Therefore link
review and evidence-quality review remain separate gates.

## 2. EvidenceAssessment contract

The frozen V6 runtime exposes:

```text
id
assertion_claim_link_id
policy_version
study_design
evidence_directness
endpoint_or_response_json
study_scope_json
methodological_dimensions_json
statistical_result_json
independence_status
limitations_json
assessor
created_at
supersedes_assessment_id
```

Physical DB CHECK detected specifically for `independence_status`:

```text
false
```

RATE-2M does not exploit the absence of a physical enum as permission to invent
arbitrary values. The assessment policy owns a controlled vocabulary.

## 3. Evidence-quality rule

For each reviewed assertion link, a future assessment must derive the following
from the primary source methods/results:

```text
study design
evidence directness
endpoint/response
study scope
sample origin
experimental unit
measurement methods
controls/comparators
replication
analysis pipeline
relevant statistics
limitations
```

The existing link value:

```text
support_mode = author_interpretation
```

must not be silently upgraded to `direct_measurement`.

## 4. Independence is origin-level, not citation-level

Two different DOI values are two publications, not automatically two
independent evidence origins.

Conversely, overlapping authorship is not by itself proof that the underlying
experimental evidence is dependent.

The pair currently has known shared authors:

```text
Mads Albertsen
Per H. Nielsen
```

Therefore:

```text
independent_support_origin_count = unresolved
```

and automatic counting as two independent supports remains forbidden.

## 5. Candidate independence vocabulary

```text
unresolved
dependent
partially_independent
independent
```

The initial state for both links is `unresolved`.

A later review must compare at least:

```text
authors
institutions/labs
samples/specimens
datasets
experimental systems
analysis pipelines
direct source lineage
declared coordination/cross-dependence
```

Missing data remains `unresolved`; it is not evidence of independence.

## 6. Source lineage

`source_lineage_edges` is reserved for explicit provenance/derivation
relationships.

Authorship overlap alone must **not** create a lineage edge.

The actual frozen `SourceLineageEdgesRow` contract is:

```text
id
parent_source_id
child_source_id
relation
basis_claim_id
basis_evidence_json
review_status
created_at
```

RATE-2M R2 uses this exact contract. The failed R1 harness assumption
`edge_type / lineage_metadata_json` is explicitly discarded.

## 7. Persistence boundary

RATE-2M is design-only:

```text
evidence_assessments inserted       = 0
source_lineage_edges inserted       = 0
knowledge_syntheses inserted        = 0
ProcessScientificSupportV1          = false
real V6 write                       = false
numeric RateModel                   = false
remote write                        = false
```

## 8. Next gate

```text
RATE-2N — Primary Source Evidence Assessment Candidate Extraction
```

RATE-2N should inspect the exact primary-source methods/results needed for the
two link-specific assessments and produce assessment candidates while leaving
`independence_status=unresolved` unless the origin-separation evidence is
actually sufficient.
