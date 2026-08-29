# EcoBiome — Primary Evidence Review Replay + Assertion-Link Candidates V1

Status: replay PASS; link candidates pending human review
Gate: RATE-2J

Review replay SHA-256:

```text
8ed77ae413ef85b87e772f6c77a714decb2b7ea16f291ee6fc288e5fa3779e6c
```

Assertion-link candidate package SHA-256:

```text
a1a9677f4a20956b184833147b0a3ea11b79de4d97ae5d96c742bb0cd6857d50
```

## 1. Exact RATE-2H replay

RATE-2J reacquired both PMC XML representations and required every frozen
RATE-2H content identity to match exactly:

```text
10.1038/nature16459
raw            fa8e4aff5b391665b1e40ab0dfbab102342e2b7b8a063d8462223610b26f3112
representation b6381ea1cf12c5e3275d9dfdb71d3e7b5b1f437d385ab359a55497ed4ff7ad5c
evidence       ac8ba171582a37a611c119702345a1cd9cf1645977234c82900a4b0baf12ff1f

10.1038/nature16461
raw            0dcc84cb40ce5009d1cf7443c6a75c9e7eb788f2773bb4e9ad9a14ba2c4d9941
representation 055dbad29329b542f83a0d051aad92cbbde46d6fb5b9e97e089c181bb97e4b08
evidence       6dd08e05dd4c8f400651fe422c5a162625da0eb52cc25315611d181bdf041b9b
```

Any upstream article-byte or normalization drift causes fail-closed behavior.

## 2. RATE-2I human reviews replayed

Claim 1:

```text
decision      = correct
effective SHA = 445533b6d4ebff5e36ad68c246268ae3ed9c93d1f6ed0284eb516de3b0a210e9
```

Claim 2:

```text
decision      = accept
effective SHA = 7461bcc9d3facfb73adb18e579919cc03313bd52367e0e166a0f7fbae5320ac3
```

Exactly two `claim_review_events` were inserted on the disposable shadow.

The real V6 was not modified.

## 3. Proposed link classification

Both candidate links propose:

```text
stance             = supports
support_mode       = author_interpretation
scope_alignment    = source_broader
semantic_alignment = compatible_partial
review_status      = pending_human_review
```

This shape passes EcoBiome's V6 assertion-link validator.

### Why `author_interpretation`

The source statements synthesize the nitrification mechanism at article level.
They are not themselves direct measurements of the exact EcoBiome assertion.

### Why `source_broader`

Both source claims describe the ammonia-to-nitrite step inside a broader
nitrification sequence that also includes the nitrite-to-nitrate step.

### Why `compatible_partial`

The ammonia-to-nitrite semantics support the target assertion, but each source
claim contains additional mechanism scope beyond that target.

## 4. No automatic link insertion

RATE-2J deliberately leaves:

```text
assertion_claim_links = 0 new rows
```

Human acceptance of a source claim does not automatically accept EcoBiome's
classification of that claim as evidence for a particular assertion.

## 5. Independence remains unresolved

RATE-2J still does not assign:

```text
independent_support_origin_count
```

That belongs to evidence assessment, especially because the two papers share
authors.

## 6. Next gate

```text
RATE-2K — Assertion-Claim Link Human Review
```

Each of the two candidate link classifications requires explicit human
`accept`, `reject`, or `revise`.
