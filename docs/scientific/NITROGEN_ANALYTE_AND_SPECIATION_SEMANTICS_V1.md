# EcoBiome — Nitrogen Analyte and Speciation Semantics V1

Status: scientific semantics background for RATE-1D
Persistence status: NOT part of Scientific Foundation V6
Implementation status: no speciation calculation

## 1. Purpose

This note documents the scientific terminology used by the RATE-1D state
design.

It is architecture/scientific background only. None of these references are
automatically promoted into Scientific Foundation V6.

## 2. Total ammonia nitrogen

The U.S. EPA freshwater ammonia criteria describe aqueous ammonia as the
equilibrium pair:

```text
NH4+ <-> NH3 + H+
```

and define total ammonia, commonly expressed on a nitrogen basis as total
ammonia nitrogen (TAN), as the sum of ionized ammonium and un-ionized ammonia.

EPA 2013 freshwater ammonia criteria:
https://www.epa.gov/sites/default/files/2015-08/documents/aquatic-life-ambient-water-quality-criteria-for-ammonia-freshwater-2013.pdf

Text version:
https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P100VT5L.TXT

RATE-1D therefore uses:

```text
TAN-N = NH3-N + NH4+-N
```

as the semantic partition identity.

## 3. Dependence of ammonia speciation on pH and temperature

EPA cites Emerson et al. (1975) for freshwater ammonia equilibrium
calculations and shows that the relative NH3/NH4+ fractions depend strongly on
pH and temperature.

Reference:

K. Emerson, R. C. Russo, R. E. Lund & R. V. Thurston (1975),
"Aqueous ammonia equilibrium calculations: effect of pH and temperature."

EPA HERO record:
https://hero.epa.gov/reference/36937/

RATE-1D does not implement the Emerson equation. It only records the semantic
requirement that an NH3/NH4+ partition needs explicit environmental inputs and
an applicability domain.

## 4. Ionic strength / salinity boundary

EPA's ammonia criteria note that ionic strength can alter the un-ionized
ammonia fraction, with effects generally small in most natural freshwater but
measurable in saline or very hard water.

EPA 1984 ammonia criteria:
https://www.epa.gov/sites/default/files/2019-02/documents/ambient-wqc-ammonia-1984.pdf

Therefore a future freshwater speciation model must state its ionic-strength
or salinity applicability rather than silently acting as a universal aqueous
model.

## 5. "As N" analytical basis

USGS water-quality records distinguish analytes explicitly on a nitrogen-mass
basis, including:

```text
ammonia (NH3 + NH4+), mg/L as nitrogen
nitrite, mg/L as nitrogen
nitrate + nitrite, mg/L as nitrogen
```

USGS 2026 analytical stability report:
https://pubs.usgs.gov/publication/sir20265014/full

USGS historical constituent table likewise lists dissolved ammonia and nitrite
as `MG/L AS N`:
https://water.usgs.gov/nwc/NWC/water_quality/tables/constituent.html

RATE-1D chooses `mg N` and `mg N/L` as the internal conservation and
concentration bases so nitrogen transfers remain dimensionally comparable.

## 6. DIN terminology

EPA's nutrient guidance notes that nitrate, nitrite and ammonia are commonly
reported together as dissolved inorganic nitrogen (DIN).

EPA nutrients reference:
https://www.epa.gov/caddis/nutrients

EcoBiome does not make DIN a fourth primary nitrogen inventory in RATE-1D.
It can only be a derived reporting aggregate over compatible underlying
quantities.

## 7. Species-mass reporting

An external method may report a concentration as mass of the ion or molecule
rather than as mass of nitrogen.

Those are not numerically interchangeable:

```text
mg N/L != mg NH4/L
mg N/L != mg NO2/L
mg N/L != mg NO3/L
```

RATE-1D requires the reporting basis to be explicit before normalization to
the internal elemental-N basis.

The deterministic molar-mass conversion itself belongs to a future input
normalization contract, not to RATE-1D.

## 8. Semantic consequence for the first kinetic model

The RATE-1B primary candidate uses TAN as its measured substrate.

Before any numerical coefficient from that study can be promoted, EcoBiome
must verify the paper's exact TAN definition, normalization and units against
the future canonical `total_ammonia_nitrogen` quantity.

The semantic bridge is therefore reviewed evidence, not a name-based
assumption.

## 9. Scientific boundary

RATE-1D authorizes terminology and state separation only.

It does not authorize:

- an ammonia equilibrium equation in production code;
- a pKa constant;
- a TAN-to-NH3 toxicity calculation;
- a nitrification rate law;
- a nitrite-oxidation rate law;
- any kinetic parameter;
- any Scientific Foundation V6 write.
