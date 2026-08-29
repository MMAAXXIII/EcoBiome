# PASSATION — EcoBiome G7A RATE-2C — TAN-to-Ammonia Mechanism Semantic Bridge Candidate

Gate:
`ECOBIOME_G7A_RATE_2C_TAN_TO_AMMONIA_MECHANISM_SEMANTIC_BRIDGE_CANDIDATE_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@f76ed83b64cd6e471fe1735bf842641905611792`

## RATE-2B frozen

RATE-2B mechanism candidate:

```text
candidate-g7a-ammonia-to-nitrite-mechanism-v1
payload SHA:
0b7f444bf34becee4967e42b91b87758aeb1780befac57a74b6b325d7522f15d
```

is preserved unchanged.

## RATE-2C bridge candidate

```text
candidate-g7a-tan-to-ammonia-mechanism-semantic-bridge-v1
payload SHA:
cbed8df87f5493284c72351705c1236970d6cd9fecbbf10baa422149e11c7572
```

Bridge kind:

```text
reservoir_to_reactive_species_accounting
```

## Scientific distinction

RATE-1D TAN semantics:

```text
TAN-N = NH3-N + NH4+-N
```

Reactive-substrate evidence:

```text
AMO substrate semantics -> ammonia / NH3
```

Therefore RATE-2C does **not** assert:

```text
TAN-N == NH3-N
TAN-N == NH4+-N
```

## Alignment consequence

The process-level candidate alignment becomes:

```text
alignment_class = interpretive_mechanism_support
epistemic_class = interpretive_support
```

rather than direct mechanism support.

Reason:

```text
scientific mechanism acts on a reactive species
RATE-1F source component is an analytical/model aggregate reservoir
```

## Rate boundary

This bridge authorizes no rate.

A future NH3-based RateModel requires explicit NH3 or a reviewed speciation
projection.

A separately reviewed empirical TAN-based RateModel may bind TAN directly if
its evidence actually uses TAN.

Mnyoro's parameter unit conflict remains unresolved.

## Persistence boundary

RATE-2C performs:

```text
source-code change              = false
Scientific Foundation V6 write = false
assertion insertion             = false
review insertion                = false
process support attachment      = false
remote write                    = false
```

## Next gate

`RATE-2D — Mechanism Alignment Review Package`

RATE-2D should assemble the mechanism candidate, semantic bridge candidate,
exact process evaluation scope, and a human-review decision template. It must
remain fail-closed until an explicit review decision exists.
