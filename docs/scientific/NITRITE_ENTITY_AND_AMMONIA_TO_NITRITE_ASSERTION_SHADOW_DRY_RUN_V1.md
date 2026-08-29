# EcoBiome — Nitrite Entity + Ammonia-to-Nitrite Assertion Shadow Dry-Run V1

Status: PASS on disposable shadow
Gate: RATE-2F-B

Dry-run payload SHA-256:

```text
63c8a446020a951d850801827af93919037c788c259bbb0ec0056bcd360ecb2e
```

Nitrite identity human-review decision SHA-256:

```text
dbfe7412571fd289e960e9b1b46db837973fc707473b6caa42ef9ff5405f1eca
```

## 1. Human decision recorded

The human user explicitly supplied:

```text
accept
```

for the RATE-2F-A nitrite identity candidate.

The accepted identity is:

```text
entity-pubchem-cid-946
chemical_species
nitrite
NO2-
PubChem CID 946
```

The real Scientific Foundation V6 is still not authorized for mutation.

## 2. Shadow entity seed

RATE-2F-B created on the disposable copy only:

```text
authority source      +1
scientific entity     +1
entity revision       +1
entity identifier     +1
```

The shadow entity revision and identifier are `reviewed_confirmed` because the
identity itself received an explicit human acceptance before this gate.

## 3. Corrected mechanism assertion

The shadow assertion is:

```text
assertion-g7a-nitrogen-oxidation-ammonia-to-nitrite-v1
revision 1
predicate = nitrogen_oxidized_from_to
```

Participants:

```text
source_material = entity-pubchem-cid-222@1   # ammonia / NH3
target_material = entity-pubchem-cid-946@1   # nitrite / NO2-
```

No `process_agent` is included.

This deliberately avoids inheriting `Candidatus Nitrospira inopinata` from the
older organism-specific ammonium-to-nitrate assertion.

Qualifier:

```json
{"semantic_type":"nitrogen_oxidation"}
```

Canonical assertion SHA-256:

```text
907c862992a0d11f50d8f4ccab3b123902e5330bc8066caa977b64b133fd7b96
```

## 4. Shadow transaction proof

Exact table deltas:

```text
knowledge_sources                 +1
scientific_entities               +1
scientific_entity_revisions       +1
scientific_entity_identifiers     +1
scientific_assertions             +1
scientific_assertion_revisions    +1
assertion_claim_links              0
```

SQLite validation after commit:

```text
quick_check        = ok
foreign_key_check = 0 violations
```

## 5. Real V6 proof

Real V6 SHA before and after the entire gate:

```text
76381b5a76f0dd34668634357b3fa4657ff650351235ad85acc8b6fdb421997f
```

Therefore:

```text
real V6 write authorized = false
real V6 written          = false
```

## 6. Evidence provenance remains blocked

Presence of RATE-2B primary Nature sources in current real V6:

```text
10.1038/nature16459 : 0
10.1038/nature16461 : 0
```

RATE-2F-B creates no `assertion_claim_link`.

The mechanism assertion now has a validated persistence shape, but real
scientific provenance still needs a dedicated source/claim ingestion and review
path.

## 7. Kinetic boundary

This shadow PASS does not authorize:

```text
kinetic_form
kinetic_parameter
RateModel
rate integration
Δt
```

## 8. Next gate

```text
RATE-2G — Mechanism Primary Evidence Ingestion Design
```
