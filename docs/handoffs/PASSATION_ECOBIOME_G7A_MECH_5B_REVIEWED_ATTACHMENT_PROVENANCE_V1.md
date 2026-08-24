# PASSATION — EcoBiome G7A MECH-5B — Reviewed Attachment Provenance V1

**Date:** 2026-08-24
**Gate:** `ECOBIOME_G7A_MECH_5B_REVIEWED_ATTACHMENT_PROVENANCE_V1_LOCAL`
**Precondition:** `agent/g7a-directional-nitrogen-semantic-stack-v1@f5083c5e1f987b702bc76454c84fbf8deb1bd939`

## Purpose

Close the remaining governance-provenance gap identified by MECH-5A without
changing scientific support semantics, deterministic N4 process semantics, or
the existing `EcosystemExplanationTraceV1` contract.

MECH-5A proved that reviewed Alignment V2 supports propagate into the existing
explanation trace. It also showed that the trace alone does not identify the
exact human-reviewed selection that authorized each attachment.

## Additive design

MECH-5B adds two compositional objects.

### `ReviewedSupportAttachmentReceiptV1`

An immutable governance receipt binding:

- one explicit receipt id;
- the exact pending `ProcessEvaluationV1` SHA-256;
- the exact attached `ProcessEvaluationV1` SHA-256;
- the exact attached scientific-support SHA-256;
- ScientificAssertion identity;
- Alignment V2 policy SHA-256;
- evaluation-scope SHA-256;
- model-semantic bridge id and SHA-256;
- the complete canonical human-reviewed selection payload and SHA-256;
- `automatic_acceptance = false`;
- `automatic_attachment = false`.

The new attachment helper delegates the already validated MECH-4D attachment
boundary. It does not discover, route, accept, or attach a policy automatically.

### `AuditableEcosystemExplanationV1`

An additive envelope containing:

- the existing `EcosystemExplanationTraceV1` unchanged;
- ordered exact `ProcessEvaluationV1` canonical identities;
- reviewed support attachment receipts that exactly cover the scientific
  supports carried by the trace.

The envelope fails closed if a receipt points outside the trace, binds the wrong
evaluation SHA, binds a support not present on that evaluation, or leaves a
reviewed support without a receipt.

## Deliberately unchanged contracts

MECH-5B does **not** modify:

- `ProcessScientificSupportV1`;
- `ProcessEvaluationV1`;
- `EcosystemExplanationTraceV1`;
- `material_balance_v1.py`;
- Alignment V1/V2 scientific semantics;
- model-semantic bridge semantics;
- Scientific Foundation V6 or its schema.

This preserves the distinction between scientific support and human governance.

## Nitrogen proof

The real V6 proof replays the same two explicit 1 mg N transformations used by
MECH-5A:

1. reduced inorganic N → oxidized inorganic N;
2. dissolved inorganic N → biological N.

Both supports are attached through exact human-reviewed selections and receive
independent receipts. The core `EcosystemExplanationTraceV1` must retain the
MECH-5A canonical SHA-256 exactly; the new auditable envelope gets its own
additive canonical identity.

No rate, `dt`, kinetics, or automatic extent calculation is introduced.

## Safety boundaries

- local commit only;
- no push;
- no PR #25 mutation;
- no remote branch creation;
- Scientific Foundation V6 opened read-only;
- no ProcessEvaluation persistence;
- no explanation persistence;
- no Schema V7;
- no automatic acceptance;
- no automatic attachment.

## Next boundary

Build the first reproducible nitrogen vertical demonstration artifact from the
auditable explanation envelope, with explicit initial state, explicit extents,
resulting states, scientific assertions, reviewed supports, human attachment
receipts, and rendered "Pourquoi ?" output. RateModel design remains a later,
separate boundary.
