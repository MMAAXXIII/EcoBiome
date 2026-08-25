# PASSATION — EcoBiome G7A RATE-1C — Generic RateModel V1 Contracts

Gate:
`ECOBIOME_G7A_RATE_1C_GENERIC_RATE_MODEL_V1_CONTRACTS_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@22c0d74527cedd64f19a79f5e26597e1bc6977fb`

## Implemented

New generic deterministic contracts:

- `RateScientificSupportV1`
- `RateQuantityRequirementV1`
- `RateInputQuantityBindingV1`
- `bind_rate_quantity_v1`
- `RateParameterV1`
- `RateParameterSetV1`
- `RateModelDefinitionV1`
- `RateApplicabilityResultV1`
- `RateEvaluationV1`

## Enforced invariants

1. Canonical rate unit is exactly `mg N/h`.
2. RateEvaluation is bound to an exact `EcosystemStateV1` SHA.
3. Quantity bindings are exact and state-preserving.
4. Definition support roles are distinct from the existing mechanism support:
   `kinetic_form` and `applicability_domain`.
5. Numeric parameters use `kinetic_parameter` support.
6. An applicable numeric evaluation requires:
   - complete definition support;
   - every required state quantity;
   - exact parameter coverage;
   - reviewed support for every parameter.
7. Non-applicable evaluations cannot carry a numeric rate.
8. Negative rates are rejected.
9. Integration-time identifiers (`dt`, `duration`, `elapsed_time`, `time_step`,
   `timestep`) are forbidden as RateModel parameter IDs.
10. `RateEvaluationV1` contains no output-state SHA and no time-step field.
11. No MaterialBalance call exists in this module.
12. No concrete nitrification formula or literature coefficient exists in this
    module.

## Deliberately not implemented

- no Mnyoro coefficient;
- no temperature coefficient;
- no Monod function;
- no ammonia/TAN rate evaluator;
- no nitrite component;
- no nitrate component change;
- no Δt integrator;
- no state mutation;
- no Scientific Foundation write;
- no remote write.

## Scientific status

RATE-1B remains authoritative:

```text
two-step nitrification target = adopted
first process = ammonia/TAN-N -> nitrite-N
numeric nitrification model approved = false
```

The generic contracts are therefore executable data contracts, not an
executable reviewed nitrification model.

## Next boundary

Before a concrete rate model can emit a number, EcoBiome must close two linked
gaps:

1. explicit TAN/nitrite/nitrate state semantics for the two-step vertical;
2. promotion/review of a complete kinetic evidence package with applicability
   and parameter identities.

Recommended next gate:

`RATE-1D — Two-step Nitrogen State Semantics Design`
