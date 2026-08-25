# EcoBiome — Nitrification Kinetic Evidence Candidates V1

Status: candidate evidence review
Persistence status: NOT part of Scientific Foundation V6
Gate: RATE-1B

## 1. Purpose

This note evaluates candidate literature for the first future nitrogen
RateModel. It does not promote any paper, equation or parameter into
Scientific Foundation V6.

The selected future process is:

```text
ammonia/TAN-N -> nitrite-N
```

in a freshwater attached-biofilm aquaculture biofilter context.

## 2. Candidate A — Mnyoro et al. 2021 — PRIMARY

Mang'era Samwel Mnyoro, Erik Arvin, Renalda N. Munubi, Sebastian W.
Chenyambuga & Lars-Flemming Pedersen.

"Effect of water velocity on ammonium and nitrite removal in pilot scale fixed
bed biofilters." *Aquacultural Engineering* 93 (2021), 102160.

DOI:
https://doi.org/10.1016/j.aquaeng.2021.102160

Open peer-reviewed manuscript:
https://backend.orbit.dtu.dk/ws/files/242604311/1_s2.0_S0144860921000169_main_1_.pdf

### What the paper directly provides

The study used three freshwater pilot-scale RAS with rainbow trout and
fixed-bed biofilters.

Surface TAN removal was defined as:

```text
STr = ([TAN]in - [TAN]out) * Q / Am
```

where:

- TAN is total ammonium nitrogen concentration;
- Q is flow;
- Am is nominal carrier surface area.

At the two highest tested biofilter water velocities, 10.8 and 16.2 m/h, TAN
concentration was positively correlated with surface TAN removal.

The reported first-order surface removal coefficient was:

```text
k1 = 0.45 m/d
```

The paper describes this coefficient as relevant to low, TAN-limited
conditions.

The nominal TAN spike was approximately 1 mg TAN/L.

The paper also reports that reducing water velocity substantially increased
nitrite accumulation, supporting the need to preserve a distinct nitrite
state.

### Observed operating context

The reported acclimatization table shows approximately:

```text
temperature: 19.1–19.6 °C system means
dissolved oxygen: 9.3–10.1 mg/L system means
pH: 7.8–7.9 system means
```

with sufficient alkalinity and high oxygen availability.

These values are **context descriptors**, not yet adopted applicability bounds.

### Candidate mathematical family

For the high-velocity, TAN-limited fixed-bed context:

```text
surface_TAN_flux ≈ k1 * TAN_concentration
```

Dimensional basis:

```text
(m/d) * (g N/m³) = g N/m²/d
```

A future model can convert this flux to `mg N/h` only with explicit biofilter
surface area.

### Why this is PRIMARY but not yet executable

Strengths:

- peer-reviewed;
- full manuscript accessible;
- aquaculture-specific;
- freshwater;
- explicit normalization equation;
- explicit first-order coefficient;
- hydraulic context quantified;
- nitrite response measured.

Remaining review requirements:

- exact admissible TAN range;
- exact interpolation policy between tested velocities;
- whether the coefficient should be represented as one pooled value or as a
  narrower condition-specific value;
- exact definition of nominal versus effective carrier surface area;
- explicit treatment of uncertainty;
- scientific assertion/parameter records in a future Foundation version.

Verdict:

```text
candidate_quality = strong
implementation_ready = false
```

## 3. Candidate B — Malone, Bergeron & Cristina 2006

R. Malone, John J. Bergeron & Chad M. Cristina.

"Linear versus Monod representation of ammonia oxidation rates in oligotrophic
recirculating aquaculture systems." *Aquacultural Engineering* 34 (2006),
214–223.

DOI:
https://doi.org/10.1016/j.aquaeng.2005.08.005

Publisher record:
https://www.sciencedirect.com/science/article/pii/S0144860905001147

### Relevant result

The paper argues that, in the low-substrate mesotrophic/oligotrophic range
examined, a simple zero-intercept linear relation can be more stable than a
Monod fit.

The abstract identifies a calibration range of:

```text
0.1–0.5 g TAN/m³
```

which is numerically equivalent to:

```text
0.1–0.5 mg TAN/L
```

It reports much lower parameter variability for the linear slope than for the
fitted Monod parameters.

### Role in EcoBiome

This is strong conceptual support for evaluating a **low-TAN linear family**
rather than assuming Monod is universally superior.

The accessible record used in RATE-1B does not provide a complete numerical
parameter set suitable for implementation.

Verdict:

```text
candidate_role = kinetic_form_comparison
implementation_ready = false
```

## 4. Candidate C — Zhu & Chen 1999

Songming Zhu & Shulin Chen.

"An experimental study on nitrification biofilm performances using a series
reactor system." *Aquacultural Engineering* 20 (1999), 245–259.

DOI:
https://doi.org/10.1016/S0144-8609(99)00019-9

Publisher record:
https://www.sciencedirect.com/science/article/pii/S0144860999000199

