# PASSATION — EcoBiome G7A RATE-1E — Canonical Nitrogen State + Projection Contracts

Gate:
`ECOBIOME_G7A_RATE_1E_CANONICAL_NITROGEN_STATE_AND_PROJECTION_CONTRACTS_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@b1e20c74f33d479f48c49e63ff00678cbadc456e`

## Implemented

New deterministic module:

`src/ecobiome/simulation/nitrogen_state_v1.py`

Contracts/functions:

- `PredictiveNitrogenInventoryBindingV1`
- `PredictiveNitrogenStateValidationV1`
- `validate_predictive_nitrogen_state_v1`
- `NitrogenConcentrationProjectionV1`
- `project_nitrogen_concentration_v1`
- `PredictiveNitrogenConcentrationSetV1`
- `project_predictive_nitrogen_concentrations_v1`

## Primary predictive inventories

Exactly these three components form the RATE-1D predictive nitrification
inventory set:

```text
total_ammonia_nitrogen
nitrite_nitrogen
nitrate_nitrogen
```

Each uses:

```text
variable_id = material_inventory
unit        = mg N
zone_id     = exact water zone
```

Inventories must be non-negative.

## Non-overlap enforcement

A validated predictive nitrogen zone rejects these additional primary
`material_inventory` identifiers:

```text
unionized_ammonia_nitrogen
ammonium_nitrogen
dissolved_inorganic_nitrogen
reduced_inorganic_nitrogen
oxidized_inorganic_nitrogen
```

This prevents double-counting TAN partitions and legacy aggregate/process
abstractions.

`biological_nitrogen` is not rejected because it is a separate nitrogen pool,
not an alternative representation of TAN/nitrite/nitrate.

## Concentration projection

The projection:

```text
material_inventory mg N
       /
exact water_volume converted to L
       =
material_concentration mg N/L
```

is deterministic and state-preserving.

Supported exact input water-volume units are aligned with current deterministic
water-volume handling:

```text
L
liter
litre
mL
```

The canonical output is always:

```text
mg N/L
```

The projection carries:

- exact input-state SHA;
- exact inventory quantity and basis SHA;
- exact water-volume quantity and basis SHA;
- deterministic derived concentration quantity;
- projection identity;
- fixed decimal precision/rounding metadata.

For non-terminating decimal ratios, RATE-1E freezes:

```text
precision = 28 significant decimal digits
rounding  = ROUND_HALF_EVEN
```

This is a deterministic numeric projection policy, not a statement about
measurement precision.

## Source-of-truth boundary

RATE-1E does not add derived concentrations back into `EcosystemStateV1`.

An observed concentration may coexist as evidence in the generic state, but
validation counts only primary `material_inventory` quantities.

RATE-1E therefore does not treat inventory and concentration as two additive
stocks.

## Deliberately not implemented

- no TAN -> NH3/NH4 speciation equation;
- no pKa;
- no molecular/ionic mass conversion;
- no Mnyoro/Kinyage/Monod coefficient;
- no RateModel formula;
- no Δt;
- no MaterialBalance transformation extension;
- no mutation of EcosystemStateV1;
- no Scientific Foundation V6 write;
- no remote write.

## Legacy compatibility

The frozen G7A demonstration is untouched.

RATE-1E does not globally redefine legacy process-scoped component semantics.
It only refuses overlapping legacy inventories when explicitly validating a
new predictive nitrogen zone.

## Next gate

`RATE-1F — Two-step Nitrogen MaterialBalance Contracts`

RATE-1F may add deterministic elemental-N transfer support for:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
nitrite_nitrogen       -> nitrate_nitrogen
```

It must still consume an explicit extent and must not introduce a kinetic
formula or Δt integration.
