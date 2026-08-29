# EcoBiome — G7A RATE-4G candidate handoff

## Scope

Concrete TAN -> nitrite-N instantaneous rate model candidate derived from the
RATE-4F shadow authorization.

This candidate is validated only in a disposable `git archive HEAD` shadow.
No real repository write, Git write, Scientific Foundation write, CAS write or
active-snapshot mutation is authorized by RATE-4G.

## Scientific boundary

Primary source: Mnyoro et al. 2021
DOI: `10.1016/j.aquaeng.2021.102160`

Reviewed kinetic form:

`surface_TAN_flux = k1 * TAN_concentration`

Reviewed/adjudicated parameter:

`k1 = 0.45 m/d`

The original source conflict (`m/h` versus `m/d`) remains explicit in the
review provenance. No official erratum is claimed.

## Exact execution guard

The candidate emits a numeric instantaneous rate only when all of the
following are true:

- freshwater;
- fixed-bed attached biofilm;
- carrier exactly `RK Bioelements Heavy`;
- mature colonized media;
- elevation/pore velocity measured in the media bed;
- velocity exactly `10.8` or `16.2 m/h`;
- at least 3 days since hydraulic change;
- `0 <= TAN <= 1.0 mg N/L`;
- temperature `19.1–19.6 °C`;
- dissolved oxygen `9.3–10.1 mg/L`;
- pH `7.8–7.9`;
- alkalinity `185–222 mg/L as CaCO3`;
- nominal active carrier surface area explicitly present and positive.

The environmental intervals are execution-policy fences over the reported
central context; they are not universal biological tolerance limits.

## Numeric relation

`rate_mg_N_h = 0.45 * TAN_mg_N_L * nominal_active_carrier_area_m2 * 1000 / 24`

No temperature, pH, oxygen, Monod or other cross-paper modifier is used.

## Explicit exclusions

- no state mutation;
- no `dt`;
- no rate-to-extent integration;
- no MaterialBalance invocation;
- no production/runtime activation;
- no live aquarium prediction;
- no portable filter-media generalization;
- no interpolation between 10.8 and 16.2 m/h;
- no new scientific-support persistence.

## Next boundary

`RATE-4H_CONCRETE_TAN_TO_NITRITE_RATE_MODEL_CANDIDATE_HUMAN_REVIEW_AND_REPO_INTEGRATION_AUTHORIZATION`

## RATE-4H human-review correction incorporated in R5

RATE-4H review identity:

`90f6c07e34991b03dfbdc5668923474cd22647db3c1b3475e60821d522101da3`

The R4 candidate was held from real-repository integration because the support
bundle validated only role names. R5 additionally binds each
`RateScientificSupportV1` to the exact canonical RATE-4F reviewed identity.

A same-role replacement support with a different canonical identity must now
fail closed before any numerical evaluation can be constructed.

