# PASSATION - EcoBiome G7A VERTICAL-1C - Nitrogen Explanation UI V1

**Gate:** `ECOBIOME_G7A_VERTICAL_1C_NITROGEN_EXPLANATION_UI_V1_LOCAL`
**Precondition:** `agent/g7a-directional-nitrogen-semantic-stack-v1@c98a4de8c73aae608a25a92762dc3f3ee112d0f5`

## Decision

Do not start RateModel yet.

VERTICAL-1B proves the first vertical from the CLI, but the representation
remains too technical to evaluate the product promise "Pourquoi ça marche ?".
EcoBiome already has a canonical React/Bolt frontend and local HTTP API, so the
next smallest product-learning step is to expose the exact same frozen vertical
visually.

## Scope

Add one navigation entry and one view: `Cycle de l'azote`.

The view shows initial/final nitrogen pools, the two explicit 1 mg N
transformations, the reviewed explanation, a clear non-predictive warning, and
collapsible provenance.

## API

`GET /api/nitrogen-demo`

The endpoint rebuilds the exact VERTICAL-1A artifact through the VERTICAL-1B
read-only runtime. `ECOBIOME_SCIENTIFIC_FOUNDATION_V6` can override the exact
local V6 path.

## Non-goals

No RateModel, no dt, no time slider, no persistence, no V6 write, no Schema V7,
no remote write.

## Next boundary

Run the integrated frontend and perform a visual/usability smoke test. Only
after that test should RateModel V1 design begin.
