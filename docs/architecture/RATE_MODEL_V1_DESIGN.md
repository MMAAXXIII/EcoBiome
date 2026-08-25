# EcoBiome — RateModel V1 Design

Status: proposed design contract
Scope: design only; no kinetic implementation
Vertical: G7A nitrogen

## 1. Why this contract exists

The reviewed nitrogen vertical currently proves:

- exact deterministic material transfer;
- elemental-N conservation;
- reviewed mechanism/direction support;
- human-reviewed scientific attachment provenance;
- reproducible explanation.

It does **not** prove or calculate:

- reaction velocity;
- a kinetic law;
- kinetic parameters;
- elapsed-time evolution;
- a forecasted process extent.

`evaluate_nitrogen_transformation_extent_v1()` therefore remains an exact
material-balance evaluator that consumes an already-known elemental-N extent.
RateModel V1 must sit *upstream* of that evaluator and must not weaken its
existing invariants.

## 2. Non-negotiable separation

The target architecture is:

```text
EcosystemStateV1
      |
      | exact required quantities + reviewed rate parameters
      v
RateModelV1
      |
      | instantaneous rate evaluation
      v
RateEvaluationV1
      |
      | explicit integration request / Δt
      v
ProcessExtentIntegrator (separate contract, not RATE-1A)
      |
      | predicted absolute extent in mg N
      v
existing evaluate_nitrogen_transformation_extent_v1()
      |
      v
ProcessEvaluationV1 + new EcosystemStateV1
```

RateModel V1 SHALL NOT:

- mutate `EcosystemStateV1`;
- call `replace_quantities`;
- call MaterialBalance;
- accept an already-computed process extent;
- hide Δt inside a parameter;
- infer missing environmental drivers;
- silently extrapolate outside its reviewed applicability domain.

## 3. RateModelDefinitionV1

A future executable contract should define at minimum:

```text
rate_model_id
version
process_id
process_version
source_component_id
target_component_id
required_state_quantities
required_parameters
output_rate_unit
assumptions
```

### V1 output unit

The integration boundary should consume an **absolute elemental-N transfer
rate**:

```text
mg N / h
```

If published evidence gives a normalized rate such as:

- mg N / L / h;
- g N / m² / d;
- mg N / g biomass / h;

the RateModel implementation must require the corresponding scaling quantity
(volume, active biofilter area, biomass, etc.) explicitly and convert to
`mg N / h` inside an auditable evaluation.

There is no implicit “per aquarium” normalization.

## 4. Required state quantities are explicit

A RateModel must declare every state quantity it reads, including exact units
and semantic role.

A nitrification model may eventually require quantities such as:

- source nitrogen inventory or concentration;
- dissolved oxygen;
- water temperature;
- pH;
- water volume;
- nitrifier biomass or active biofilter area;
- salinity or other applicability drivers.

RATE-1A does not decide that all these variables belong to every model.
The concrete reviewed kinetic formulation must decide its exact driver set.

Missing required data is a hard non-evaluable state, not a default.

## 5. Scientific support taxonomy

Existing `ProcessScientificSupportV1(role="mechanism")` establishes a reviewed
mechanism/direction. It is **insufficient** to authorize a numerical rate.

RateModel V1 requires distinct reviewed support roles:

```text
kinetic_form
kinetic_parameter
applicability_domain
```

Potential additional roles may be introduced later only if required by a real
paper-backed implementation.

A numeric rate may be emitted only when:

1. the kinetic mathematical form is reviewed;
2. every numerical parameter used by the evaluation is bound to reviewed
   scientific support;
3. the current state is inside the reviewed applicability domain;
4. all required scaling quantities are explicit.

Mechanism support may be referenced for semantic continuity, but it cannot
upgrade itself into kinetic evidence.

## 6. RateParameterSetV1

Every parameter must be independently auditable.

A future canonical parameter entry should include at minimum:

```text
parameter_id
value_decimal
unit
semantic_role
scientific_assertion_ref
reviewed_support_identity
applicability_scope
```

A parameter set must have its own deterministic canonical SHA-256.

No anonymous numeric constants may appear in a reviewed RateModel
implementation.

## 7. Applicability is fail-closed

RateModel V1 must represent applicability as an explicit evaluation result.

Candidate statuses:

```text
applicable
missing_required_quantity
outside_reviewed_domain
scientific_support_missing
parameter_support_missing
```

