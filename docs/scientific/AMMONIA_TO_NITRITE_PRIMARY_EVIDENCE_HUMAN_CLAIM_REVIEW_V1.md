# EcoBiome — Primary Evidence Human Claim Review V1

Status: human review completed
Gate: RATE-2I
Scientific Foundation V6 write: forbidden

## 1. Claim 1 — van Kessel et al. 2015

Source:

```text
DOI   10.1038/nature16459
PMCID PMC4878690
```

Human decision:

```text
correct
```

Original claim:

```text
Nitrification includes an ammonia/ammonium oxidation step that produces nitrite before nitrite is oxidized to nitrate.
```

Corrected claim:

```text
Nitrification includes oxidation of ammonia to nitrite, followed by oxidation of nitrite to nitrate.
```

Corrected-text SHA-256:

```text
445533b6d4ebff5e36ad68c246268ae3ed9c93d1f6ed0284eb516de3b0a210e9
```

Decision payload SHA-256:

```text
3a6a3fc9c2d588c323692cf58ee30a7b628ded4f04507151fdbead3f5d954193
```

The correction keeps the first-step ammonia-to-nitrite mechanism while
removing the wording that could conflate ammonia/NH3 with ammonium or the TAN
reservoir.

## 2. Claim 2 — Daims et al. 2015

Source:

```text
DOI   10.1038/nature16461
PMCID PMC5152751
```

Human decision:

```text
accept
```

Accepted claim:

```text
Nitrification proceeds through ammonia oxidation involving nitrite before the subsequent nitrate state.
```

Claim SHA-256:

```text
7461bcc9d3facfb73adb18e579919cc03313bd52367e0e166a0f7fbae5320ac3
```

Decision payload SHA-256:

```text
482574cb105c21993933dabf519002d22cee71207d434fc1caec503e0fa5dcfb
```

No corrected text is attached to this decision.

## 3. Review-event projection

The two repository decision artifacts are designed to project one-to-one onto
future V6 `claim_review_events` rows:

```text
claim 1: decision=correct
         corrected_text present
         corrected_text_sha256 exact

claim 2: decision=accept
         corrected_text null
         corrected_text_sha256 null
```

RATE-2I does not itself write those rows because the two source claims currently
exist only in the validated RATE-2H shadow provenance graph, not in real V6.

## 4. Assertion-link boundary

Human claim review completion does not by itself determine:

```text
support_mode
scope_alignment
semantic_alignment
independence_status
```

Therefore RATE-2I still freezes:

```text
assertion_claim_links = none
evidence_assessments  = none
knowledge_synthesis   = none
ProcessScientificSupportV1 = none
```

The eventual assertion link must remain consistent with the already accepted
process-level alignment:

```text
interpretive_mechanism_support
interpretive_support
```

## 5. Independence boundary

The two primary studies remain distinct DOI records but are not automatically
counted as independent origins.

```text
independent_origin_count = unresolved
```

A later `EvidenceAssessment` must resolve that explicitly.

## 6. Persistence boundary

```text
real Scientific Foundation V6 write = false
claim_review_event inserted          = false
assertion_claim_link inserted        = false
source-code change                   = false
remote write                         = false
numeric RateModel authorized         = false
```

## 7. Next gate

```text
RATE-2J — Primary Evidence Review Replay + Assertion Link Candidates
```

RATE-2J should reconstruct the validated RATE-2H provenance graph on a
disposable V6 copy, apply these two exact claim-review events, and produce
human-reviewable assertion-link candidates without yet materializing any
supporting `assertion_claim_link`.
