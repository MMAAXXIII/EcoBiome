# EcoBiome N4 — Aquarium / Pond Vertical Slice Local Implementation V1

Gate target:
`ECOBIOME_N4_AQUARIUM_POND_VERTICAL_SLICE_LOCAL_IMPLEMENTATION_VALIDATED`

Baseline:
- branch `main`
- HEAD `156cffd68bdecb4f831ad37028ce499d0979d0da`
- Scientific Foundation physical Schema V6 unchanged
- Collector compatibility schema 2 unchanged
- Projection V1.1 unchanged

## Scope

This implementation adds the first executable universal ecosystem vertical
slice without introducing Schema V7.

The same generic profile contracts represent an aquarium and a small pond:
physical structures, environment zones, functional systems, biological
populations, material components and resource flows.

Dynamic scientific values remain outside topology and are represented by
canonical state quantities with an explicit epistemic basis.

## Numeric boundary

Canonical N4 state/process payloads use normalized decimal strings.
Native floats are rejected by the canonical contracts.

A canonical typed decimal object is always exactly
`{"type":"decimal","value":"..."}`. Units are stored by the enclosing
quantity object rather than inserted into the typed-decimal object. This
preserves the Scientific Foundation V1.1 serialization invariant.

Legacy `Observation` values are accepted only through the explicit
`canonicalize_observation_v1` compatibility adapter. A legacy native float is
converted deterministically at that boundary and produces the warning
`legacy_native_float_canonicalized`.

## First deterministic processes

### Well-mixed water exchange V1

Applies exact conservation of dissolved material inventory under:
- an explicit current water volume;
- explicit removed and replacement volumes;
- the explicit assumption that the water zone is well mixed before removal;
- explicit replacement composition for every tracked dissolved material.

Unknown replacement composition is a hard failure, never implicit zero.

### Nitrogen transformation extent V1

Moves an explicit elemental-N mass extent between admitted nitrogen pools.
It does not calculate or infer a biological rate.

Initial admitted transformations:
- `reduced_inorganic_nitrogen -> oxidized_inorganic_nitrogen`
- `dissolved_inorganic_nitrogen -> biological_nitrogen`

The evaluator enforces exact elemental-N conservation and rejects an extent
larger than the source inventory.

N4 V1 deliberately does not claim `mechanism_supported`, even when exact
ScientificAssertion references are supplied, because a reviewed
process-to-assertion semantic-alignment seam does not yet exist. Those refs
remain auditable evidence links and the result stays `support_missing`.

This restriction is enforced at the ProcessEvaluationV1 contract boundary:
`mechanism_supported` is not an admitted N4 V1 support status, so callers
cannot bypass the evaluator by directly constructing a promoted evaluation.
Without refs, an assumed extent remains `scenario_hypothesis`. Exact
arithmetic never promotes an assumption into scientific truth.

## Process parameter and intervention audit binding

Every `ProcessEvaluationV1` now freezes a canonical `parameters` object.

For a water exchange, the evaluation stores both the complete canonical
`WaterExchangeInterventionV1` payload and its canonical SHA-256. This binds
removed/replacement volumes, replacement composition, epistemic bases and the
intervention identity to the process evaluation instead of leaving them as
free external references.

For a nitrogen transformation, the evaluation freezes the requested extent,
its supplied unit, its normalized elemental-N base extent, source/target pools,
zone and extent basis.

## Explanation trace

`EcosystemExplanationTraceV1` joins a contiguous sequence of deterministic
process evaluations and preserves separately:
- observation references;
- intervention references;
- process evaluations;
- ScientificAssertion audit references when supplied;
- epistemic basis categories from both process parameters and the affected
  input-state quantities;
- assumptions;
- warnings;
- unknowns.

Observation references are derived from observation bases actually used by
the starting state/process parameters. Intervention references are derived
from interventions cryptographically bound inside process evaluations.
Caller-supplied reference lists must exactly match those derived references.

The legacy `KnowledgeRegistry` reasoning engines remain unchanged.

## Persistence and compatibility

No N4 persistence table is added.
No Scientific Foundation table or index is changed.
No Collector contract is changed.
No Semantic Candidate or Projection V1.1 contract is changed.
No provider/model call is introduced.

Legacy `WaterBody`, `WorldState`, events and observations remain available.

## Validation policy

The implementation launcher writes these files only after a disposable
`git archive HEAD` shadow copy passes:
- Python compilation;
- Ruff;
- Mypy;
- N4 targeted tests;
- N3/Persistence/Collector regression tests;
- full pytest;
- Schema V6 identity checks.

After local write, the same validation is repeated. A post-write failure
triggers byte-for-byte rollback of modified tracked files and deletion of all
new N4 paths.

The runtime audit ZIP is the authority for the final validation result.

## Sensitive boundaries

This implementation does not stage, commit, push, merge, edit GitHub metadata
or call a provider.

Exact staging requires a separate explicit authorization.


## R7 independent-audit hardening

- public explanation-trace constructors validate state SHA identities,
  process-evaluation ordering, assertion-ref closure and epistemic categories;
- the JSON profile loader rejects scalar-to-string coercion for identifiers
  and references;
- direct `ProcessEvaluationV1` construction cannot claim
  `mechanism_supported` in N4 V1.
