# PASSATION — EcoBiome G7A RATE-2H — Primary Evidence Shadow Acquisition + Claim Package

Gate:
`ECOBIOME_G7A_RATE_2H_PRIMARY_EVIDENCE_SHADOW_ACQUISITION_AND_CLAIM_PACKAGE_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@6efe4fa8e6ef08e95dee3cd2147338b7845239ef`

## Result

```text
shadow acquisition = PASS
real V6 write       = false
```

Result SHA:

```text
e4827356c9c2504714876af5c2c44e0b8b6632f1cda81116d21fe0e980777c0b
```

Claim review package SHA:

```text
69a8d89758a650ce4eaa33dbf812a7ad769a94852498068a1312e535ed94fa70
```

## Shadow persistence

Two complete provenance chains were written on the disposable copy through:

```text
knowledge_source
acquisition_job
retrieval
raw_artifact
representation
segment
source_evidence
source_claim
claim_evidence_link
source_assessment
```

No claim review or assertion link was generated.

## Claims awaiting human review

van Kessel 2015:

```text
Nitrification includes an ammonia/ammonium oxidation step that produces nitrite before nitrite is oxidized to nitrate.
```

Daims 2015:

```text
Nitrification proceeds through ammonia oxidation involving nitrite before the subsequent nitrate state.
```

## Copyright/storage boundary

Full XML, normalized full text and verbatim evidence are external-CAS/shadow
only and are excluded from Git and the handoff bundle.

## Schema correction

Physical V6:

```text
claim_layer = atomic
```

RATE-2G `source_statement` remains recorded only as conceptual provenance.

## Next gate

`RATE-2I — Primary Evidence Human Claim Review`

Do not create assertion support links until both individual claim decisions are
explicitly recorded.
