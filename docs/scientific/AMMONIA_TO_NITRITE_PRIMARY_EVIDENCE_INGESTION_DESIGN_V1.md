# EcoBiome — Ammonia-to-Nitrite Primary Evidence Ingestion Design V1

Status: design ready
Gate: RATE-2G
Scientific Foundation V6 write: forbidden

Plan payload SHA-256:

```text
0e34424f7164e7ffa4f66a69f05415965cf1856e2bce05dacde5ae9538199aba
```

## 1. Starting point

RATE-2F-B proved on a disposable V6 copy that EcoBiome can persist:

```text
entity-pubchem-cid-946@1            # nitrite
assertion-g7a-nitrogen-oxidation-ammonia-to-nitrite-v1@1
```

with assertion SHA:

```text
907c862992a0d11f50d8f4ccab3b123902e5330bc8066caa977b64b133fd7b96
```

The real V6 still contains neither object.

The remaining scientific-provenance gap is the primary evidence graph.

## 2. Primary source 1 — van Kessel et al. 2015

```text
Title : Complete nitrification by a single microorganism
Nature 528, 555–559
DOI   : 10.1038/nature16459
PMID  : 26610025
PMCID : PMC4878690
```

Canonical source identity:

```text
https://doi.org/10.1038/nature16459
```

Preferred acquisition representation:

```text
PubMed Central author manuscript
https://pmc.ncbi.nlm.nih.gov/articles/PMC4878690/
```

Candidate claim, deliberately paraphrased:

```text
Nitrification includes an ammonia/ammonium oxidation step that produces
nitrite before nitrite is oxidized to nitrate.
```

Short evidence anchor:

```text
Nitrification is a two-step process
```

The ingestion gate must resolve an exact source span around this anchor,
persist exact offsets and SHA-256, and never substitute a model-generated
excerpt.

## 3. Primary source 2 — Daims et al. 2015

```text
Title : Complete nitrification by Nitrospira bacteria
Nature 528, 504–509
DOI   : 10.1038/nature16461
PMID  : 26610024
PMCID : PMC5152751
```

Canonical source identity:

```text
https://doi.org/10.1038/nature16461
```

Preferred acquisition representation:

```text
PubMed Central author manuscript
https://pmc.ncbi.nlm.nih.gov/articles/PMC5152751/
```

Candidate claim, deliberately paraphrased:

```text
Nitrification proceeds through ammonia oxidation involving nitrite before
the subsequent nitrate state.
```

Short evidence anchor:

```text
oxidation of ammonia via nitrite to nitrate
```

Again, exact offsets and evidence SHA must be obtained from the acquired
representation.

## 4. Publication identity versus retrieval identity

EcoBiome must not conflate:

```text
scientific publication identity
```

with:

```text
retrieval representation
```

Therefore:

```text
knowledge_sources.canonical_locator = DOI
retrieval requested/resolved locator = PMC representation
```

This lets a future representation change without changing the scientific
source identity.

## 5. Required V6 graph

The future ingestion path must explicitly traverse:

```text
knowledge_sources
  -> acquisition_jobs
  -> retrievals
  -> raw_artifacts
  -> representations
  -> segments
  -> source_evidence
  -> source_claims
  -> claim_evidence_links
  -> source_assessments
  -> claim_review_events
```

Only after a claim receives explicit human review may the pipeline consider:

```text
assertion_claim_links
evidence_assessments
knowledge_syntheses
ProcessScientificSupportV1
```

## 6. Why assertion links are deferred

`AssertionClaimLinksRow` support links require resolved values for:

```text
support_mode
scope_alignment
semantic_alignment
```

The persistence validator rejects an unresolved supporting semantic/scope
alignment.

RATE-2G therefore does **not** pre-create a support link and does not use a
technical ingestion PASS as a scientific acceptance.

## 7. Source independence is not automatic

The two DOI records represent distinct primary studies, but they share at
least these authors:

```text
Mads Albertsen
Per H. Nielsen
```

Therefore EcoBiome must not automatically infer:

```text
independent_support_origin_count = 2
```

The independence relation requires a dedicated assessment considering study
samples, laboratories, datasets, authorship overlap and methodological
dependence.

## 8. Copyright / storage policy

The PMC records expose Nature author manuscripts under conditions that permit
academic-research use and text/data mining subject to the stated terms.

RATE-2G therefore requires:

```text
full source text in Git repository = false
raw/full representation            = external CAS only
license evidence locator           = mandatory
license assessment                  = mandatory
```

Repository documents may retain metadata, hashes, short anchors, human review
events and paraphrased claims, but not duplicate the full articles.

## 9. No kinetic promotion

These papers are used here for the **mechanism** evidence chain only.

RATE-2G does not promote:

```text
kinetic_form
kinetic_parameter
RateModel
Mnyoro coefficient
Δt integration
```

## 10. Next gate

```text
RATE-2H — Primary Evidence Shadow Acquisition + Claim Package
```

RATE-2H should acquire the two PMC representations into a disposable external
CAS + shadow V6, resolve exact evidence spans, construct source claims, and
stop with those claims still pending human review.
