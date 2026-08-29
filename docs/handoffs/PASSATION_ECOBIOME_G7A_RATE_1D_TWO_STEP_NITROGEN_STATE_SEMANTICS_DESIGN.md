# PASSATION — EcoBiome G7A RATE-1D — Two-step Nitrogen State Semantics

Gate:
`ECOBIOME_G7A_RATE_1D_TWO_STEP_NITROGEN_STATE_SEMANTICS_DESIGN_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@84ceb6cf4af0dde22d1f7716af11424d8d3ff0c8`

## Adopted state semantics

Primary predictive water-zone nitrogen inventories:

```text
total_ammonia_nitrogen
nitrite_nitrogen
nitrate_nitrogen
```

Canonical extensive unit:

```text
mg N
```

Derived concentration unit:

```text
mg N/L
```

## Non-overlap rule

`NH3-N` and `NH4+-N` are derived partitions of TAN-N:

```text
TAN-N = NH3-N + NH4+-N
```

They are not additional primary inventories.

A reporting DIN aggregate is likewise derived and is not a fourth primary
inventory.

## Measurement rule

Species-mass and elemental-N reporting must remain distinct:

```text
mg NH4/L != mg N/L
mg NO2/L != mg N/L
mg NO3/L != mg N/L
```

Conversion requires explicit analyte semantics and auditable deterministic
normalization.

## Speciation rule

Future NH3/NH4+ speciation requires explicit TAN, pH, temperature and a
freshwater ionic-strength/salinity applicability statement.

No pH or temperature default is allowed.

## Legacy compatibility

The frozen G7A components:

```text
reduced_inorganic_nitrogen
oxidized_inorganic_nitrogen
dissolved_inorganic_nitrogen
biological_nitrogen
```

remain process-scoped demonstration abstractions.

RATE-1D does not globally identify them with the new predictive components and
does not change the frozen nitrogen demonstration artifact.

## No-go items

RATE-1D contains:

- no source-code change;
- no material-balance extension;
- no explicit nitrite state object yet;
- no ammonia speciation formula;
- no pKa;
- no kinetic coefficient;
- no RateModel implementation;
- no Δt;
- no Scientific Foundation V6 write;
- no remote write.

## Next gate

`RATE-1E — Canonical Nitrogen State + Projection Contracts`

RATE-1E may implement deterministic quantity/state projections and explicit
non-overlap invariants. It must not implement kinetics or time integration.
