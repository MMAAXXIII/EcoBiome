# EcoBiome — G3 Roadmap / Scientific Foundation V6 Reconciliation V1

**Date:** 2026-08-17
**Canonical base:** `main@e84f389cd3698328f0fee8f1907001ff808dad76`

## Goal

Reconcile the roadmap with the Scientific Foundation that is already canonical
in the repository.

This milestone is documentation/governance only. It does not add or alter a
SQLite table, index, migration, persistence row contract, Collector behavior or
scientific policy.

## G3 evidence

The read-only G3 audit proved:

- physical `SCHEMA_VERSION = 6`;
- 34 exact tables;
- 45 exact indexes;
- runtime design SHA-256
  `e0c732320b8bf901de3fd285ffcc41b74db8f1e0a227df89e0428e893e4f9181`;
- fresh-database schema tests: PASS;
- SQLite store tests: PASS;
- CAS tests: PASS;
- Semantic Candidate review tests: PASS;
- entity-resolution V6 tests: PASS;
- full suite: 435 passed, 1 skipped.

## Superseded roadmap assumptions

The previous roadmap still described future V5 work that already exists inside
the current V6 foundation.

### Old G4

`Schema V5 fresh-database + tests d'identité/intégrité`

Classification:

`SUPERSEDED_BY_V6 / DONE_AT_V6_LEVEL`

The V6 initializer, exact schema identity and integrity tests are canonical.

### Old G5

`Persistence provider-neutral semantic_candidates + reviews`

Classification:

`DONE`

Semantic Candidates and append-only review events are canonical and G2 added
the operator review surface.

### Old G6

`Persistence provider-run/origins/CAS`

Classification:

`PARTIAL`

The V6 physical structures exist and CAS behavior is tested. The next gate must
still prove the end-to-end Collector/provider-run/candidate-origin/CAS retention
path before this operational milestone is declared fully closed.

### Old G7

`Entity resolution + mappings reviewés`

Classification:

`PARTIAL`

V6 already includes persisted entity-resolution review events and tests. The
remaining gap is broader operator workflow and reviewed projection/mapping
coverage.

## New gate order

- G0 — done: Projection V1 review
- G1 — done: Projection V1 publication
- G2 — done: append-only Semantic Candidate human-review operator workflow
- G3 — done by this milestone: V6 consistency audit + roadmap reconciliation
- G4 — prove end-to-end provider-run/origins/CAS retention and Collector compatibility
- G5 — complete entity-resolution operator workflow and reviewed mappings
- G6 — extend reviewed projection mappings relation by relation
- G7 — vertical slice aquarium/mare “Pourquoi ça marche ?”
- G8 — user/sensor collectors + synthesis/trends
- G9 — simulation and integrated scientific UX

## Safety decision

Do not create Schema V7 merely because the old roadmap named V5 work as future.

A future schema version requires an independently demonstrated missing physical
invariant that cannot be represented safely by the current V6 contracts.
