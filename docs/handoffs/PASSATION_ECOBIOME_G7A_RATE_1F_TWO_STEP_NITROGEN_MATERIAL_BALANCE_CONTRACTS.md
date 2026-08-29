# PASSATION — EcoBiome G7A RATE-1F — Two-step Nitrogen MaterialBalance Contracts

Gate:
`ECOBIOME_G7A_RATE_1F_TWO_STEP_NITROGEN_MATERIAL_BALANCE_CONTRACTS_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@d069664d0eecbfda9ac4a3b480a549282581e35f`

## Implementation strategy

RATE-1F deliberately does **not** modify the historical:

```text
src/ecobiome/simulation/material_balance_v1.py
```

The frozen G7A deterministic demonstration therefore keeps its existing
MaterialBalance implementation byte-for-byte.

The predictive two-step balance is isolated in:

```text
src/ecobiome/simulation/nitrogen_material_balance_v1.py
```

## New deterministic processes

```text
ammonia_oxidation_to_nitrite_extent_v1
nitrite_oxidation_to_nitrate_extent_v1
```

Admitted edges:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
nitrite_nitrogen       -> nitrate_nitrogen
```

No reverse or one-step TAN -> nitrate edge is admitted.

## Exact extent boundary

The evaluator consumes:

```text
explicit extent
unit = mg N
```

It never calculates that extent.

The extent:

- must be non-negative;
- cannot exceed the source inventory;
- is transferred exactly from source to target.

## State boundary

Before and after every transfer, RATE-1F calls the RATE-1E predictive nitrogen
state validator.

Therefore the material balance requires:

```text
total_ammonia_nitrogen
nitrite_nitrogen
nitrate_nitrogen
```

as exact non-overlapping `material_inventory` values in `mg N`.

Overlapping TAN partitions or legacy aggregate inventories are rejected.

## Conservation invariant

The evaluator records and verifies:

```text
TAN-N + nitrite-N + nitrate-N
```

before and after each transformation.

The exact elemental-N total must be unchanged.

The ProcessEvaluation parameters contain:

- pre-state predictive nitrogen validation SHA;
- post-state predictive nitrogen validation SHA;
- total primary nitrogen before;
- total primary nitrogen after;
- explicit extent and basis.

## Scientific support boundary

Both new process definitions require the future scientific role:

```text
mechanism
```

RATE-1F embeds no real reviewed two-step mechanism assertion.

Without reviewed process-specific alignment:

- scenario/user extent -> `scenario_hypothesis`;
- assertion ref alone -> `support_missing`.

The contract can accept a future exact `ProcessScientificSupportV1` attachment
without changing the material-balance arithmetic.

The existing reviewed one-step ammonium -> nitrate assertion is **not**
silently reused as support for ammonium/TAN -> nitrite.

## Deliberately not implemented

- no kinetic law;
- no Mnyoro coefficient;
- no Monod expression;
- no temperature coefficient;
- no RateModel invocation;
- no rate -> extent conversion;
- no Δt;
- no ammonia speciation;
- no Scientific Foundation V6 write;
- no remote write.

## Next scientific blocker

After RATE-1F, the deterministic state and balance layers can represent an
explicit two-step nitrogen scenario.

The next numerical predictive step remains blocked until EcoBiome has:

1. process-specific reviewed mechanism evidence for TAN/ammonia -> nitrite;
2. a reviewed kinetic-form + parameter + applicability package for the chosen
   first RateModel;
3. a later explicit rate-to-extent integration contract.

Recommended next gate:

`RATE-2A — Ammonia-to-Nitrite Scientific Evidence Promotion Design`
