# Passation — EcoBiome V2.6 + Epistemic Enforcement V1

## Status

Local integration candidate. Do not commit/push automatically.

## Frozen assets

- Registry V2.6 canonical SHA: `46e768e56310c2f48efb4fe9b1f62b94c65ff38b5aeba97ea5d204cd4d9a3ce7`
- Coordinated-span/Epistemic Policy V1 canonical SHA: `1b4b25aca3cf57f1ed2c02b1fa27cf2208961d1b7c3d9b15508f7fea39852b2c`

## Added architecture

- `semantic_epistemic.py`: deterministic coordinated-span and epistemic controls.
- `semantic_benchmark_grounded_v2_6.py`: side-by-side wrapper over V2.3.3 grounded evaluator.
- V2.4 and V2.3.3 remain untouched.

## Safety rules

- No automatic conjunction split/merge/cross-product.
- Coordinated source grounding never grants entailment by itself.
- Forbidden epistemic upgrades are blocking.
- Epistemic-class identity never grants entailment by itself.
- Fixture #3 remains regression-only.
- Fixture #4 remains reserved for future generalization measurement.

## Next step after green integration

Run a controlled local Collector dry-run on a known source. Do not certify the production provider from that dry-run.
