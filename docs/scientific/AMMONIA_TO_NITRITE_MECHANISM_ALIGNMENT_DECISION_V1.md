# EcoBiome — Ammonia-to-Nitrite Mechanism Alignment Human Review Decision V1

Status: accepted
Gate: RATE-2E
Persistence status: no Scientific Foundation V6 write

Decision payload SHA-256:

```text
aec4200eff9a7ef672b788479a516623285a2e5174e9fc0b00972fc40f9f952e
```

## 1. Explicit human decision

The human user explicitly supplied:

```text
accept
```

RATE-2E records that decision as an immutable review event.

It does not infer acceptance from RATE-2D's technical PASS.

Recorded review time:

```text
2026-08-26T00:36:46+02:00
```

Reviewer identity is deliberately non-identifying:

```text
human_user_current_conversation
```

## 2. Reviewed RATE-2D package

```text
review package:
review-g7a-ammonia-to-nitrite-mechanism-alignment-v1

review payload SHA:
4460d608d544cad1555ee8cd79ee3c6f09aa2f0c5fea5b2e0eb99c504f7ea602

review file SHA:
65bbdfe37cb84db600ba70da6d7c4f61d67a8946da22e1f241ba7ed7d5c05bd6
```

RATE-2D's original pending package remains unchanged.

RATE-2E adds a separate decision artifact rather than rewriting history.

## 3. Accepted mechanism candidate

```text
candidate-g7a-ammonia-to-nitrite-mechanism-v1

payload SHA:
0b7f444bf34becee4967e42b91b87758aeb1780befac57a74b6b325d7522f15d
```

The accepted claim remains mechanism-only.

No kinetic form, parameter or environmental response is promoted by this
decision.

## 4. Accepted TAN semantic bridge

```text
candidate-g7a-tan-to-ammonia-mechanism-semantic-bridge-v1

payload SHA:
cbed8df87f5493284c72351705c1236970d6cd9fecbbf10baa422149e11c7572
```

The accepted bridge remains:

```text
reservoir_to_reactive_species_accounting
```

and still rejects:

```text
TAN-N == NH3-N
TAN-N == NH4+-N
```

## 5. Accepted alignment strength

The human review accepts exactly:

```text
role            = mechanism
alignment_class = interpretive_mechanism_support
epistemic_class = interpretive_support
```

It does **not** upgrade the evidence to:

```text
direct_mechanism_support
explicit_causal_result
```

## 6. Accepted evaluation scope

```text
process_id      = ammonia_oxidation_to_nitrite_extent_v1
process_version = 1

/source_component_id = "total_ammonia_nitrogen"
/target_component_id = "nitrite_nitrogen"
```

Process-definition SHA:

```text
fb34a9f83decc88d1b66ed1d1c806c769c851d5604bd9201b5a8c66bbfc4b2e5
```

Evaluation-scope SHA:

```text
72cc77fa3ccec09b16b99f00fa999be94df637e72490d2832e985486cd54a7de
```

## 7. Human acceptance checks

All eight RATE-2D checks are now explicitly accepted:

```text
mechanism_source_lineage_verified        = true
mechanism_claim_wording_verified         = true
tan_semantics_verified                   = true
nh3_substrate_semantics_verified         = true
reservoir_accounting_bridge_verified     = true
interpretive_alignment_class_verified    = true
evaluation_scope_verified                = true
no_kinetic_strength_increase_verified    = true
```

This is the semantic meaning of the explicit `accept` response requested by
RATE-2D.

## 8. What acceptance now permits

RATE-2E establishes:

```text
mechanism_alignment_accepted = true
mechanism_assertion_candidate_accepted_for_promotion = true
semantic_bridge_candidate_accepted_for_promotion = true
evaluation_scope_accepted = true
```

This means the scientific package may advance to a persistence-preparation
gate.

## 9. What acceptance still does NOT permit

`ProcessScientificSupportV1` cannot yet be materialized because an exact
persisted `ScientificAssertionRefV1` does not yet exist for the new mechanism
assertion.

The alignment-policy identity must also be frozen before support
materialization.

Therefore:

```text
process_scientific_support_attachable_now = false
```

## 10. No V6 write authorization

The human decision is an acceptance of the scientific alignment review.

It is **not** authorization to mutate Scientific Foundation V6.

RATE-2E therefore freezes:

```text
Scientific Foundation V6 write authorized = false
Scientific Foundation V6 written          = false
assertion inserted                         = false
review inserted                            = false
```

A separate explicit authorization is required before any V6 mutation.

## 11. Kinetic boundary unchanged

RATE-2E does not review or authorize:

```text
kinetic_form
kinetic_parameter
RateModel
rate -> extent integration
Δt
```

The Mnyoro `0.45` source-unit conflict remains unresolved.

Therefore:

```text
numeric_rate_model_authorized = false
```

## 12. RATE-2E verdict

```text
human_review_completed = true
decision               = accept

alignment:
  interpretive_mechanism_support
  interpretive_support

mechanism alignment accepted = true

Scientific Foundation V6 write = false
ProcessScientificSupport materialized = false
numeric RateModel authorized = false
```

Recommended next gate:

```text
RATE-2F — Mechanism Assertion Persistence Dry-Run
```

RATE-2F should construct the exact proposed V6 assertion/revision/review
transaction and verify it against a disposable copy or shadow database, while
leaving the real Scientific Foundation V6 byte-for-byte unchanged.
