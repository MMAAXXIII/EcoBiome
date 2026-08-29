# PASSATION ECOBIOME — G7A RATE-5L

## Dormant nitrite zero-order evidence candidate implementation V1

**Gate:** `RATE-5L_DORMANT_NITRITE_ZERO_ORDER_EVIDENCE_CANDIDATE_IMPLEMENTATION_V1`  
**Base:** `main@a6931417bb02644157bac27a159a6dad4da060e1`  
**Branch:** `agent/g7a-rate-5l-nitrite-zero-order-evidence-candidate-v1`  
**Status:** `PASS_IMPLEMENTED_CI_GREEN_PENDING_HUMAN_REVIEW`

## 1. Purpose

RATE-5L preserves a bounded second-stage nitrification evidence candidate for
`nitrite_oxidation_to_nitrate` without promoting it to an executable
`RateModelV1`.

The exact zero-order nitrite constant is kept as evidence only:

- value: `139`
- unit: `g NO2-N/m3-media/d`
- basis: media volume
- kinetic order: zero order

No ecosystem rate is calculated and no state is mutated.

## 2. Source identities

### Exact numeric source

Associated SSRN preprint:

- SSRN id: `4911049`
- local reviewed artifact: `ssrn-4911049.pdf`
- SHA-256: `2e9af660d0121c9ace5ec469716400458b4994062f7a3ce97a10589e008063e8`
- peer reviewed: `false`
- exact parameter observed: `true`

The preprint explicitly labels itself as not peer reviewed. In its results it
reports zero-order nitrite kinetics of `139, 391, 458, and 479 g/m3/d` for
plastic beads, ceramic beads, coconut shells, and polyurethane foam,
respectively. Its methods define zero-order kinetics from concentration values
above `1.0 mg N/L`.

### Peer-reviewed continuity source

Final publication:

- Mnyoro, M. S.; Munubi, R. N.; Chenyambuga, S. W.; Pedersen, L.-F. (2024)
- *Comparison of four different types of biomedia during start-up in a
  recirculating aquaculture system with rainbow trout*
- Journal of Water Process Engineering, volume 68, article 106549
- DOI: `10.1016/j.jwpe.2024.106549`
- peer reviewed: `true`
- exact `139` parameter independently verified in final article body by
  RATE-5L: `false`

Therefore the final paper is represented only as publication-continuity
evidence. It is not used to impersonate an exact reviewed numeric support.

## 3. Source re-audit correction relative to RATE-5K planning

RATE-5K planning provisionally referenced `RK Bioelements Heavy` for the
plastic carrier. RATE-5L re-audited the attached primary preprint before
writing code.

The source-supported description is:

`15 mm commercial polypropylene plastic beads`

The paper also shows and labels the material as `Plastic beads` in Figure 2.
It does not establish the exact product identity `RK Bioelements Heavy` in the
available source text or figure.

RATE-5L therefore **does not** carry the provisional RK identity forward.
Instead it freezes:

`15_mm_commercial_polypropylene_plastic_beads`

and tests that `RK_Bioelements_Heavy`, generic polypropylene media,
polyurethane foam, and other carriers fail closed.

This correction prevents cross-paper carrier identity stitching.

## 4. Experimental context preserved

The evidence candidate preserves these bounded context facts:

- freshwater RAS context;
- twelve upflow biofilters with media fixed between perforated plates;
- fixed-bed upflow interpretation;
- `15 mm commercial polypropylene plastic beads`;
- 20 L media filling per biofilter;
- water velocity exactly `12 m/h`;
- water flow `1500 L/h`;
- air flow `5.0 L/min`;
- six-week startup with fish followed by kinetic tests during weeks 7-8;
- nitrite spike around `5 mg/L` for the kinetic assay;
- zero-order threshold strictly above `1.0 mg NO2-N/L`.

The reported study-level RAS envelope is preserved conservatively as an
applicability fence:

- temperature: `15.0–16.8 °C`
- dissolved oxygen: `9.2–10.8 mg/L`
- pH: `7.0–7.4`

These ranges are not represented as universal biological tolerances and are
not claimed to be exact kinetic-assay-specific bounds.

Alkalinity is retained only as context:

- mean: `125 mg/L as CaCO3`
- SD: `8.6 mg/L as CaCO3`
- hard guard: `false`

## 5. Implementation boundary

RATE-5L adds exactly four files:

1. `src/ecobiome/simulation/mnyoro2024_nitrite_zero_order_evidence_candidate_v1.py`
2. `tests/test_mnyoro2024_nitrite_zero_order_evidence_candidate_v1.py`
3. `tests/fixtures/rate_models/mnyoro2024_nitrite_zero_order_evidence_candidate_v1.json`
4. `docs/handoffs/PASSATION_ECOBIOME_G7A_RATE_5L_DORMANT_NITRITE_ZERO_ORDER_EVIDENCE_CANDIDATE_IMPLEMENTATION_V1.md`

