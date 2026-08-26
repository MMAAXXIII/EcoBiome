# PASSATION — EcoBiome G7A RATE-2Q — Assessment Policy Promotion + Independence Aggregation Design

Expected precondition:

```text
agent/g7a-directional-nitrogen-semantic-stack-v1@5c9a987c4884ab248e5328ebd7b4363e186b32bb
```

RATE-2P:

```text
materialization payload = 0f992cec2aa0f6d84dd1739da5d231e1b8436edeeff5c58dff7d9cb0dd5c27a4
projection contract     = 87df15ce0cd0201414fd39e9940af66249a67c48ef41ab19fdbf25b60ca1ce86
```

RATE-2Q candidates:

```text
assessment policy promotion = 508e273824f6e0b58765b6034c8e1a993c93d57ed8359a72a482d7e559a42ad1
independence aggregation    = f44bc14c91ace946836a0b11d5480244664133ab95449910a15498dfb0c2c75f
```

## Proposed policy promotion

```text
ecobiome-evidence-assessment-1-candidate
->
ecobiome-evidence-assessment-1
```

Scientific assessment fields remain unchanged.

## Aggregation rule

```text
partially_independent -> no integer projection
unresolved            -> no integer projection
```

Because `KnowledgeSynthesesRow.independent_support_origin_count` is a required
integer, the current ammonia-to-nitrite evidence set cannot yet produce a
KnowledgeSynthesis without information loss.

## Current state

```text
support links                     = 2
pairwise independence             = partially_independent
per-link independence_status      = unresolved
independent_support_origin_count  = null
knowledge synthesis               = blocked
```

## Boundaries

```text
policy adopted       = false
KnowledgeSynthesis   = none
schema migration     = none
real V6 write        = false
remote write         = false
RateModel            = unauthorized
```

## Next

`RATE-2R — Assessment Policy + Independence Aggregation Human Review`
