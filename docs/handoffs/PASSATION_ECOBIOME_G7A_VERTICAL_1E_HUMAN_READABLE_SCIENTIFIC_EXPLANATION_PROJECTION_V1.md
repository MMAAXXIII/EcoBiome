# PASSATION - EcoBiome G7A VERTICAL-1E - Human-readable Scientific Explanation Projection V1

**Gate:** `ECOBIOME_G7A_VERTICAL_1E_HUMAN_READABLE_SCIENTIFIC_EXPLANATION_PROJECTION_V1_LOCAL`

**Precondition:** `agent/g7a-directional-nitrogen-semantic-stack-v1@17049c1687d4a8a130e120d7fb5cd123c350912f`

## Trigger

The VERTICAL-1D browser smoke-test validated the UI plumbing but exposed two
product/scientific presentation problems:

1. the main "Pourquoi ?" block surfaced internal process IDs, epistemic enum
   names, receipts, selections and SHA values instead of a human explanation;
2. the four N4 categories were displayed side-by-side in a way that could imply
   four globally independent additive physical pools, despite the reviewed
   process-scoped bridge design.

## Architectural response

Add a presentation-only contract:

`HumanReadableNitrogenExplanationV1`

It consumes the already-frozen `NitrogenVerticalDemonstrationV1` canonical
payload and validates the exact reviewed assertion, bridge, selection and
receipt identities before emitting user-facing language.

It does not alter:

- `ProcessEvaluationV1`;
- `ProcessScientificSupportV1`;
- any Alignment V1/V2 contract;
- model-semantic bridges;
- material balance;
- the VERTICAL-1A artifact;
- Scientific Foundation V6.

## Human projection

For each reviewed mechanism the projection exposes:

- one process-scoped title;
- source and target values before/after;
- explicit extent;
- what happens in the deterministic scenario;
- what the reviewed scientific support establishes;
- what the scenario still imposes;
- technical provenance in a separate nested payload.

The UI uses two mechanism panels rather than four globally adjacent pool cards.

A visible abstraction note states that the categories are process-scoped model
views and must not be naively added as four independent physical stocks.

## Scientific wording boundary

The projection states only what existing reviewed identities support:

- oxidation: ammonium -> nitrate, represented in the N4 oxidation scope as
  reduced inorganic N -> oxidized inorganic N;
- assimilation: ammonium -> L-glutamine biological nitrogen, represented in the
  N4 assimilation scope as dissolved inorganic N -> biological N.

The explicit 1 mg N extents remain scenario inputs. The projection explicitly
states that support for mechanism/direction is not yet a kinetic prediction.

## UI boundary

The main "Pourquoi ?" section becomes human-readable. Raw technical trace,
assertion/bridge/selection/receipt identifiers and SHAs remain available only
inside the collapsed technical provenance section.

## Non-goals

- no RateModel;
- no dt;
- no kinetic parameter;
- no persistence;
- no V6 write;
- no Schema V7;
- no remote write.

## Next boundary

Run a second browser smoke-test of the revised `Cycle de l'azote` view. If a
non-developer can distinguish mechanism, reviewed scientific basis, explicit
scenario extent, and model limitation without inspecting technical provenance,
the vertical is ready for RateModel V1 design.
