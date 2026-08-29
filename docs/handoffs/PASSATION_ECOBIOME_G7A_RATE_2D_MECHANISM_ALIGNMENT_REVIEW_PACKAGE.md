# PASSATION — EcoBiome G7A RATE-2D — Mechanism Alignment Review Package

Gate:
`ECOBIOME_G7A_RATE_2D_MECHANISM_ALIGNMENT_REVIEW_PACKAGE_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@99ad2aa0d187c9f142297de888faf572b800104d`

## RATE-2C frozen

RATE-2C bridge candidate:

```text
candidate-g7a-tan-to-ammonia-mechanism-semantic-bridge-v1
payload SHA:
cbed8df87f5493284c72351705c1236970d6cd9fecbbf10baa422149e11c7572
```

remains unchanged.

## RATE-2D package

Review package ID:

```text
review-g7a-ammonia-to-nitrite-mechanism-alignment-v1
```

Review payload SHA:

```text
4460d608d544cad1555ee8cd79ee3c6f09aa2f0c5fea5b2e0eb99c504f7ea602
```

Exact evaluation-scope SHA:

```text
72cc77fa3ccec09b16b99f00fa999be94df637e72490d2832e985486cd54a7de
```

## Proposed alignment

```text
role            = mechanism
alignment class = interpretive_mechanism_support
epistemic class = interpretive_support
```

No direct-support upgrade is allowed.

## Fail-closed review state

```text
decision = pending
all acceptance checks = false
human review completed = false
```

No support object is materialized.

## Materialization blockers

Before `ProcessScientificSupportV1` can exist:

```text
explicit human acceptance
all review checks true
persisted ScientificAssertionRefV1
exact alignment-policy identity
exact evaluation-scope SHA
```

are all required.

## Kinetic boundary

RATE-2D does not authorize:

```text
RateModel
kinetic form
kinetic parameter
Mnyoro coefficient
Δt
```

## Persistence boundary

```text
Scientific Foundation V6 write = false
assertion insertion             = false
review insertion                = false
source-code change              = false
remote write                    = false
```

## Next gate

`RATE-2E — Mechanism Alignment Human Review Decision`

RATE-2E must only be executed after an explicit human decision. No script or
default may infer acceptance from the existence of this review package.
