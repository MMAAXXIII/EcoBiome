# EcoBiome — Nitrite Entity Identity Candidate V1

Status: candidate ready for human review
Gate: RATE-2F-A
Persistence status: no Scientific Foundation V6 write

Candidate payload SHA-256:

```text
4fe7808c45aecafbe6ecd09d4590aff6d5b0d965b5a795502020ed49220e129f
```

## 1. Why RATE-2F stopped

The frozen V6 oxidation assertion contains three participants:

```text
process_agent  = Candidatus Nitrospira inopinata
source_material = ammonium
target_material = nitrate
```

RATE-2F R1 incorrectly expected exactly two participants.

That harness assumption is rejected.

The process-agent participant must **not** simply be copied to the new
ammonia-to-nitrite assertion because RATE-2B explicitly adopted a
process-level, non-organism-exclusive mechanism claim.

## 2. Deeper V6 blocker

Current Scientific Foundation V6 contains reviewed entities for:

```text
ammonia   — PubChem CID 222
ammonium  — PubChem CID 223
nitrate   — PubChem CID 943
```

but no reviewed `nitrite` entity.

Therefore the new assertion cannot yet receive a valid target
`ScientificEntityRef`.

## 3. Proposed nitrite identity

Authority:

```text
PubChem Compound
CID 946
```

Proposed EcoBiome identity:

```text
entity_id       = entity-pubchem-cid-946
entity_kind     = chemical_species
canonical_label = nitrite
formula         = NO2-
```

Authority source candidate:

```text
authority-source-pubchem-cid-946
https://pubchem.ncbi.nlm.nih.gov/compound/946
```

## 4. Human-review boundary

RATE-2F-A does **not** mark this entity as:

```text
reviewed_confirmed
```

The candidate remains:

```text
mapping_review_status = pending_human_review
review_status         = pending_human_review
```

An explicit human `accept`, `reject`, or `revise` decision is required before a
shadow seed may use `reviewed_confirmed`.

## 5. Source semantics correction for future RATE-2F

The accepted RATE-2C bridge states that reactive AMO substrate semantics are
associated with ammonia/NH3.

V6 already contains:

```text
entity-pubchem-cid-222
ammonia
NH3
reviewed_confirmed
```

The future mechanism assertion dry-run should therefore use ammonia CID 222 as
the scientific source participant.

It should **not** silently reuse ammonium CID 223 merely because the historical
one-step template did.

## 6. Qualifier correction

The frozen oxidation template contains the generic qualifier:

```json
{"semantic_type":"nitrogen_oxidation"}
```

RATE-2F R1 incorrectly assumed empty qualifiers.

A corrected future assertion may preserve this generic semantic qualifier
because it describes the assertion type rather than an organism-exclusive
scope.

## 7. Evidence graph remains separate

The current V6 source graph does not yet contain the two RATE-2B Nature
articles:

```text
10.1038/nature16459
10.1038/nature16461
```

This does not block identity review for nitrite.

It does mean that future real assertion promotion still needs an evidence
ingestion/link review gate before scientific provenance is complete.

## 8. RATE-2F-A verdict

```text
nitrite_identity_candidate_materialized = true
human_review_completed                  = false
reviewed_confirmed                      = false

real V6 write                           = false
mechanism assertion created             = false
assertion-claim links created           = false
numeric RateModel authorized            = false
```

Next step requires an explicit human decision on the nitrite identity.
