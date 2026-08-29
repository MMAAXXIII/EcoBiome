# PASSATION ECOBIOME — G7A RATE-5L / RATE-5L-R1

## Dormant nitrite zero-order evidence candidate implementation V1

**Gate initial:** `RATE-5L_DORMANT_NITRITE_ZERO_ORDER_EVIDENCE_CANDIDATE_IMPLEMENTATION_V1`  
**Correction gate:** `RATE-5L-R1_SCIENTIFIC_CONTEXT_IDENTITY_AND_KINETIC_ASSAY_SCOPE_CORRECTION`  
**Base:** `main@a6931417bb02644157bac27a159a6dad4da060e1`  
**Branch:** `agent/g7a-rate-5l-nitrite-zero-order-evidence-candidate-v1`  
**Status:** `R1_IMPLEMENTED_PENDING_RATE_5M_REAUDIT`

## 1. Purpose

RATE-5L preserves a bounded second-stage nitrification evidence candidate for
`nitrite_oxidation_to_nitrate` without promoting it to an executable
`RateModelV1`.

The exact zero-order nitrite constant is retained as evidence only:

- value: `139`
- unit: `g NO2-N/m3-media/d`
- basis: media volume
- kinetic order: zero order

No ecosystem rate is calculated and no state is mutated.

RATE-5L-R1 corrects two merge-readiness blockers identified by RATE-5M:

1. the scientific evidence context is now identity-bearing in the candidate
   canonical payload;
2. temperature, dissolved oxygen, pH, and alkalinity from experiment 1 are no
   longer used as kinetic-assay applicability guards.

## 2. Source identities

### Exact numeric source

Associated SSRN preprint:

- SSRN id: `4911049`
- local reviewed artifact: `ssrn-4911049.pdf`
- SHA-256: `2e9af660d0121c9ace5ec469716400458b4994062f7a3ce97a10589e008063e8`
- peer reviewed: `false`
- exact parameter observed: `true`

The preprint reports zero-order nitrite kinetics of `139, 391, 458, and 479
g/m3/d` for plastic beads, ceramic beads, coconut shells, and polyurethane
foam, respectively. Its methods define zero-order kinetics from concentration
values above `1.0 mg N/L`.

### Peer-reviewed continuity source

Final publication:

- Mnyoro, M. S.; Munubi, R. N.; Chenyambuga, S. W.; Pedersen, L.-F. (2024)
- *Comparison of four different types of biomedia during start-up in a
  recirculating aquaculture system with rainbow trout*
- Journal of Water Process Engineering, volume 68, article 106549
- DOI: `10.1016/j.jwpe.2024.106549`
- peer reviewed: `true`
- exact `139` parameter independently verified in final article body by
  RATE-5L/R1: `false`

The final paper remains publication-continuity evidence only. It is not used
to impersonate an exact reviewed numeric support.

## 3. Carrier identity correction preserved

The available preprint supports:

`15 mm commercial polypropylene plastic beads`

It does not establish the exact product identity `RK Bioelements Heavy`.
RATE-5L/R1 therefore freezes:

`15_mm_commercial_polypropylene_plastic_beads`

and continues to reject RK/generic carrier substitution.

## 4. Directly supported assay context

The candidate preserves the following assay/context facts as canonical
identity-bearing information:

- freshwater context;
- fixed-bed upflow biofilters with media held between perforated plates;
- exact source-supported plastic carrier description;
- 20 L media filling per biofilter;
- water velocity `12 m/h`;
- water flow `1500 L/h`;
- air flow `5.0 L/min`;
- six-week startup with fish followed by weeks 7-8 without fish;
- closed-loop performance tests;
- nitrite spike approximately `5 mg NO2-N/L`;
- zero-order threshold strictly `> 1.0 mg NO2-N/L`.

The runtime evidence-context object contains only the directly supported
matching dimensions used by RATE-5L/R1:

- water type;
- biofilter mode;
- carrier identity;
- water velocity;
- nitrite concentration relative to the zero-order threshold;
- source-specific maturity context.

## 5. RATE-5L-R1 environmental scope correction

The preprint states that the following ranges were measured biweekly during
**experiment 1**:

- temperature: `15.0–16.8 °C`;
- dissolved oxygen: `9.2–10.8 mg/L`;
- pH: `7.0–7.4`.

It also reports experiment-1 alkalinity around:

- mean `125 mg/L as CaCO3`;
- SD `8.6 mg/L as CaCO3`.

Before the later kinetic phase, fish were removed and approximately 90% of the
system water was exchanged. The available RATE-5L artifact does not directly
bind exact temperature, dissolved oxygen, pH, or alkalinity values to the
closed-loop nitrite spike that produced the `139` parameter.

