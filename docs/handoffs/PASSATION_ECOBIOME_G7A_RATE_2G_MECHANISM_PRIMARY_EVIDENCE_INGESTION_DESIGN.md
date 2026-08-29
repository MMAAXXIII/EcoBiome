# PASSATION — EcoBiome G7A RATE-2G — Mechanism Primary Evidence Ingestion Design

Gate:
`ECOBIOME_G7A_RATE_2G_MECHANISM_PRIMARY_EVIDENCE_INGESTION_DESIGN_LOCAL`

Expected precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@f87f7d9c8e1220b4227dcc0b137e803c6352a17d`

## RATE-2F-B frozen

Shadow assertion:

```text
assertion-g7a-nitrogen-oxidation-ammonia-to-nitrite-v1@1
SHA 907c862992a0d11f50d8f4ccab3b123902e5330bc8066caa977b64b133fd7b96
```

Real V6 remains unchanged.

## RATE-2G plan identity

```text
0e34424f7164e7ffa4f66a69f05415965cf1856e2bce05dacde5ae9538199aba
```

## Primary sources

```text
van Kessel et al. 2015
DOI   10.1038/nature16459
PMID  26610025
PMCID PMC4878690

Daims et al. 2015
DOI   10.1038/nature16461
PMID  26610024
PMCID PMC5152751
```

Canonical source identity uses DOI.
Acquisition representation uses PMC.

## Required review boundary

Claims may be acquired and linked to exact source evidence, but they remain:

```text
pending_human_review
```

until an explicit claim-review gate.

No `assertion_claim_link` is created before that review.

## Independence boundary

Distinct DOI does not imply independent origin.

The two studies share Mads Albertsen and Per H. Nielsen, so independence must
be assessed rather than assumed.

## Storage boundary

```text
full article in Git = false
external CAS only   = true
license assessment  = required
```

## Persistence boundary

RATE-2G performs:

```text
Scientific Foundation V6 write = false
source ingestion                = false
claim insertion                 = false
assertion link                  = false
source-code change              = false
remote write                    = false
```

## Next gate

`RATE-2H — Primary Evidence Shadow Acquisition + Claim Package`
