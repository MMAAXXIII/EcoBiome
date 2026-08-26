# EcoBiome — Primary Mechanism Evidence Shadow Acquisition V1

Status: shadow acquisition PASS
Gate: RATE-2H

Result payload SHA-256:

```text
e4827356c9c2504714876af5c2c44e0b8b6632f1cda81116d21fe0e980777c0b
```

Claim review package SHA-256:

```text
69a8d89758a650ce4eaa33dbf812a7ad769a94852498068a1312e535ed94fa70
```

## 1. What RATE-2H proved

Both RATE-2B primary sources were acquired through a deterministic PMC XML
retrieval path and persisted into a disposable Scientific Foundation V6 copy.

The real V6 remained byte-for-byte unchanged:

```text
76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
```

No restricted full text or evidence sentence is committed to Git or included
in the RATE-2H bundle.

## 2. Shadow graph deltas

```text
knowledge_sources      +2
acquisition_jobs       +2
retrievals              +2
raw_artifacts           +2
representations         +2
segments                +2
source_evidence         +2
source_claims           +2
claim_evidence_links    +2
source_assessments      +2

claim_review_events      0
assertion_claim_links    0
```

SQLite post-write:

```text
quick_check        = ok
foreign_key_check = 0 violations
```

## 3. van Kessel et al. claim candidate

```text
DOI   : 10.1038/nature16459
PMCID : PMC4878690
claim : Nitrification includes an ammonia/ammonium oxidation step that produces nitrite before nitrite is oxidized to nitrate.
```

Evidence is cryptographically bound to the acquired representation.

Short anchor retained for review:

```text
Nitrification is a two-step process
```

Evidence SHA-256:

```text
ac8ba171582a37a611c119702345a1cd9cf1645977234c82900a4b0baf12ff1f
```

The full verbatim evidence sentence remains only inside the disposable
shadow/CAS environment and is intentionally excluded from repository artifacts.

## 4. Daims et al. claim candidate

```text
DOI   : 10.1038/nature16461
PMCID : PMC5152751
claim : Nitrification proceeds through ammonia oxidation involving nitrite before the subsequent nitrate state.
```

Short anchor:

```text
oxidation of ammonia via nitrite to nitrate
```

Evidence SHA-256:

```text
6dd08e05dd4c8f400651fe422c5a162625da0eb52cc25315611d181bdf041b9b
```

## 5. Physical Schema V6 correction

RATE-2G used `source_statement` as a conceptual claim-layer label.

The actual frozen V6 schema permits only:

```text
extracted
atomic
```

RATE-2H therefore persists the two paraphrased mechanism claims as:

```text
claim_layer = atomic
```

and records the RATE-2G conceptual layer in claim qualifiers for traceability.

No schema mutation was needed.

## 6. Human-review boundary

Both claims remain:

```text
pending_human_review
```

There are deliberately no `claim_review_events`.

Consequently there are also no:

```text
assertion_claim_links
evidence_assessments
knowledge_syntheses
ProcessScientificSupportV1
```

A technical shadow PASS cannot substitute for scientific claim review.

## 7. Independence boundary

The two studies have distinct DOI records but share authors including:

```text
Mads Albertsen
Per H. Nielsen
```

RATE-2H therefore records no independent-origin count.

That question belongs to a later evidence assessment.

## 8. Next gate

```text
RATE-2I — Primary Evidence Human Claim Review
```

RATE-2I requires explicit human decisions for both claims:

```text
accept
correct
reject
```
