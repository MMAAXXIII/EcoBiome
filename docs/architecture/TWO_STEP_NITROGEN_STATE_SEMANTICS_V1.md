# EcoBiome — Two-step Nitrogen State Semantics V1

Status: adopted design decision
Gate: RATE-1D
Vertical: G7A nitrogen
Implementation status: design only; no state/material-balance code change

## 1. Objective

RATE-1B adopted the predictive nitrification target:

```text
ammonia/TAN-N -> nitrite-N -> nitrate-N
```

RATE-1C then added generic RateModel contracts without a concrete kinetic
formula.

RATE-1D defines the exact **state semantics** required before that two-step
vertical can become executable.

The central rule is:

> EcoBiome must conserve elemental nitrogen on one non-overlapping extensive
> inventory basis. Analytical aggregates, concentrations and acid/base species
> views must not be counted again as independent nitrogen stocks.

## 2. Canonical predictive nitrogen inventories

The first predictive nitrogen state uses three primary water-zone material
components:

```text
total_ammonia_nitrogen
nitrite_nitrogen
nitrate_nitrogen
```

Each primary inventory uses:

```text
variable_id = material_inventory
unit        = mg N
zone_id     = exact water zone
```

The `mg N` basis means mass of nitrogen atoms represented by the component,
not mass of NH3, NH4+, NO2- or NO3- ions/molecules.

### 2.1 total_ammonia_nitrogen

`total_ammonia_nitrogen` is the canonical extensive TAN-N pool.

For RATE-1D semantics:

```text
TAN-N = NH3-N + NH4+-N
```

within the same water zone and state instant.

It is an analytical/model aggregate over the two aqueous ammonia forms.
It is not a claim that TAN is one chemical entity.

### 2.2 nitrite_nitrogen

`nitrite_nitrogen` is the canonical extensive nitrite-N pool.

It is represented on an elemental-N mass basis for material conservation.
RATE-1D does not yet model free nitrous acid speciation separately.

### 2.3 nitrate_nitrogen

`nitrate_nitrogen` is the canonical extensive nitrate-N pool.

It is represented on the same elemental-N mass basis.

## 3. NH3-N and NH4+-N are derived partitions, not extra stocks

The following are **derived views** of `total_ammonia_nitrogen`:

```text
unionized_ammonia_nitrogen   # NH3-N
ammonium_nitrogen            # NH4+-N
```

In V1 they must never coexist as independently additive primary inventories
with TAN-N.

The conservation identity is:

```text
NH3-N + NH4+-N = TAN-N
```

not:

```text
TAN-N + NH3-N + NH4+-N
```

A future non-equilibrium ammonia-speciation model could choose a different
state representation, but that would require a new reviewed state-model
version. RATE-1D does not authorize it.

## 4. Concentrations are intensive projections

MaterialBalance operates on extensive inventories.

Concentrations required by a RateModel are derived from an exact inventory and
an exact water volume:

```text
concentration_as_N = material_inventory_mg_N / water_volume_L
```

with canonical concentration unit:

```text
mg N/L
```

For the predictive nitrogen state, candidate concentration projections are:

```text
TAN-N concentration
nitrite-N concentration
nitrate-N concentration
```

The concentration projection must retain provenance to:

- the exact input `EcosystemStateV1` SHA;
- the exact inventory quantity basis;
- the exact water-volume quantity basis;
- the deterministic projection definition/version.

No "typical aquarium volume" or implicit volume is allowed.

## 5. Observed concentration versus conserved inventory

Aquarium and laboratory measurements commonly enter EcoBiome as
concentrations rather than absolute inventories.

RATE-1D therefore freezes a source-of-truth rule:

> For a given semantic nitrogen pool, zone and logical state, EcoBiome may
> ingest an observed concentration and derive an inventory from exact water
> volume, or ingest an inventory and derive concentration, but it must not
> treat both as independent conserved amounts.

If both an observed concentration and an independently observed inventory are
available, they are separate evidence that must be reconciled or flagged; they
are not additive.

## 6. Analytical reporting basis is explicit

External measurements can be reported either:

```text
as elemental nitrogen
```

or as mass of the chemical ion/molecule.

Examples of distinct units/semantics include:

```text
mg N/L
mg NH3/L
mg NH4/L
mg NO2/L
mg NO3/L
```

