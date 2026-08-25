# Nitrogen kinetic modelling boundary — research note V1

Status: architecture input only
Persistence status: NOT part of Scientific Foundation V6
Purpose: identify evidence requirements before RateModel implementation

## Existing EcoBiome evidence

The frozen G7A vertical has two reviewed scientific assertions:

1. oxidation mechanism/direction;
2. assimilation mechanism/direction.

These assertions are sufficient for the existing `mechanism` support role.
They do not contain a reviewed numerical kinetic law or reviewed kinetic
parameters.

## External background consulted for RATE-1A

The following literature was consulted only as **design background**. It is not
automatically promoted to EcoBiome Scientific Foundation evidence.

### Temperature in RAS biofilters

J. Kinyage & Lars-Flemming Pedersen (2016), *Aquacultural Engineering* 75,
51–55, "Impact of temperature on ammonium and nitrite removal rates in RAS
moving bed biofilters".

Consensus record:
https://consensus.app/papers/impact-of-temperature-on-ammonium-and-nitrite-removal-kinyage-pedersen/64f9adb2c6e054089d0f55c361f54e74/

Design implication: rate behaviour and applicability can depend strongly on
temperature, and ammonia- and nitrite-oxidation should not be assumed to have
identical responses.

### pH and two-step nitrification

T. Le, J. Fettig & G. Meon (2018), *Ecohydrology & Hydrobiology*, "Kinetics and
simulation of nitrification at various pH values of a polluted river in the
tropics".

Consensus record:
https://consensus.app/papers/kinetics-and-simulation-of-nitrification-at-various-ph-le-fettig/968c2582f6c85c5ba8fa91926790dedb/

Design implication: pH can materially alter nitrifier activity, and the
one-step simplification must not be treated as equivalent to a two-step
kinetic model.

### Monod-type kinetic parameters and oxygen

Miao Zhang, Meng Yu, Yixin Wang, Chengda He, Jingjin Pang & Jun Wu (2019),
*Science of the Total Environment* 697, 134101, "Operational optimization of a
three-stage nitrification moving bed biofilm reactor (NMBBR) by obtaining
enriched nitrifying bacteria: Nitrifying performance, microbial community, and
kinetic parameters."

Consensus record:
https://consensus.app/papers/operational-optimization-of-a-threestage-nitrification-zhang-yu/b84ccada1a0e54dcb2e40132c492c4df/

Design implication: substrate and oxygen half-saturation parameters are
model-specific quantities; they cannot be introduced as anonymous universal
constants.

## Evidence acquisition requirements

Before a concrete reviewed nitrification RateModel can be activated, EcoBiome
must review evidence for the exact chosen model formulation, including:

- mathematical kinetic form;
- definition of every variable;
- definition and units of every parameter;
- organism / biofilm / reactor context;
- temperature range;
- pH range;
- dissolved oxygen range;
- substrate range;
- normalization basis (volume, area, biomass, etc.);
- freshwater/salinity domain if relevant;
- whether the model describes ammonia oxidation, nitrite oxidation, or a
  lumped net nitrification rate;
- uncertainty or variability reported by the source.

A parameter from one reactor configuration must not be silently transplanted
into another domain solely because both concern nitrification.

## Required epistemic rule

A reviewed mechanism assertion answers:

```text
Can this transformation occur, and in what direction?
```

A reviewed kinetic assertion must separately answer:

```text
Under these defined conditions, what mathematical relationship and parameters
support a rate estimate?
```

EcoBiome must preserve that distinction in both data and code.
