# PASSATION — EcoBiome G7A RATE-2I — Primary Evidence Human Claim Review

Gate:
`ECOBIOME_G7A_RATE_2I_PRIMARY_EVIDENCE_HUMAN_CLAIM_REVIEW_LOCAL`

Expected precondition:
`agent/g7a-directional-nitrogen-semantic-stack-v1@1379e14139bb5e19554b0f029e434b53fa4a174f`

RATE-2H claim-review package:

```text
69a8d89758a650ce4eaa33dbf812a7ad769a94852498068a1312e535ed94fa70
```

## Human decisions

Claim 1:

```text
claim-g7a-nature16459-ammonia-to-nitrite-v1
decision = correct

corrected text:
Nitrification includes oxidation of ammonia to nitrite, followed by oxidation of nitrite to nitrate.

corrected SHA:
445533b6d4ebff5e36ad68c246268ae3ed9c93d1f6ed0284eb516de3b0a210e9

decision payload SHA:
3a6a3fc9c2d588c323692cf58ee30a7b628ded4f04507151fdbead3f5d954193
```

Claim 2:

```text
claim-g7a-nature16461-ammonia-to-nitrite-v1
decision = accept

claim SHA:
7461bcc9d3facfb73adb18e579919cc03313bd52367e0e166a0f7fbae5320ac3

decision payload SHA:
482574cb105c21993933dabf519002d22cee71207d434fc1caec503e0fa5dcfb
```

## Scientific boundary

These decisions review the source claims only.

They do not yet review or authorize:

```text
assertion_claim_link support_mode
scope_alignment
semantic_alignment
source independence
ProcessScientificSupportV1
kinetics
RateModel
```

## Persistence boundary

RATE-2I is docs/review-artifact only:

```text
real V6 write             = false
claim-review rows in V6   = false
assertion-link rows       = false
source-code change        = false
remote write              = false
```

Next:

`RATE-2J — Primary Evidence Review Replay + Assertion Link Candidates`
