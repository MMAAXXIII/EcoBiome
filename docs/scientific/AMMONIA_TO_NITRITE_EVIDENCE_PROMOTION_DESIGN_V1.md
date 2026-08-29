# EcoBiome — Ammonia-to-Nitrite Scientific Evidence Promotion Design V1

Status: adopted promotion design
Gate: RATE-2A
Vertical: G7A predictive nitrogen
Persistence status: no Scientific Foundation write

## 1. Purpose

RATE-1F can now represent, with an explicit elemental-N extent:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
nitrite_nitrogen       -> nitrate_nitrogen
```

RATE-2A defines the scientific evidence package that must exist before
EcoBiome may attach reviewed support to the first process and before any
concrete TAN-removal RateModel may emit a numerical rate.

RATE-2A does **not** promote evidence into Scientific Foundation V6.

## 2. Evidence roles must remain separate

The first predictive process needs distinct reviewed evidence roles:

```text
mechanism
kinetic_form
kinetic_parameter
applicability_domain
```

These roles answer different questions.

### mechanism

Does aerobic nitrification support the directional process:

```text
ammonia/ammonium nitrogen -> nitrite nitrogen
```

as a first oxidation step?

### kinetic_form

Does a particular empirical system support the mathematical relation chosen
for a RateModel?

Example candidate:

```text
surface_TAN_removal_flux = k1 * TAN_concentration
```

### kinetic_parameter

What exact numerical parameter, unit, normalization basis and source lineage
belong to that mathematical form?

### applicability_domain

Under what experimental/system conditions may that form and parameter be
applied?

A mechanism paper cannot silently authorize a biofilter coefficient.
A biofilter coefficient cannot silently authorize a universal nitrification
mechanism or environmental response function.

## 3. Mechanism evidence candidate

Two independent 2015 Nature studies on complete nitrification explicitly
describe nitrification as oxidation of ammonia through nitrite to nitrate.

Candidate sources:

1. van Kessel et al. (2015),
   "Complete nitrification by a single microorganism",
   Nature 528, 555–559.
   DOI: https://doi.org/10.1038/nature16459

2. Daims et al. (2015),
   "Complete nitrification by Nitrospira bacteria",
   Nature 528, 504–509.
   DOI: https://doi.org/10.1038/nature16461

A more recent review also states that ammonia-oxidising archaea oxidize
ammonia to nitrite:

Wright & Lehtovirta-Morley (2023),
"Nitrification and beyond: metabolic versatility of ammonia oxidising archaea",
The ISME Journal 17, 1358–1368.
https://doi.org/10.1038/s41396-023-01467-0

### Promotion interpretation

These sources support the **directional first nitrification step** without
requiring EcoBiome to assert that one microbial guild is exclusively
responsible.

The candidate mechanism assertion should therefore be process-level, not
organism-exclusive.

Candidate semantic statement:

```text
Under aerobic nitrification, ammonia/ammonium nitrogen can be oxidized to
nitrite nitrogen as the first oxidation step of nitrification.
```

The final persisted wording must be reviewed against the exact source text and
EcoBiome entity semantics.

## 4. Kinetic-form candidate — Mnyoro et al. 2021

Primary empirical source:

Mang'era Samwel Mnyoro, Erik Arvin, Renalda N. Munubi,
Sebastian W. Chenyambuga & Lars-Flemming Pedersen (2021).

"Effect of water velocity on ammonium and nitrite removal in pilot scale fixed
bed biofilters." Aquacultural Engineering 93, 102160.

DOI:
https://doi.org/10.1016/j.aquaeng.2021.102160

Peer-reviewed accepted manuscript:
https://backend.orbit.dtu.dk/ws/portalfiles/portal/242604311/1_s2.0_S0144860921000169_main_1_.pdf

### Reported normalization

The paper defines surface TAN removal rate as:

```text
STr = ([TAN]in - [TAN]out) * Q / Am
```

with:

```text
STr   g N m^-2 d^-1
TAN   g N m^-3
Q     m^3 d^-1
Am    nominal carrier surface area, m^2
```

The first-order regression uses calculated surface TAN removal rate versus mean
biofilter TAN concentration at the two highest tested water velocities.

### Tested hydraulic points

```text
1.4 m/h
5.4 m/h
10.8 m/h
16.2 m/h
```

A significant positive TAN-concentration / surface-removal correlation was
reported at:

```text
10.8 m/h
16.2 m/h
```

but not at the two lower velocities.

Therefore any first-order RateModel derived from this experiment must treat
hydraulic condition as part of its applicability evidence.

## 5. Critical parameter-unit conflict

Mnyoro et al. 2021 contains an internal unit inconsistency for the reported
first-order coefficient.

The published abstract and one sentence in the results text report:

```text
0.45 m h^-1
```

while the conclusion and the Fig. 4 caption report:

```text
0.45 m d^-1
```

The paper's own dimensional definition gives:

```text
(STr unit) / (TAN concentration unit)
=
(g N m^-2 d^-1) / (g N m^-3)
=
m d^-1
```

Therefore `m d^-1` is dimensionally consistent with Equation (1) and the
Fig. 4 axes, while `m h^-1` is not.

RATE-2A does **not** silently correct the publication.

Promotion status:

```text
kinetic_parameter_value_candidate = 0.45
kinetic_parameter_unit = CONFLICT_UNRESOLVED
kinetic_parameter_promotable = false
```

A future reviewer must explicitly resolve and document this discrepancy before
the parameter can enter a reviewed Scientific Foundation revision.

## 6. Applicability evidence versus observed context

RATE-2A distinguishes experimentally varied applicability factors from
conditions merely observed during the trial.

### Experimentally varied

Water velocity was deliberately tested at four values:

```text
1.4, 5.4, 10.8, 16.2 m/h
```

The first-order relation was observed at the two highest velocities.

### Observed/acclimatization context

The three systems were reported around:

```text
temperature        19.1–19.6 °C system means
dissolved oxygen    9.3–10.1 mg/L system means
pH                   7.8–7.9 system means
alkalinity          185–222 mg/L CaCO3 system means
```

The NH4Cl spike targeted approximately:

```text
1 mg TAN/L
```

These contextual values must **not** be converted into experimentally
validated response curves or hard universal applicability bounds.

They can be persisted as context/provenance constraints, but they do not
authorize:

```text
temperature correction
pH correction
DO correction
alkalinity correction
```

## 7. Surface-area semantics

The Mnyoro normalization uses:

```text
Am = nominal surface area of carrier elements
```

A future RateModel therefore needs an explicit quantity representing the same
surface-area semantics.

EcoBiome must not silently substitute:

```text
geometric filter footprint
external tank area
manufacturer "protected surface area"
effective active biofilm area
generic aquarium filter area
```

for the paper's `Am` basis.

The future parameter/model package must bind the RateModel scaling quantity to
an exact reviewed surface-area definition.

## 8. TAN semantics

Mnyoro's Equation (1) uses TAN concentration on a nitrogen basis.

RATE-1D/RATE-1E already define:

```text
total_ammonia_nitrogen inventory = mg N
derived TAN concentration         = mg N/L
```

Before promotion, the evidence reviewer must confirm that the experimental TAN
quantity is semantically compatible with the EcoBiome
`total_ammonia_nitrogen` projection.

No name-only mapping is sufficient.

## 9. Candidate evidence records

RATE-2A recommends a future evidence-review package containing at least these
logical records.

### A. Mechanism support

```text
role:
  mechanism