No pre-existing source file is modified.

The implementation intentionally does **not** import or construct:

- `RateScientificSupportV1`
- `RateParameterV1`
- `RateModelDefinitionV1`
- `RateEvaluationV1`
- `EcosystemStateV1`
- `MaterialBalance`

The candidate exposes documentary parameter identity and evidence-context
assessment only.

## 6. Epistemic fail-closed invariants

The evidence bundle rejects all of the following:

- marking the SSRN preprint as peer reviewed;
- removing `exact_parameter_observed=True` from the preprint role;
- claiming that the final publication directly exposes the exact `139`
  parameter;
- changing the frozen preprint artifact SHA-256;
- changing the final publication DOI;
- assigning either source to the wrong role;
- supplying a frozen final-body artifact SHA that RATE-5L does not possess.

The candidate itself hardcodes:

- `execution_authorized = false`
- `production_authorized = false`

The numeric parameter is not constructor-configurable.

## 7. Applicability behavior

The evidence-context assessment returns only:

- `within_evidence_context`
- `outside_evidence_context`

It deliberately does not use the `RateApplicabilityResultV1` status
`applicable`.

Blocking fences include:

- water type;
- fixed-bed upflow reactor mode;
- exact source-supported carrier description;
- exact `12 m/h` study velocity;
- nitrite strictly `> 1.0 mg NO2-N/L`;
- reported temperature, dissolved-oxygen, and pH study envelope;
- source-specific maturity context.

No interpolation or portable carrier generalization is allowed.

## 8. Explicitly absent capabilities

RATE-5L contains no:

- numerical ecosystem rate evaluation;
- `rate_decimal` output;
- `dt`, duration, elapsed time, time-step, or timestep;
- rate-to-extent integration;
- output-state identity;
- state mutation;
- MaterialBalance invocation;
- Scientific Foundation persistence;
- active pointer mutation;
- runtime policy mutation;
- production activation.

## 9. Validation and test matrix

The dedicated test file covers:

- frozen fixture identities;
- canonical SHA determinism;
- parameter value/unit/basis identity sensitivity;
- exact preprint SHA rejection on mismatch;
- exact final DOI rejection on mismatch;
- anti-escalation checks for preprint/final publication roles;
- no hidden context defaults;
- strict `>1.0 mg/L` zero-order threshold;
- exact `12 m/h` hydraulic fence;
- inclusive environmental envelope boundaries;
- fail-closed carrier/reactor/maturity checks;
- explicit rejection of `RK Bioelements Heavy` substitution;
- absence of execution/integration fields;
- absence of `evaluate_*` numerical rate callables;
- absence of imports from generic RateModel contracts.

A temporary isolated harness using the repository canonical serialization
behavior executed the dedicated test file before the GitHub CI run:

`34 passed`

GitHub Python CI subsequently validated the complete repository after the
RATE-5L Ruff corrections:

- Ruff: `All checks passed!`
- mypy: `Success: no issues found in 262 source files`
- pytest: `735 passed, 2 skipped`

The companion Frontend CI also completed successfully. The RATE-5L repository
head therefore has green Python and frontend CI before human review.

## 10. Control-plane statement

RATE-5L does not touch the Scientific Foundation control plane.

Expected unchanged identities remain those frozen at RATE-5B:

- active scientific snapshot database SHA-256:
  `2bc6d8524c529ebb52ce5c5a9b3b44f879dcdf9b62b5d6c8d2153443259dfde9`
- active pointer file SHA-256:
  `1fc84f79ed15dc68acebff454f494c90538664ce058173e33e80bf9e144e8014`
- runtime policy file SHA-256:
  `5f3a1afc0a9290882bb49e95e294786ba3be5af0ee8d7453141a5f184a2e64c5`

Remote GitHub implementation cannot independently certify the user's local
external pointer/policy files; local post-merge verification remains required.

## 11. Gate result

Current state after source re-audit, implementation, and CI validation:

```text
ECOBIOME_G7A_RATE_5L
DORMANT_NITRITE_ZERO_ORDER_EVIDENCE_CANDIDATE_IMPLEMENTATION_V1

implementation = COMPLETE
source_reaudit = PASS_WITH_CARRIER_IDENTITY_CORRECTION
dedicated_isolated_tests = 34_PASS
repository_ruff = PASS
repository_mypy = PASS_262_SOURCE_FILES
repository_pytest = 735_PASS_2_SKIPPED
frontend_CI = PASS
repository_CI = PASS
human_review = PENDING
merge_authorized = FALSE
production_activation = FALSE
scientific_foundation_mutation = FALSE
control_plane_mutation = FALSE
```

RATE-5L is `PASS_IMPLEMENTED_CI_GREEN_PENDING_HUMAN_REVIEW`. Merge remains a
separate explicit human decision.
