# EcoBiome — Ammonia-to-Nitrite Mechanism Evidence Candidate Package V1

Status: candidate ready for human review
Gate: RATE-2B
Persistence status: NOT part of Scientific Foundation V6

Candidate payload SHA-256:

```text
0b7f444bf34becee4967e42b91b87758aeb1780befac57a74b6b325d7522f15d
```

## 1. Purpose

RATE-2B materializes the mechanism evidence candidate anticipated by RATE-2A.

It does not create a reviewed assertion and does not create a
`ProcessScientificSupportV1`.

The candidate is intentionally split into two questions:

```text
scientific mechanism:
  ammonia/ammonium nitrogen -> nitrite nitrogen

software process:
  total_ammonia_nitrogen -> nitrite_nitrogen
```

The first is strongly supported by the selected primary literature.

The second still requires a reviewed semantic bridge because
`total_ammonia_nitrogen` is an analytical/model aggregate rather than the
literal chemical wording used by the mechanism papers.

## 2. Proposed mechanism assertion

Candidate identifier:

```text
assertion-g7a-nitrogen-oxidation-ammonia-to-nitrite-v1
```

Candidate predicate:

```text
nitrogen_oxidized_from_to
```

Proposed claim:

```text
During aerobic nitrification, ammonia/ammonium nitrogen can be oxidized to
nitrite nitrogen as the first oxidation step.
```

The candidate deliberately does not specify an exclusive organism or microbial
guild.

It contains no kinetic form, rate, duration or environmental response.

## 3. Primary source A

Maartje A. H. J. van Kessel et al. (2015).

"Complete nitrification by a single microorganism."

Nature 528, 555–559.

```text
DOI  : 10.1038/nature16459
PMID : 26610025
PMC  : PMC4878690
```

Source:
https://doi.org/10.1038/nature16459

The paper's abstract describes canonical nitrification as a two-step process
where ammonia is first oxidized to nitrite and nitrite is subsequently oxidized
to nitrate.

The study then reports Nitrospira capable of complete ammonium oxidation via
nitrite to nitrate.

RATE-2B uses this as primary process-direction evidence only.

## 4. Independent primary source B

Holger Daims et al. (2015).

"Complete nitrification by Nitrospira bacteria."

Nature 528, 504–509.

```text
DOI  : 10.1038/nature16461
PMID : 26610024
PMC  : PMC5152751
```

Source:
https://doi.org/10.1038/nature16461

The paper independently describes nitrification as oxidation of ammonia via
nitrite to nitrate and reports a completely nitrifying Nitrospira with both
ammonia- and nitrite-oxidation pathways.

This independent source reduces dependence on a single publication for the
directional mechanism claim.

## 5. What the two papers support

Together they support the candidate proposition:

```text
ammonia/ammonium nitrogen
          |
          | aerobic nitrification first oxidation step
          v
nitrite nitrogen
```

For RATE-2B this is a mechanism statement.

It does not imply:

```text
a universal rate
a Monod form
a first-order coefficient
a temperature correction
a pH correction
a hydraulic correction
an exclusive microbial guild
```

## 6. Why ProcessScientificSupport is still blocked

RATE-1F uses:

```text
source_component_id = total_ammonia_nitrogen
target_component_id = nitrite_nitrogen
```

The target alignment is direct at the present semantic level.

The source requires more care.

RATE-1D defines TAN-N as the analytical/model total:

```text
TAN-N = NH3-N + NH4+-N
```

but the primary mechanism sources discuss ammonia/ammonium oxidation rather
than a software-level TAN inventory.

Therefore RATE-2B records:

```text
process_scientific_support_attachable = false
blocker = pending TAN-N -> ammonia/ammonium semantic bridge review
```

This is deliberately stricter than attaching a support object solely because
the words appear related.

## 7. Future evaluation scope candidate

If the semantic bridge is later accepted, the candidate process alignment is:

```text
process_id      = ammonia_oxidation_to_nitrite_extent_v1
process_version = 1
role            = mechanism

required parameter bindings:
  /source_component_id = total_ammonia_nitrogen
  /target_component_id = nitrite_nitrogen
```

Candidate alignment class:

```text
direct_mechanism_support
```

Candidate epistemic class:

```text
explicit_causal_result
```

These values are **not reviewed support yet**.

## 8. No collision with RATE-2A kinetic evidence

The Mnyoro 2021 first-order coefficient is deliberately absent from this
candidate package.

RATE-2B does not attempt to resolve:

```text
0.45 m/h versus 0.45 m/d
```

and does not authorize a numerical RateModel.

Mechanism evidence and kinetic evidence remain independent review tracks.

## 9. Human review checklist

Before assertion promotion:

1. verify both source records and DOI lineage;
2. review the claim wording against the primary sources;
3. verify subject/object entity semantics and elemental-N basis;
4. decide whether the claim is appropriately classified as
   `explicit_causal_result`;
5. record reviewer identity and review artifact identity.

Before process-support attachment, additionally:

1. review the TAN-N analytical-pool semantic bridge;
2. verify the exact RATE-1F parameter bindings;
3. construct and validate the exact evaluation scope;
4. run the scientific alignment policy without increasing epistemic strength.

## 10. RATE-2B verdict

```text
mechanism_assertion_candidate_materialized = true
two_independent_primary_sources = true
human_review_completed = false
scientific_foundation_write = false
process_scientific_support_attachable = false
semantic_bridge_review_required = true
numeric_rate_model_authorized = false
```

Recommended next gate:

```text
RATE-2C — TAN-to-Ammonia Mechanism Semantic Bridge Candidate
```