### Relevant result

At 27.2 °C the study reported a mean minimum TAN concentration of 0.07 mg/L
and an empirical single-substrate relationship:

```text
R = 1859 * (S - 0.07) / (S + 1.93)
```

where S is TAN concentration.

### Role in EcoBiome

This is a useful saturation-family candidate and demonstrates that a
non-zero minimum TAN concentration may matter in a steady-state biofilm.

RATE-1B does **not** adopt the coefficient because the accessible abstract
alone is insufficient to verify the full dimensional definition, normalization
basis and applicability domain required by RATE-1A.

Verdict:

```text
candidate_role = saturation_form_candidate
implementation_ready = false
```

## 5. Candidate D — Kinyage & Pedersen 2016

John Peter Hewa Kinyage & Lars-Flemming Pedersen.

"Impact of temperature on ammonium and nitrite removal rates in RAS moving bed
biofilters." *Aquacultural Engineering* 75 (2016), 51–55.

DOI:
https://doi.org/10.1016/j.aquaeng.2016.10.006

DTU record:
https://orbit.dtu.dk/en/publications/impact-of-temperature-on-ammonium-and-nitrite-removal-rates-in-ra/

### Relevant result

Using colonized moving-bed bioelements from a freshwater RAS, surface-specific
TAN removal increased from approximately 0.04 to 0.25 g TAN/m²/d between 6 and
30 °C, then decreased at 36 °C.

The reported temperature coefficient for ammonium oxidation over 6–30 °C was:

```text
theta = 1.079
```

Nitrite oxidation had a different reported coefficient:

```text
theta = 1.054
```

### Role in EcoBiome

This supports:

- separate ammonia- and nitrite-oxidation kinetics;
- explicit temperature applicability;
- rejection of a single universal nitrification temperature response.

RATE-1B does not multiply `theta=1.079` into the Mnyoro fixed-bed coefficient.
The studies use different biofilter configurations and experimental designs.

Verdict:

```text
candidate_role = temperature_response_evidence
implementation_ready_as_modifier = false
```

## 6. Candidate E — Mnyoro et al. 2021 hydraulic effect

The same primary paper also supplies a critical applicability result:

- water velocities below 10.8 m/h significantly reduced TAN removal;
- the first-order TAN relation was observed at 10.8 and 16.2 m/h;
- at low velocity TAN concentration had little explanatory effect on the rate;
- nitrite accumulation increased strongly at the lowest velocity.

Therefore `water_velocity` cannot be treated as irrelevant metadata for this
candidate model family.

## 7. Candidate F — pH / broader kinetic background

T. Le, J. Fettig & G. Meon (2018).

"Kinetics and simulation of nitrification at various pH values of a polluted
river in the tropics." *Ecohydrology & Hydrobiology*.

Consensus record:
https://consensus.app/papers/kinetics-and-simulation-of-nitrification-at-various-ph-le-fettig/968c2582f6c85c5ba8fa91926790dedb/

The paper reports strong pH dependence and distinct behaviour of ammonia and
nitrite oxidation.

It is not a freshwater RAS biofilter parameter source for the first EcoBiome
model. Its role is to prevent omission of pH from applicability reasoning.

## 8. Candidate matrix

| Source | System | Kinetic contribution | Direct first-model use |
|---|---|---|---|
| Mnyoro et al. 2021 | freshwater fixed-bed RAS | surface TAN equation + first-order coefficient + hydraulics | PRIMARY candidate |
| Malone et al. 2006 | oligotrophic RAS | linear vs Monod model-family comparison | supporting |
| Zhu & Chen 1999 | nitrifying aquaculture biofilm | saturation-family equation | alternative |
| Kinyage & Pedersen 2016 | freshwater moving-bed RAS | temperature response | supporting only |
| Le et al. 2018 | tropical river | pH sensitivity | applicability background |

## 9. Scientific no-go

RATE-1B explicitly rejects this synthetic formula:

```text
rate =
    Mnyoro_fixed_bed_k1
    * TAN
    * Kinyage_temperature_modifier
    * Le_pH_modifier
```

No reviewed source in this gate establishes that combined model.

## 10. Evidence promotion requirements

Before Candidate A can become an executable reviewed RateModel, EcoBiome needs
a future Scientific Foundation revision or candidate-review workflow that
captures at least:

```text
kinetic_form
k1 value + unit
TAN quantity definition
surface-area definition
hydraulic applicability
temperature context/domain
DO context/domain
pH context/domain
freshwater context
uncertainty
source lineage
```

and binds them to the exact future RateModel parameter set.

## 11. RATE-1B verdict

```text
granularity = two_step
first_kinetic_process = ammonia/TAN-N -> nitrite-N
primary_evidence_candidate = Mnyoro et al. 2021 fixed-bed first-order surface TAN model
numeric_model_approved = false
cross_paper_parameter_splicing = forbidden
scientific_foundation_v6_write = false
```
