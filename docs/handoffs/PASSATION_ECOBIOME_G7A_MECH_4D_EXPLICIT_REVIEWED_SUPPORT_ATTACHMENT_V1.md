# PASSATION — EcoBiome G7A MECH-4D — Explicit Reviewed Support Attachment V1

**Date:** 2026-08-24
**Gate:** `ECOBIOME_G7A_MECH_4D_EXPLICIT_REVIEWED_SUPPORT_ATTACHMENT_V1_LOCAL_R4`
**Precondition:** `agent/g7a-directional-nitrogen-semantic-stack-v1@c730abc28746cdb44fcd3bc0dac24b681ddca9e1`

## Purpose

Close the explicit attachment boundary after MECH-4C proved both accepted
Alignment V2 policies against the real Scientific Foundation V6 repositories.

The new attachment seam requires the caller to provide:

1. one exact `HumanReviewedAlignmentV2SelectionV1`;
2. the expected canonical SHA-256 of that human-reviewed selection;
3. the exact `ProcessEvaluationV1`;
4. Scientific Assertion and Knowledge Synthesis repositories.

No policy is discovered or selected automatically.

## Product change

`attach_g7a_reviewed_alignment_v2_support_v1(...)`:

- validates the exact human-reviewed selection identity;
- requires `accept / reviewed_confirmed / human`;
- preserves `automatic_acceptance = false`;
- preserves `automatic_attachment = false`;
- reruns Alignment V2 against the repositories;
- delegates attachment to the existing reviewed V1 support primitive;
- requires final status `scientific_alignment_reviewed`;
- proves the deterministic evaluation semantics are unchanged.

The following evaluation fields are invariant across attachment:

- evaluation identity;
- process definition;
- profile;
- input/output state SHA-256;
- parameters;
- parameter bases;
- process deltas;
- process assumptions.

Only scientific-support metadata, warnings and uncertainties may change.

## Scientific boundary

This gate does **not**:

- change `material_balance_v1.py`;
- calculate a nitrogen rate or process extent;
- persist ProcessEvaluation values;
- write Scientific Foundation V6;
- introduce Schema V7;
- auto-route an evaluation to an Alignment V2 policy;
- auto-accept scientific knowledge;
- auto-attach scientific support;
- push or modify PR #25.

The attachment occurs only because an explicit caller invokes the attachment seam
with the exact accepted selection identity.

## Validated nitrogen cases

- reduced inorganic N → oxidized inorganic N;
- dissolved inorganic N → biological N.

Cross-scope selection reuse remains fail-closed.

## Next boundary

Build the first end-to-end `EcosystemExplanationTraceV1` from these explicitly
supported `ProcessEvaluationV1` values, while keeping nitrogen extent explicit.
A kinetic/rate model remains a separate later boundary.
