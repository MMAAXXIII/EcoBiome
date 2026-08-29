# EcoBiome — Primary Evidence Assessment Candidates V1

Status: pending human review
Gate: RATE-2N

Candidate package SHA-256:

```text
50f86f92a0a0d11dec238679d96c7c72444c7af7e39306981592b639b98abcd0
```

## 1. van Kessel et al. 2015

```text
DOI: 10.1038/nature16459
study_design:
experimental_enrichment_culture_multimodal

evidence_directness:
direct_functional_support_with_intermediate_inference

independence_status:
unresolved
```

Assessment basis includes replicated enrichment/batch physiology, isotope
tracing, chemical nitrogen measurements, metagenomics, AMO labelling and
FISH-MAR.

Important limitation: the main aerobic ammonium-to-nitrate batch experiment
did not accumulate detectable nitrite. Support for the ammonia-to-nitrite
intermediate therefore combines isotope evidence and mechanistic localization
rather than relying on transient bulk nitrite accumulation alone.

## 2. Daims et al. 2015

```text
DOI: 10.1038/nature16461
study_design:
experimental_enrichment_culture_multimodal

evidence_directness:
direct_functional_support

independence_status:
unresolved
```

This candidate has direct functional support from replicated ammonium
incubations with transient nitrite accumulation, complemented by qPCR,
metaproteomics and a separately isolated non-nitrifying betaproteobacterial
control.

## 3. Pairwise origin assessment candidate

Proposed status:

```text
partially_independent
```

Why it is not automatically `independent`:

```text
shared authors
partial Aalborg institutional/analytical overlap
cross-reference between the concurrent studies
```

Why it is not classified `dependent`:

```text
different environmental samples
different enrichment systems
different temperature regimes
different target Nitrospira populations
no shared primary experimental dataset identified
no direct sample/data lineage identified
```

Therefore `partially_independent` is a **candidate**, not a completed decision.

```text
independent_support_origin_count = null
```

## 4. Copyright and provenance boundary

Full article XML and verbatim paragraphs are not committed to Git and are not
included in the RATE-2N bundle.

The package retains only article identities, retrieval SHA-256 values and
cryptographic bindings to the source paragraphs used during extraction.

## 5. Persistence boundary

```text
evidence_assessments inserted = 0
source_lineage_edges inserted = 0
knowledge_syntheses inserted  = 0
real V6 write                 = false
ProcessScientificSupportV1    = false
numeric RateModel             = false
```

## 6. Next gate

```text
RATE-2O — Evidence Assessment + Independence Human Review
```

The two EvidenceAssessment candidates and the pairwise
`partially_independent` proposal require explicit human review.