process:
  ammonia_oxidation_to_nitrite_extent_v1

claim:
  ammonia/ammonium nitrogen can be oxidized to nitrite nitrogen during
  aerobic nitrification

sources:
  van Kessel et al. 2015
  Daims et al. 2015
```

### B. Kinetic-form support

```text
role:
  kinetic_form

model family:
  first-order surface TAN removal

relation:
  STr proportional to TAN concentration

system:
  freshwater pilot-scale fixed-bed RAS

hydraulic evidence:
  positive relation at 10.8 and 16.2 m/h
```

### C. Kinetic-parameter candidate

```text
role:
  kinetic_parameter

parameter_id:
  surface_tan_first_order_coefficient

value:
  0.45

unit:
  BLOCKED_BY_SOURCE_CONFLICT

normalization:
  surface TAN removal / TAN concentration

status:
  candidate_not_promotable
```

### D. Applicability support

```text
role:
  applicability_domain

required system identity:
  freshwater attached fixed-bed aquaculture biofilter

tested hydraulic evidence:
  10.8 and 16.2 m/h for the first-order regression

context only:
  temperature, DO, pH, alkalinity and nominal TAN spike conditions
```

## 10. No cross-paper parameter construction

Kinyage & Pedersen (2016) remains useful evidence that temperature affects
ammonium and nitrite oxidation differently in moving-bed RAS biofilters.

It does **not** authorize multiplying a Mnyoro fixed-bed coefficient by a
Kinyage moving-bed temperature coefficient.

Malone et al. (2006) supports consideration of a low-TAN linear family in
oligotrophic RAS.

It does **not** provide the Mnyoro fixed-bed coefficient or resolve the Mnyoro
unit conflict.

## 11. Promotion gates

A future scientific promotion may proceed in stages.

### Mechanism promotion

May proceed when:

```text
exact source passages reviewed
claim wording frozen
entities/bases verified
process scope verified
review event recorded
```

### Kinetic-form promotion

May proceed when:

```text
Equation (1) semantics verified
regression basis verified
TAN quantity semantics verified
surface-area normalization verified
hydraulic applicability encoded
```

### Kinetic-parameter promotion

Must remain blocked until:

```text
0.45 unit conflict explicitly resolved
resolution rationale recorded
reviewer identity recorded
source lineage retained
```

## 12. RATE-2A verdict

```text
mechanism_evidence_candidate_ready_for_review = true
kinetic_form_candidate_ready_for_review = true
kinetic_parameter_value_identified = true
kinetic_parameter_unit_resolved = false
numeric_rate_model_authorized = false
scientific_foundation_v6_write = false
```

The correct next action is evidence review/promotion design completion, not
RateModel implementation.
