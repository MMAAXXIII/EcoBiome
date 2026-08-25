# PASSATION — EcoBiome G7A RATE-1A — RateModel V1 Design

Gate:
`ECOBIOME_G7A_RATE_1A_RATE_MODEL_V1_DESIGN_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@22229c76afe336a89cdea026ebf8dfd86ac976a6`

## Result expected

Design-only commit. No source-code kinetic implementation.

## Frozen decisions

1. RateModel V1 returns an instantaneous, absolute elemental-N rate in
   `mg N/h`.
2. RateModel does not mutate EcosystemState and does not call MaterialBalance.
3. Δt/integration is a separate future contract.
4. Every scaling quantity must be explicit.
5. Mechanism support is insufficient for a numerical rate.
6. Separate reviewed roles are required for kinetic form, kinetic parameters
   and applicability domain.
7. Missing driver/support/out-of-domain conditions fail closed.
8. Current Scientific Foundation V6 remains insufficient for a concrete
   reviewed RateModel.
9. A concrete nitrification model must explicitly choose lumped net
   nitrification or a two-step ammonium -> nitrite -> nitrate representation.
10. Preferred long-term direction is two-step so nitrite transients remain
    representable.

## No-go items in RATE-1A

- no Monod implementation;
- no Q10/Arrhenius implementation;
- no kinetic constant in Python;
- no default temperature coefficient;
- no rate calculation;
- no Δt;
- no new nitrogen component;
- no persistence;
- no Scientific Foundation write;
- no remote Git write.

## Next gate

`RATE-1B — Nitrification Granularity + Scientific Evidence Candidate`

It should decide the exact first kinetic mechanism and gather/review the
corresponding kinetic evidence before any numerical RateModel is enabled.
