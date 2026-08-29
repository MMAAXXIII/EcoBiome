# PASSATION - EcoBiome G7A VERTICAL-1A - Reproducible Nitrogen Demonstration V1

**Gate:** `ECOBIOME_G7A_VERTICAL_1A_REPRODUCIBLE_NITROGEN_DEMONSTRATION_V1_LOCAL`
**Precondition:** `agent/g7a-directional-nitrogen-semantic-stack-v1@d412811bdc99c70e09e5bf069650be8f53c8c2f7`

## Purpose

Turn the validated MECH-5B auditable explanation envelope into the first
reproducible, inspectable nitrogen vertical demonstration artifact.

This boundary is deliberately vertical-specific. It does not introduce a generic
demonstration framework before a second ecological vertical exists.

## Artifact contract

`NitrogenVerticalDemonstrationV1` binds:

- the exact initial, intermediate, and final `EcosystemStateV1` payloads and SHAs;
- the exact two reviewed `ProcessEvaluationV1` identities;
- explicit process extent values and their epistemic bases;
- the exact `AuditableEcosystemExplanationV1`;
- the two reviewed support attachment receipts;
- the exact Scientific Foundation V6 snapshot identity;
- explicit model-boundary flags stating that no rate, dt, kinetics, or forecast
  is present.

The canonical JSON artifact is self-contained for the deterministic scenario and
governance provenance carried by MECH-5B. A Markdown rendering provides the
first human-readable vertical demonstration.

## Frozen V1 scenario

The real V6 proof replays the established G7A scenario:

1. reduced inorganic N -> oxidized inorganic N, explicit extent 1 mg N;
2. dissolved inorganic N -> biological N, explicit extent 1 mg N.

The same MECH-5A core explanation SHA and MECH-5B auditable explanation SHA
must be preserved.

## Safety boundary

No existing simulation, support, alignment, bridge, or explanation contract is
modified. Scientific Foundation V6 is read-only. No ProcessEvaluation,
explanation, or demonstration artifact is persisted to V6. No Schema V7 is
created. No rate model is introduced. No remote Git write is performed.

## Runtime outputs

The gate bundle includes:

- `NITROGEN_VERTICAL_DEMONSTRATION_V1.json`;
- `NITROGEN_VERTICAL_DEMONSTRATION_V1.md`;
- real-V6 reproducibility report;
- test/lint/type-check logs;
- DB and Git before/after proofs.

## Next boundary

After this artifact is validated, expose the demonstration through one minimal
local product surface (prefer the existing CLI unless its current architecture
makes that inappropriate), while keeping extents explicit. RateModel design
remains a later boundary after the first user-visible vertical is operational.
