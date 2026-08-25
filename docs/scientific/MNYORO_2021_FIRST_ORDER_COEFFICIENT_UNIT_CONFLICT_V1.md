# EcoBiome — Mnyoro 2021 First-order Coefficient Unit Conflict Review V1

Status: blocking scientific discrepancy
Gate: RATE-2A
Persistence status: NOT part of Scientific Foundation V6

## 1. Source

Mnyoro MS, Arvin E, Munubi RN, Chenyambuga SW, Pedersen L-F. (2021).

"Effect of water velocity on ammonium and nitrite removal in pilot scale fixed
bed biofilters."

Aquacultural Engineering 93, 102160.

DOI:
https://doi.org/10.1016/j.aquaeng.2021.102160

## 2. Conflicting representations

The publication exposes both of the following units for the same stated
first-order TAN surface-removal coefficient:

```text
0.45 m h^-1
0.45 m d^-1
```

The `m h^-1` form appears in the abstract and a results sentence.

The `m d^-1` form appears in the conclusion and Fig. 4 caption.

## 3. Dimensional audit

Equation (1) defines:

```text
STr = ([TAN]in - [TAN]out) * Q / Am
```

with:

```text
[TAN]  g N m^-3
Q      m^3 d^-1
Am     m^2
```

Therefore:

```text
STr = g N m^-2 d^-1
```

The regression slope is:

```text
STr / TAN
```

and therefore:

```text
(g N m^-2 d^-1) / (g N m^-3)
= m d^-1
```

`m d^-1` is dimensionally coherent with the defined quantities.

This dimensional result is evidence about consistency; it is not permission
for EcoBiome to silently edit the published source.

## 4. Promotion policy

The candidate parameter must be represented as:

```text
value = 0.45
unit = unresolved_source_conflict
promotion_status = blocked
```

until a human scientific review explicitly adopts a resolution.

An acceptable resolution record must contain:

```text
source DOI
conflicting passages
dimensional derivation
chosen canonical unit
reason for the choice
reviewer identity
review timestamp
review artifact SHA
```

## 5. Runtime consequence

Until the unit is resolved and promoted:

```text
RateParameterV1 for this coefficient = forbidden
applicable RateEvaluationV1 using this coefficient = forbidden
numeric TAN-removal rate from this model = forbidden
```

The generic RATE-1C contracts remain usable for other reviewed models.

## 6. No hidden conversion

EcoBiome must not:

- interpret `0.45 m/h` and convert it to `10.8 m/d`;
- interpret `0.45 m/d` and convert it to `0.01875 m/h`;
- select one form based only on convenience;
- average or otherwise reconcile the two values numerically.

The conflict is epistemic/source-level and must be resolved before numeric use.

## 7. Search status

RATE-2A located the peer-reviewed publication record, publisher abstract and
peer-reviewed accepted manuscript.

No correction or erratum resolving this unit discrepancy was identified in the
RATE-2A evidence search.

This statement records the search result for this gate; it is not a guarantee
that no correction can exist elsewhere.
