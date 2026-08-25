# EcoBiome — Ammonia-to-Nitrite Mechanism Alignment Review Package V1

Status: pending human review
Gate: RATE-2D
Persistence status: no Scientific Foundation write

Review payload SHA-256:

```text
4460d608d544cad1555ee8cd79ee3c6f09aa2f0c5fea5b2e0eb99c504f7ea602
```

Exact evaluation-scope SHA-256:

```text
72cc77fa3ccec09b16b99f00fa999be94df637e72490d2832e985486cd54a7de
```

## 1. Purpose

RATE-2D assembles the complete review surface needed to decide whether the
RATE-2B mechanism evidence and RATE-2C TAN semantic bridge may support the
RATE-1F process:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
```

It does not perform that human review.

It does not create `ProcessScientificSupportV1`.

## 2. Evidence chain under review

### Mechanism candidate

```text
candidate-g7a-ammonia-to-nitrite-mechanism-v1

payload SHA:
0b7f444bf34becee4967e42b91b87758aeb1780befac57a74b6b325d7522f15d
```

The candidate is backed by two independent 2015 Nature primary studies and
supports the directional first nitrification step.

### TAN semantic bridge candidate

```text
candidate-g7a-tan-to-ammonia-mechanism-semantic-bridge-v1

payload SHA:
cbed8df87f5493284c72351705c1236970d6cd9fecbbf10baa422149e11c7572
```

Bridge kind:

```text
reservoir_to_reactive_species_accounting
```

The bridge explicitly refuses:

```text
TAN-N == NH3-N
TAN-N == NH4+-N
```

## 3. Process identity under review

```text
process_id      = ammonia_oxidation_to_nitrite_extent_v1
process_version = 1

process definition canonical SHA:
fb34a9f83decc88d1b66ed1d1c806c769c851d5604bd9201b5a8c66bbfc4b2e5
```

Required scientific role:

```text
mechanism
```

## 4. Exact evaluation scope

The candidate scope is equivalent to
`ProcessScientificEvaluationScopeV1` with:

```text
process_id      = ammonia_oxidation_to_nitrite_extent_v1
process_version = 1
role            = mechanism
match mode      = contains_exact_required
```

Required parameter bindings:

```text
/source_component_id = "total_ammonia_nitrogen"
/target_component_id = "nitrite_nitrogen"
```

Canonical scope SHA:

```text
72cc77fa3ccec09b16b99f00fa999be94df637e72490d2832e985486cd54a7de
```

RATE-2D verifies this SHA against the live EcoBiome
`ProcessScientificEvaluationScopeV1` implementation.

## 5. Proposed alignment strength

The review package proposes:

```text
alignment_class = interpretive_mechanism_support
epistemic_class = interpretive_support
```

not:

```text
direct_mechanism_support
explicit_causal_result
```

Reason:

```text
scientific evidence acts at reactive-species mechanism level
EcoBiome source state is an aggregate TAN-N reservoir
```

The mapping is scientifically motivated but still a model interpretation.

## 6. Human review template

The package contains a deterministic decision template initialized to:

```text
decision    = pending
reviewer    = null
review time = null
rationale   = null
review SHA  = null
```

Allowed future decisions:

```text
accept
reject
revise
```

An acceptance is not valid unless every required review check is explicitly
true.

## 7. Required acceptance checks

A human reviewer must verify all of the following:

```text
mechanism source lineage
mechanism claim wording
TAN-N semantics
NH3 substrate semantics
reservoir-accounting interpretation
interpretive alignment classification
exact process evaluation scope
absence of kinetic epistemic-strength increase
```

RATE-2D itself marks all checks false.

## 8. Why support still cannot be materialized

Even a future accepted alignment decision is not sufficient by itself to build
`ProcessScientificSupportV1`.

That object requires an exact persisted:

```text
ScientificAssertionRefV1
```

containing:

```text
assertion_id
assertion_revision
canonical_payload_sha256
```

The RATE-2B mechanism assertion remains a candidate and is not persisted in
Scientific Foundation V6.

Therefore RATE-2D freezes:

```text
process_scientific_support_attachable_now = false
```

## 9. Kinetic boundary unchanged

This review package is mechanism-only.

It does not review:

```text
kinetic_form
kinetic_parameter
applicability_domain for a RateModel
```

The Mnyoro coefficient conflict remains unresolved.

Therefore:

```text
numeric_rate_model_authorized = false
```

regardless of any future mechanism-alignment acceptance.

## 10. Persistence boundary

RATE-2D performs:

```text
source-code change              = false
Scientific Foundation V6 write = false
assertion insertion             = false
review insertion                = false
ProcessScientificSupport write  = false
remote write                    = false
```

## 11. RATE-2D verdict

Before human review:

```text
review_package_materialized = true
human_review_decision       = pending
all_acceptance_checks       = false
support_attachable          = false
numeric_rate_model          = false
```

Next step requires an explicit human review decision.

Recommended next gate after that explicit decision:

```text
RATE-2E — Mechanism Alignment Human Review Decision
```