RATE-5L-R1 therefore classifies these environmental values as:

`experiment_1_reference_environment`

with:

`hard_guard = false`

They remain in the candidate canonical identity as documentary source context,
but they cannot establish kinetic-assay applicability.

## 6. Fail-closed applicability status

RATE-5L previously allowed the positive status:

`within_evidence_context`

when all fences passed.

RATE-5L-R1 removes that claim. A context matching every directly supported
assay dimension now returns only:

`assay_context_match_environment_unresolved`

This means:

- directly supported assay/context dimensions match;
- exact kinetic-assay environmental binding remains unresolved;
- no full applicability claim is made;
- no numerical rate execution is authorized.

A directly contradicted context still returns:

`outside_evidence_context`

with explicit blocking reason codes.

## 7. Canonical scientific-context binding

The candidate canonical payload now includes an `evidence_context` object with:

- exact assay-context categorical identities;
- exact `12 m/h` velocity;
- strict zero-order threshold `> 1.0 mg NO2-N/L`;
- maturity context;
- explicit `unresolved_exact_kinetic_assay_environment` state;
- experiment-1 reference T/DO/pH/alkalinity values marked non-guarding.

Changing any of these scientific context dimensions changes the candidate
canonical SHA-256.

This closes the RATE-5M identity blocker where two different applicability
contexts could previously share the same candidate identity.

## 8. Epistemic fail-closed invariants

The evidence bundle rejects all of the following:

- marking the SSRN preprint as peer reviewed;
- removing `exact_parameter_observed=True` from the preprint role;
- claiming that the final publication directly exposes the exact `139`;
- changing the frozen preprint artifact SHA-256;
- changing the final publication DOI;
- assigning either source to the wrong role;
- supplying a final-body artifact SHA that RATE-5L/R1 does not possess.

The candidate hardcodes:

- `execution_authorized = false`;
- `production_authorized = false`.

The numeric parameter is not constructor-configurable.

## 9. Explicitly absent capabilities

RATE-5L/R1 contains no:

- numerical ecosystem rate evaluation;
- `rate_decimal` output;
- `dt`, duration, elapsed time, time-step, or timestep;
- rate-to-extent integration;
- output-state identity;
- state mutation;
- MaterialBalance invocation;
- Scientific Foundation persistence;
- active pointer mutation;
- runtime policy mutation;
- production activation.

It does not import or construct:

- `RateScientificSupportV1`;
- `RateParameterV1`;
- `RateModelDefinitionV1`;
- `RateEvaluationV1`;
- `EcosystemStateV1`;
- `MaterialBalance`.

## 10. R1 test additions

The dedicated tests now verify that:

- candidate identity contains the canonical evidence context;
- changing carrier, reactor mode, velocity, threshold, maturity, unresolved
  environment state, or experiment-1 reference values changes candidate SHA;
- T/DO/pH are absent from the runtime assay-context input;
- experiment-1 T/DO/pH/alkalinity are explicitly non-guarding reference data;
- a fully matching direct assay context still returns
  `assay_context_match_environment_unresolved` rather than
  `within_evidence_context`;
- existing source identity, anti-escalation, carrier-substitution, and
  no-execution protections remain enforced.

## 11. Control-plane statement

RATE-5L/R1 does not touch the Scientific Foundation control plane.

Expected unchanged identities remain those frozen at RATE-5B:

- active scientific snapshot database SHA-256:
  `2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9`
- active pointer file SHA-256:
  `1fc84f79ed15dc68acebff454f494c90538664ce058173e33e80bf9e144e8014`
- runtime policy file SHA-256:
  `5f3a1afc0a9290882bb49e95e294786ba3be5af0ee8d7453141a5f184a2e64c5`

Remote GitHub work cannot independently certify the user's local external
pointer/policy files; local post-merge verification remains required.

## 12. Current gate result

```text
ECOBIOME_G7A_RATE_5L_R1
SCIENTIFIC_CONTEXT_IDENTITY_AND_KINETIC_ASSAY_SCOPE_CORRECTION

implementation = COMPLETE
canonical_context_binding = IMPLEMENTED
kinetic_assay_environment_scope = CORRECTED_FAIL_CLOSED
exact_139_preprint_parameter = UNCHANGED
carrier_identity = SOURCE_SUPPORTED_PLASTIC_BEADS_ONLY
numeric_rate_execution = ABSENT
scientific_foundation_mutation = FALSE
control_plane_mutation = FALSE
merge_authorized = FALSE
next_step = RATE_5M_REAUDIT_AFTER_CI
```

The PR must remain draft until the corrected head is green and RATE-5M is
re-audited.