RATE-1D forbids silently interpreting a species-mass result as `mg N/L`.

Any conversion to the canonical elemental-N basis must be an explicit,
auditable deterministic conversion tied to the exact reported analyte and
chemical identity.

This is especially important for aquarium test kits, whose displayed unit can
refer to the ion/molecule rather than nitrogen mass.

## 7. Ammonia speciation inputs

In freshwater, the partition between NH3 and NH4+ depends strongly on pH and
temperature. Ionic strength/salinity can also affect the equilibrium outside
the low-salinity freshwater domain.

A future `AmmoniaSpeciationModel` therefore requires, at minimum, exact:

```text
TAN-N
pH
temperature
```

and an explicit applicability statement concerning freshwater ionic
strength/salinity.

RATE-1D does not implement the equilibrium equation and does not persist an
equilibrium constant.

Missing pH or temperature means the NH3-N / NH4+-N partition is not evaluable.
There is no default pH or temperature.

## 8. Toxicity semantics and kinetic semantics remain separate

A future toxicity model may require the derived un-ionized ammonia view
`NH3-N`.

A future empirical nitrification RateModel may instead be defined directly on
TAN-N.

Those models must bind to the semantic quantity actually used by their
reviewed evidence.

EcoBiome must not substitute:

```text
TAN-N
NH3-N
NH4+-N
```

for one another merely because they refer to the same total ammonia system.

## 9. Two-step MaterialBalance target

A future material-balance revision may add exactly these predictive
transformations:

```text
total_ammonia_nitrogen -> nitrite_nitrogen
nitrite_nitrogen       -> nitrate_nitrogen
```

Both remain elemental-N transfers.

RATE-1D itself does not modify `_ALLOWED_NITROGEN_TRANSFORMATIONS` and does not
add a new evaluator.

## 10. Legacy G7A demonstration compatibility

The frozen demonstration currently uses process-scoped abstractions such as:

```text
reduced_inorganic_nitrogen
oxidized_inorganic_nitrogen
dissolved_inorganic_nitrogen
biological_nitrogen
```

RATE-1D does not rename or reinterpret those identifiers globally.

They remain valid for the frozen reviewed demonstration and its exact artifact
identity.

In particular:

- `reduced_inorganic_nitrogen` is not globally declared identical to TAN-N;
- `oxidized_inorganic_nitrogen` is not globally declared identical to
  nitrite-N or nitrate-N;
- `dissolved_inorganic_nitrogen` is not redefined as a global analytical DIN
  stock.

Any future bridge between a legacy abstraction and a predictive nitrogen
component must remain process/model scoped and separately reviewed.

## 11. DIN is an aggregate view, not a fourth primary inventory

For reporting, a dissolved inorganic nitrogen aggregate may be formed from
compatible dissolved ammonia, nitrite and nitrate quantities.

RATE-1D does not introduce a primary predictive component named
`dissolved_inorganic_nitrogen`, because doing so beside TAN-N, nitrite-N and
nitrate-N would create an overlapping inventory.

A DIN value, if exposed, must be a clearly derived aggregate.

## 12. State assembly invariants

A future predictive-state assembler must enforce:

1. primary nitrogen inventories use elemental-N units;
2. TAN-N, nitrite-N and nitrate-N are non-overlapping primary pools;
3. NH3-N and NH4+-N are partitions of TAN-N, not additional stocks;
4. concentrations are intensive views, not additional inventory;
5. species-mass versus "as N" reporting is explicit;
6. every derivation retains exact quantity provenance;
7. missing volume blocks concentration-to-inventory conversion;
8. missing pH/temperature blocks TAN speciation;
9. legacy process-scoped abstractions are not silently mapped globally;
10. no predictive nitrite dynamics are claimed until an explicit nitrite
    primary inventory exists.

## 13. Recommended next implementation order

```text
RATE-1D  state semantics design                    <- this gate
RATE-1E  canonical nitrogen state/projection code
RATE-1F  two-step MaterialBalance contracts
RATE-2A  kinetic evidence promotion/review
RATE-2B  first reviewed TAN-N -> nitrite-N RateModel
RATE-2C  explicit Δt integration
RATE-2D  predictive vertical + explanation/UI
```

RATE-1E may implement deterministic state/projection contracts only. It must
not introduce a kinetic coefficient or elapsed-time integration.
