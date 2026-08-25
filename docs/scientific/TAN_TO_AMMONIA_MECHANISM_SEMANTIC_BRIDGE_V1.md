# EcoBiome — TAN-to-Ammonia Mechanism Semantic Bridge Candidate V1

Status: candidate ready for human review
Gate: RATE-2C
Persistence status: NOT part of Scientific Foundation V6

Canonical candidate-payload SHA-256:

```text
cbed8df87f5493284c72351705c1236970d6cd9fecbbf10baa422149e11c7572
```

## 1. Purpose

RATE-2B produced a scientifically strong mechanism candidate for:

```text
ammonia/ammonium nitrogen -> nitrite nitrogen
```

RATE-1F, however, moves elemental nitrogen from:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
```

RATE-2C defines the semantic bridge between these layers without pretending
that the aggregate TAN pool is one chemical species.

## 2. TAN-N is an analytical/model reservoir

RATE-1D froze:

```text
TAN-N = NH3-N + NH4+-N
```

The RATE-1E primary component:

```text
total_ammonia_nitrogen
```

is therefore an elemental-N inventory over the aqueous ammonia system.

It is not synonymous with:

```text
NH3
NH4+
```

and RATE-2C does not make either identification.

## 3. Reactive substrate evidence

Jung et al. studied ammonia-oxidizer substrate kinetics across pH and report
evidence supporting the hypothesis that ammonia rather than ammonium is the
substrate of ammonia monooxygenase for ammonia-oxidizing archaea and comammox,
consistent with the established interpretation for ammonia-oxidizing bacteria.

Reference:

Man-Young Jung et al.
"Ammonia-oxidizing archaea possess a wide range of cellular ammonia
affinities."

The ISME Journal 16, 272–283.

```text
DOI  : 10.1038/s41396-021-01064-z
PMID : 34316016
PMC  : PMC8692354
```

Source:
https://doi.org/10.1038/s41396-021-01064-z

RATE-2C uses this source for **substrate semantics**, not to import a kinetic
parameter or affinity value.

## 4. Bridge type

The adopted candidate bridge kind is:

```text
reservoir_to_reactive_species_accounting
```

Its interpretation is:

> An explicit RATE-1F elemental-N extent removed from TAN-N can represent
> nitrogen leaving the total ammonia reservoir through ammonia oxidation,
> without asserting that the whole TAN inventory is instantaneously NH3.

This is a bookkeeping/model bridge.

It is **not** a chemical identity bridge.

## 5. Why the alignment is interpretive

The literature directly supports a reactive-species mechanism involving
ammonia.

The RATE-1F source quantity is an aggregate TAN-N inventory.

Consequently the candidate process alignment is deliberately downgraded from
the provisional RATE-2B value:

```text
direct_mechanism_support
explicit_causal_result
```

to:

```text
interpretive_mechanism_support
interpretive_support
```

This preserves the distinction between:

```text
direct scientific result
```

and:

```text
model interpretation needed to bind that result to EcoBiome state semantics
```

No support object is created yet.

## 6. Acid/base partition boundary

To know how much of TAN is present as NH3-N rather than NH4+-N, a future
speciation model needs explicit environmental inputs.

At minimum for the freshwater V1 direction:

```text
TAN-N
pH
temperature
```

and an applicability statement concerning ionic strength/salinity.

RATE-2C includes no equilibrium equation and no pKa.

Missing pH/temperature therefore blocks an NH3-fraction calculation.

## 7. Material balance versus kinetics

The deterministic RATE-1F MaterialBalance may consume an explicit extent
because it only accounts for elemental-N transfer.

It does not need to calculate the NH3 fraction to preserve mass.

A mechanistic kinetic model using NH3 does need either:

```text
an explicit NH3 quantity
```

or:

```text
a reviewed TAN -> NH3 speciation projection
```

before rate evaluation.

## 8. Empirical TAN RateModels remain possible

An empirical kinetic study may define its rate law directly against measured
TAN concentration.

If that evidence is independently reviewed, a RateModel may bind:

```text
TAN-N concentration
```

directly.

That does not change the biochemical statement that AMO substrate semantics
are associated with ammonia rather than the total TAN aggregate.

Therefore RATE-2C keeps these evidence chains separate:

```text
mechanistic substrate semantics
empirical TAN-rate relation
```

## 9. Mnyoro blocker unchanged

RATE-2C does not resolve the RATE-2A Mnyoro coefficient conflict:

```text
0.45 m/h
versus
0.45 m/d
```

The parameter remains non-promotable.

## 10. Human review decision required

Before process scientific support can be attached, a reviewer must confirm:

1. TAN-N aggregate semantics;
2. mechanism candidate source lineage;
3. ammonia-vs-ammonium substrate interpretation;
4. the reservoir-accounting bridge;
5. the downgrade to `interpretive_mechanism_support`;
6. exact RATE-1F process bindings.

Until then:

```text
human_review_completed = false
process_scientific_support_attachable = false
```

## 11. RATE-2C verdict

```text
bridge_candidate_materialized = true
bridge_kind = reservoir_to_reactive_species_accounting

TAN_equals_NH3 = false
TAN_equals_NH4 = false

alignment_class_candidate = interpretive_mechanism_support
epistemic_class_candidate = interpretive_support

human_review_completed = false
scientific_foundation_write = false
numeric_rate_model_authorized = false
```

Recommended next gate:

```text
RATE-2D — Mechanism Alignment Review Package
```
