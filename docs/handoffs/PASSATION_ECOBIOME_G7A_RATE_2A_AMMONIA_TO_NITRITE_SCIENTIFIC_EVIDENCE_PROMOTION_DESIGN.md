# PASSATION — EcoBiome G7A RATE-2A — Ammonia-to-Nitrite Scientific Evidence Promotion Design

Gate:
`ECOBIOME_G7A_RATE_2A_AMMONIA_TO_NITRITE_SCIENTIFIC_EVIDENCE_PROMOTION_DESIGN_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@dbf75dc133506cd28e311a9dcc8645e93e2422ce`

## RATE-1F frozen

RATE-1F is validated and frozen at the precondition above.

It provides deterministic explicit-extent transfers:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
nitrite_nitrogen       -> nitrate_nitrogen
```

without kinetics or Δt.

## RATE-2A decisions

Scientific evidence roles are separated into:

```text
mechanism
kinetic_form
kinetic_parameter
applicability_domain
```

### Mechanism candidate

Peer-reviewed nitrification literature supports ammonia oxidation through a
nitrite intermediate.

Candidate sources include:

- van Kessel et al. 2015, Nature, DOI 10.1038/nature16459;
- Daims et al. 2015, Nature, DOI 10.1038/nature16461.

The future persisted claim must be process-level and must not assert that one
microbial guild is exclusively responsible.

### Kinetic-form candidate

Mnyoro et al. 2021 supports evaluation of a first-order surface TAN-removal
relation in a freshwater pilot fixed-bed RAS at the two highest tested water
velocities:

```text
10.8 m/h
16.2 m/h
```

### Parameter blocker

The publication contains an internal unit conflict for the reported coefficient
`0.45`:

```text
abstract/results sentence : m h^-1
conclusion/Fig. 4 caption : m d^-1
```

Equation (1) and dimensional analysis support `m d^-1`, but RATE-2A does not
silently correct the source.

Therefore:

```text
kinetic_parameter_promotable = false
numeric_rate_model_authorized = false
```

### Applicability discipline

Temperature, pH, dissolved oxygen and alkalinity observed in the Mnyoro trial
are context values, not experimentally validated response functions.

No temperature/pH/DO correction is authorized.

## V6 boundary

RATE-2A performs:

```text
Scientific Foundation V6 write = false
schema migration              = false
assertion insertion           = false
review insertion              = false
remote write                  = false
```

## Recommended next gate

`RATE-2B — Mechanism Evidence Candidate Package`

RATE-2B should build a fully auditable candidate package for the
`ammonia_oxidation_to_nitrite_extent_v1` mechanism assertion, still without
writing V6.

The kinetic parameter should remain separately blocked until the Mnyoro unit
conflict is explicitly resolved.
