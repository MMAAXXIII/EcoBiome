# PASSATION — EcoBiome G7A RATE-2B — Mechanism Evidence Candidate Package

Gate:
`ECOBIOME_G7A_RATE_2B_MECHANISM_EVIDENCE_CANDIDATE_PACKAGE_LOCAL`

Precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@2f93cf026ad3bbcd38303a1ecbdcfc6adc619403`

## RATE-2A frozen

RATE-2A established:

```text
mechanism evidence candidate ready for review = true
kinetic-form candidate ready for review       = true
Mnyoro parameter unit resolved                 = false
numeric RateModel authorized                   = false
```

## RATE-2B artifact

A deterministic candidate JSON has been created:

```text
docs/scientific/candidates/AMMONIA_TO_NITRITE_MECHANISM_CANDIDATE_V1.json
```

Canonical candidate-payload SHA-256:

```text
0b7f444bf34becee4967e42b91b87758aeb1780befac57a74b6b325d7522f15d
```

The candidate uses two independent 2015 Nature primary studies:

```text
van Kessel et al. — DOI 10.1038/nature16459
Daims et al.      — DOI 10.1038/nature16461
```

## Candidate claim

```text
During aerobic nitrification, ammonia/ammonium nitrogen can be oxidized to
nitrite nitrogen as the first oxidation step.
```

No organism-exclusive claim is made.

## Important support boundary

The scientific claim concerns:

```text
ammonia/ammonium nitrogen -> nitrite nitrogen
```

The RATE-1F software process concerns:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
```

RATE-2B therefore does not create a reviewed
`ProcessScientificSupportV1`.

Required blocker:

```text
TAN-N -> ammonia/ammonium semantic bridge review
```

Until that bridge is reviewed:

```text
process_scientific_support_attachable = false
```

## Kinetic separation

RATE-2B contains no Mnyoro coefficient and does not alter the RATE-2A unit
conflict.

```text
kinetic_parameter_promotable = false
numeric_rate_model_authorized = false
```

## Persistence boundary

RATE-2B performs:

```text
Scientific Foundation V6 write = false
schema migration              = false
assertion insertion           = false
review insertion              = false
source-code change            = false
remote write                  = false
```

## Next gate

`RATE-2C — TAN-to-Ammonia Mechanism Semantic Bridge Candidate`

RATE-2C should review/materialize the semantic bridge required to align the
analytical TAN-N source component with the primary mechanism evidence, still
without writing Scientific Foundation V6.