Only `applicable` may carry a numerical rate.

V1 must not clamp an environmental driver to the nearest published value and
continue as though the state were supported.

Interpolation/extrapolation policy belongs to the reviewed model design and
must itself be explicit.

## 8. RateEvaluationV1

A successful rate evaluation should contain:

```text
evaluation_id
rate_model_definition_sha256
input_state_sha256
zone_id
rate_decimal
rate_unit = "mg N/h"
parameter_set_sha256
scientific_supports
required_quantity_bindings
applicability_result
warnings
uncertainties
```

It is deterministic and state-preserving.

The evaluation's canonical SHA-256 must change if any of these identities
change.

## 9. Δt is intentionally outside RateModel V1

A rate is not an extent.

RATE-1A therefore forbids `duration`, `dt`, `elapsed_time`, `time_step` or an
equivalent hidden integration parameter inside RateModelDefinitionV1 or
RateEvaluationV1.

A later integration contract will explicitly define:

- duration value and unit;
- numerical integration policy;
- assumptions about rate variation during the interval;
- source-availability limiting;
- conversion from rate to candidate process extent.

This prevents a constant-rate Euler approximation from being introduced
silently.

## 10. Nitrification granularity decision

The current reviewed vertical maps an ammonium oxidation mechanism to:

```text
reduced_inorganic_nitrogen -> oxidized_inorganic_nitrogen
```

with the reviewed target bridge representing nitrate.

That abstraction is sufficient for the current deterministic mechanism
demonstration, but kinetic simulation raises a new requirement: nitrification
can require distinct ammonia-oxidation and nitrite-oxidation dynamics.

Therefore RATE-1A adopts this rule:

> No concrete nitrification RateModel may be attached to the current one-step
> vertical until the implementation gate explicitly declares whether it is a
> reviewed **lumped net nitrification model** or a reviewed **two-step model**
> with an explicit nitrite state.

EcoBiome must never present a lumped model as though it predicted nitrite
transients.

### Preferred scientific direction

For the long-term aquarium/pond simulator, the preferred target is a two-step
representation:

```text
ammonium-N -> nitrite-N -> nitrate-N
```

because it preserves the possibility of modelling nitrite accumulation and its
distinct kinetics.

This is a design preference, not yet an implemented schema change.

## 11. Current Scientific Foundation boundary

Scientific Foundation V6 is frozen and remains read-only.

Its currently reviewed G7A assertions support the oxidation and assimilation
mechanism/direction vertical. RATE-1A adds **no kinetic assertion, parameter,
rate law, or applicability evidence** to V6.

Consequently:

```text
reviewed concrete RateModel available now = NO
```

The next concrete kinetic implementation must first obtain and review the
specific scientific evidence required by its chosen formulation.

## 12. First implementation candidate

The first RateModel candidate should concern nitrogen oxidation rather than
assimilation because it is directly coupled to the first predictive water
quality question and to the existing reviewed oxidation vertical.

However the implementation is blocked pending both:

1. the nitrification granularity choice above;
2. reviewed kinetic-form/parameter/applicability evidence.

RATE-1A deliberately stops before either numerical formula or parameter value
is committed to source code.

## 13. Invariants to test when RateModel contracts are implemented

Future contract tests must prove:

- canonical determinism;
- no state mutation;
- exact `input_state_sha256` binding;
- exact model and parameter-set identity;
- numeric rate forbidden without reviewed kinetic support;
- numeric rate forbidden outside applicability;
- numeric rate forbidden with missing driver;
- exact `mg N/h` output basis;
- no Δt field in RateModel V1;
- no MaterialBalance invocation;
- no implicit parameter constants;
- mechanism support alone cannot authorize a rate.

## 14. Accepted next sequence

```text
RATE-1A  Design contract                 <- this gate
RATE-1B  Nitrification granularity + scientific evidence candidate
RATE-1C  RateModel V1 code contracts (no concrete formula if evidence not ready)
RATE-2A  First reviewed kinetic model
RATE-2B  Explicit Δt / integration contract
RATE-2C  Rate -> extent -> MaterialBalance vertical
RATE-2D  Product explanation / UI
```

This order may compress RATE-1B and RATE-1C if the reviewed evidence and state
semantics are already sufficient, but no gate may skip the scientific-support
boundary.
