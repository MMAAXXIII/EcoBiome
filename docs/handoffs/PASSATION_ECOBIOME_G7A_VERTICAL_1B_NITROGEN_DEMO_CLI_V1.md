# PASSATION - EcoBiome G7A VERTICAL-1B - Nitrogen Demo CLI V1

**Gate:** `ECOBIOME_G7A_VERTICAL_1B_NITROGEN_DEMO_CLI_V1_LOCAL`
**Precondition:** `agent/g7a-directional-nitrogen-semantic-stack-v1@d5d7a7561fd332b7b1150467c058ecf5b743dc95`

## Purpose

Expose the validated VERTICAL-1A reproducible nitrogen artifact through one
minimal local product surface without adding kinetic semantics.

## User-visible command

```text
ecobiome nitrogen-demo --scientific-foundation <scientific-foundation-v6.sqlite3>
ecobiome nitrogen-demo --scientific-foundation <db> --format json
ecobiome nitrogen-demo --scientific-foundation <db> --output demo.md
```

The command is intentionally a frozen reviewed demonstration, not a general
simulation interface.

## Runtime boundary

`nitrogen_vertical_runtime_v1.py`:

- opens the supplied Scientific Foundation through SQLite `mode=ro`;
- enables `PRAGMA query_only=ON`;
- requires the exact reviewed V6 database SHA and design identity;
- reconstructs the exact MECH-5A state/evaluation chain;
- attaches the exact MECH-5B reviewed support receipts;
- requires the exact MECH-5A core trace SHA;
- requires the exact MECH-5B auditable explanation SHA;
- requires the exact VERTICAL-1A demonstration SHA.

The CLI therefore fails closed if scientific or provenance identity drifts.

## Non-goals

- no user-configurable kinetics;
- no `RateModel`;
- no dt or elapsed-time forecast;
- no persistence to Scientific Foundation V6;
- no Schema V7;
- no remote write;
- no generic demo framework.

## Product meaning

This is the first local EcoBiome command that exposes a complete vertical chain:

state -> deterministic process -> reviewed scientific support -> human-reviewed
attachment provenance -> explanation -> reproducible vertical artifact.

It remains a scenario demonstration because both process extents are explicit
inputs fixed at 1 mg N.

## Next boundary

After CLI validation, perform a focused usability/product audit of the rendered
nitrogen vertical. Only then decide whether the next step should be:

1. a small local visual/UI surface for the same frozen artifact; or
2. RateModel V1 design to replace explicit extents with scientifically grounded
   extent-over-dt calculation.

Do not start RateModel implementation merely because the CLI exists.
