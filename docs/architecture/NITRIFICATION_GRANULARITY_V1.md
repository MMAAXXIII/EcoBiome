# EcoBiome — Nitrification Granularity Decision V1

Status: adopted design decision
Gate: RATE-1B
Vertical: G7A nitrogen
Implementation status: no kinetic source code

## 1. Decision

EcoBiome adopts a **two-step nitrification target** for predictive work:

```text
ammonia/TAN-N -> nitrite-N -> nitrate-N
```

The existing deterministic G7A demonstration:

```text
reduced_inorganic_nitrogen -> oxidized_inorganic_nitrogen
```

remains valid as a reviewed **mechanism/direction demonstration**. It is not
deleted or retroactively reinterpreted as a nitrite-resolving kinetic model.

## 2. Why a two-step target is required

A predictive simulator must be able to represent a transient nitrite pool.

The two oxidation stages can respond differently to temperature, hydraulics,
substrate conditions and disturbances. A one-step net oxidation cannot explain
or predict nitrite accumulation.

Therefore:

> A RateModel that claims to predict nitrification dynamics must not use the
> current one-step reduced-N -> oxidized-N abstraction as though nitrite did
> not exist.

A lumped model remains permissible only when explicitly labelled as a
**lumped net nitrification model** and when its reviewed evidence and product
presentation make clear that nitrite transients are out of scope.

## 3. First future kinetic process

The first concrete kinetic target is:

```text
ammonia_oxidation_to_nitrite
```

with elemental-N transfer:

```text
ammonia/TAN-N -> nitrite-N
```

The target is process-level and does not assume that one microbial guild is the
exclusive biological agent. The scientific evidence for a concrete
implementation must define the observed system and microbial context.

The second future kinetic process is:

```text
nitrite_oxidation_to_nitrate
```

and receives its own RateModel and scientific support.

## 4. First model family scope

The first implementation candidate is intentionally narrow:

```text
freshwater attached-biofilm aquaculture biofilter
```

This is not a universal pond, aquarium, soil, sediment or water-column
nitrification model.

A model calibrated for a fixed-bed or moving-bed biofilter must never be
silently applied to:

- a sponge exhaust filter;
- free water-column nitrification;
- sediment;
- plant rhizosphere;
- a different carrier geometry;
- a marine system;
- a system outside the reviewed hydraulic domain.

Those contexts require their own reviewed applicability evidence or a
separately calibrated model.

## 5. TAN versus chemical species

Aquaculture biofilter kinetic studies often use **total ammonia nitrogen
(TAN)** as the measured substrate quantity.

RATE-1B therefore freezes this rule:

> A TAN-based empirical rate law must bind to an explicit TAN-N quantity or an
> auditable derivation of TAN-N. It must not silently substitute the existing
> `reduced_inorganic_nitrogen` model category.

Similarly, a model defined on NH4+-N or free NH3-N must bind to that exact
quantity or to an explicit speciation derivation.

The kinetic state semantics must preserve the difference between:

```text
TAN-N
NH4+-N
NH3-N
nitrite-N
nitrate-N
```

even when a higher-level explanation groups some of these into broader model
categories.

## 6. State-model consequence

The current material-balance evaluator admits:

```text
reduced_inorganic_nitrogen -> oxidized_inorganic_nitrogen
```

but no explicit intermediate nitrite transfer.

RATE-1B does not modify source code or add a new component. It records the
requirement that a future predictive vertical must provide an explicit nitrite
state before it can claim two-step nitrification prediction.

The future state design must decide the exact canonical component identifiers
and their scientific-entity bridges before material-balance support is
expanded.

## 7. Rate normalization consequence

The first evidence candidate is surface-normalized.

A future executable model of this family therefore requires explicit:

```text
TAN concentration
active/nominal biofilter surface area
hydraulic condition / water velocity
```

plus every environmental variable required by the reviewed applicability
domain.

The RateModel converts the supported normalized relation to the RATE-1A
canonical absolute output:

```text
mg N/h
```

No implicit filter area, reactor volume or “typical aquarium” constant is
allowed.

## 8. No cross-paper parameter splicing

RATE-1B explicitly forbids constructing a synthetic kinetic law by combining
independent parameters merely because they all concern nitrification.

Examples of combinations that are **not automatically valid**:

- a first-order substrate coefficient from one fixed-bed study
  multiplied by a temperature coefficient from a moving-bed study;
- a Monod half-saturation constant from wastewater treatment combined with a
  maximum rate from aquaculture;
- a pH response from a river model attached to a biofilter coefficient.

Cross-source synthesis is permissible only after a reviewed derivation or model
study establishes that the combination is scientifically justified.

## 9. RATE-1B implementation verdict

```text
two_step_granularity_adopted = true
first_process = ammonia_oxidation_to_nitrite
first_context = freshwater_attached_biofilm_aquaculture_biofilter
concrete_numeric_rate_model_ready = false
```

The blocker is not software architecture. It is exact kinetic evidence plus
explicit state semantics.

## 10. Next code boundary

RATE-1C may implement only the **generic RateModel V1 contracts** adopted by
RATE-1A:

- `RateModelDefinitionV1`;
- required quantity bindings;
- `RateParameterV1` / `RateParameterSetV1`;
- applicability result;
- `RateEvaluationV1`.

RATE-1C must still contain no concrete nitrification formula or kinetic
constant unless a separate reviewed evidence gate has first promoted a complete
parameter set.
