# EcoBiome — Assertion-Claim Link Human Review V1

Status: human review completed
Gate: RATE-2K
Scientific Foundation V6 write: forbidden

## 1. Link 1 — van Kessel et al. 2015

Candidate:

```text
assertion-link-candidate-g7a-nature16459-ammonia-to-nitrite-v1
```

Human decision:

```text
revise
```

The accepted revision changes only:

```text
semantic_alignment:
compatible_partial -> exact
```

Effective classification:

```text
stance             = supports
support_mode       = author_interpretation
scope_alignment    = source_broader
semantic_alignment = exact
```

Decision payload SHA-256:

```text
e2698ff08ab0f68bd493009f9a874a3ec3ba0106270b36f8e7b680a9ff34be70
```

The source claim explicitly states the ammonia-to-nitrite transformation.
Its additional nitrite-to-nitrate content is represented separately by
`scope_alignment=source_broader`.

## 2. Link 2 — Daims et al. 2015

Candidate:

```text
assertion-link-candidate-g7a-nature16461-ammonia-to-nitrite-v1
```

Human decision:

```text
accept
```

Effective classification:

```text
stance             = supports
support_mode       = author_interpretation
scope_alignment    = source_broader
semantic_alignment = compatible_partial
```

Decision payload SHA-256:

```text
a9a9bd007d9afe399bd1beef05d87467935e64d11f265c520b65f26742040583
```

## 3. Human assent source

The current human response was:

```text
ok
```

It directly accepted the immediately preceding RATE-2K recommendation:

```text
link 1: revise semantic_alignment=exact
link 2: accept
```

The review artifacts therefore bind the literal user message and the exact
recommendation being accepted.

## 4. V6 validator compatibility

Both effective link shapes must pass EcoBiome's frozen
`AssertionClaimLinksRow` validator.

RATE-2K validates the shapes but does not insert them.

## 5. Persistence boundary

```text
real V6 write                    = false
assertion_claim_link inserted    = false
evidence assessment inserted     = false
knowledge synthesis inserted     = false
source independence assessed     = false
ProcessScientificSupportV1       = false
numeric RateModel authorized     = false
remote write                     = false
```

## 6. Next gate

```text
RATE-2L — Reviewed Assertion-Link Shadow Materialization
```

RATE-2L may replay the reviewed source provenance on a disposable V6 copy and
materialize exactly these two human-reviewed link classifications there.

It must still leave source independence unresolved and must not write the real
Scientific Foundation V6.
