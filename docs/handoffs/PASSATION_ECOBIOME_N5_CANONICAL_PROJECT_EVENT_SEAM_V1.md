# EcoBiome N5 — Canonical Project Observation / Intervention Seam V1

Gate design:
`ECOBIOME_N5_CANONICAL_PROJECT_EVENT_SEAM_V1_DESIGN_FROZEN`

Gate implementation:
`ECOBIOME_N5_CANONICAL_PROJECT_EVENT_SEAM_V1_LOCAL_IMPLEMENTATION_VALIDATED`

## Baseline

- Repository: `MMAAXXIII/EcoBiome`
- Branch: `main`
- Required HEAD: `95aea2aef2bd41b959c192afa9810bc729e0f71d`
- Parent: `156cffd68bdecb4f831ad37028ce499d0979d0da`
- N4 vertical slice: validated
- Scientific Foundation physical Schema V6: unchanged
- Collector compatibility schema 2: unchanged
- Projection V1.1: unchanged

## Decision

N5 does **not** introduce Scientific Foundation Schema V7.

Scientific Foundation V6 remains the durable knowledge/evidence database. Project observations
and interventions remain project chronology and are persisted through the existing append-only
journal transport (`journal/events.jsonl`).

The generic `JournalEvent.payload` is not declared scientific canonical storage because its
codec admits native floats. N5 introduces a strict canonical envelope above that transport.

## Scope

N5 V1 adds:

1. a tamper-evident `CanonicalProjectEventV1`;
2. a legacy `Observation` -> canonical project observation event adapter;
3. an N4 `WaterExchangeInterventionV1` -> canonical project intervention event adapter;
4. deterministic lexical unit normalization for the already-admitted N4 aliases;
5. projection to the existing `JournalEvent` JSONL transport;
6. fail-closed rehydration and verification;
7. an append/read `CanonicalProjectEventStoreV1` facade;
8. targeted tests and full regression validation.

N5 V1 supports project event types:
- `observation`
- `intervention`

It deliberately does not persist complete `EcosystemStateV1` snapshots or
`ProcessEvaluationV1` results yet.

## Canonical numeric boundary

N5 reuses Scientific Foundation canonical serialization:

- native `float` and raw `Decimal` are forbidden in canonical payloads;
- scientific decimal values are typed JSON objects:
  `{"type":"decimal","value":"..."}`;
- decimal text is normalized by the existing `normalize_decimal`;
- legacy observation floats are accepted only through the explicit N4 observation adapter;
- legacy observation confidence is frozen as a typed decimal string in `[0,1]`;
- `ScientificMeasurement.uncertainty` is preserved as a non-negative typed decimal rather
  than being lost at the N4 state-quantity seam;
- no Pint-based numeric conversion occurs at the N5 canonical boundary.

This avoids binary-float conversion drift while retaining the original measurement uncertainty
inside the durable observation event.

## Unit boundary

`canonicalize_unit_text_v1` performs lexical normalization only. It never changes numeric
magnitude.

Admitted N4 aliases include:

- `L`, `liter`, `litre` -> `L`
- `mL` -> `mL`
- `mg`, `g`
- `mg N`, `g N`
- `mg/L`, `g/L`
- `mg N/L`, `g N/L`
- `dimensionless`

Unknown non-empty units are preserved exactly after surrounding whitespace is stripped. They
are not silently converted or promoted into process-supported units.

Canonical observation quantities must already use the resulting canonical lexeme when read
back. The embedded N4 intervention payload is preserved exactly; N5 does not rewrite its unit
strings.

## Double identity model

### 1. Scientific payload identity

`canonical_payload_sha256` hashes the complete canonical observation/intervention payload.

### 2. Project event envelope identity

`canonical_event_sha256` hashes:

- event schema version;
- `project_id`;
- `event_id`;
- `event_type`;
- `occurred_at`;
- `subject_id`;
- payload schema version;
- `canonical_payload_sha256`.

This second identity prevents undetected alteration of project identity, occurrence time,
event type or subject while retaining the same scientific payload.

`recorded_at` is journal storage metadata and is intentionally excluded from scientific event
identity.

## Observation seam

`build_canonical_observation_event_v1`:

1. calls the existing `canonicalize_observation_v1`;
2. preserves the observation UUID as both `event_id` and observation subject identity;
3. preserves source, acquisition method, timestamp and raw reference;
4. stores confidence as normalized typed decimal and revalidates its `[0,1]` domain;
5. preserves `ScientificMeasurement.uncertainty` as normalized typed decimal when present;
6. carries N4 adapter warnings;
7. requires the resulting `CanonicalQuantityV1` basis to be `observation`;
8. requires the quantity basis reference to equal the observation UUID;
9. normalizes admitted unit aliases before hashing and rejects non-normalized aliases on read;
10. validates the acquisition-method enum on rehydration.

## Intervention seam

`build_canonical_water_exchange_event_v1`:

1. accepts only an N4 `WaterExchangeInterventionV1`;
2. embeds its complete canonical payload;
3. embeds and verifies the original N4 `intervention.canonical_sha256`;
4. reconstructs the embedded N4 intervention on read to enforce its contract;
5. keeps the N4 intervention `id` as the canonical subject identity;
6. adds explicit project event UUID and occurrence timestamp;
7. does not alter N4 process semantics or material-balance logic.

## Journal projection

A canonical N5 event projects to ordinary `JournalEvent` so existing JSONL persistence remains
usable.

The projection stores:

- the canonical tag `canonical-project-event-v1`;
- canonical schema/version attributes;
- both SHA-256 identities;
- the canonical payload as one **string** field `canonical_payload_json`.

No scientific native float is placed in the generic journal payload.

## Rehydration

`canonical_project_event_from_journal_event_v1` fails closed when:

- the canonical tag is absent when explicitly rehydrating;
- `project_id` is absent;
- required canonical attributes are absent;
- canonical JSON is syntactically invalid;
- canonical JSON is not byte-for-byte canonical text;
- native float/Decimal semantics would be required;
- payload SHA does not match;
- event-envelope SHA does not match;
- event/payload schema combinations are invalid;
- confidence, uncertainty, acquisition method or canonical unit constraints are invalid;
- observation identity/basis closure is invalid;
- N4 intervention reconstruction or SHA closure is invalid.

`CanonicalProjectEventStoreV1.all()` ignores unrelated generic journal events, but any event
claiming the canonical N5 tag must validate or the read fails.

## Files

New:

- `src/ecobiome/journal/canonical_project_event_v1.py`
- `tests/test_n5_canonical_project_event_v1.py`
- `docs/handoffs/PASSATION_ECOBIOME_N5_CANONICAL_PROJECT_EVENT_SEAM_V1.md`

Modified:

- `src/ecobiome/journal/__init__.py`

Protected and unchanged:

- `src/ecobiome/knowledge_persistence/sqlite_schema.py`
- `src/ecobiome/knowledge_persistence/collector_compat.py`
- `src/ecobiome/simulation/ecosystem_state_v1.py`
- `src/ecobiome/simulation/intervention_v1.py`
- `src/ecobiome/simulation/material_balance_v1.py`

## Targeted acceptance tests

N5 targeted tests prove at minimum:

1. observation canonical payload contains no native float after JSON parse;
2. measurement uncertainty is retained as typed decimal;
3. journal persistence round-trips canonical identity;
4. admitted unit aliases normalize before hashing;
5. canonical hashes are deterministic;
6. raw float injection is rejected;
7. payload SHA tampering is rejected;
8. non-canonical JSON text is rejected;
9. naive occurrence timestamps are rejected;
10. unrelated generic journal events are ignored by the canonical facade;
11. malformed events claiming the canonical tag fail closed;
12. N4 water-exchange SHA identity is preserved;
13. outer event metadata tampering is caught by the event-envelope SHA;
14. semantically invalid observation basis closure still fails after attacker-style rehashing.

## Validation policy

The launcher:

1. requires exact `main` HEAD and a clean working tree;
2. creates a disposable `git archive` shadow copy;
3. writes N5 candidate files only into the shadow;
4. validates syntax, Ruff, Mypy, targeted N5 tests, full pytest and Schema V6 identity;
5. verifies protected-file SHA-256 values remain unchanged;
6. only then writes the real working tree;
7. repeats the same validation locally;
8. runs `git diff --check`;
9. verifies staging remains empty and exactly the four expected N5 paths are dirty;
10. on any post-write failure restores the modified tracked file byte-for-byte and deletes only
    the newly created N5 paths;
11. creates a complete transcript/audit bundle outside the repository.

Validation runs `uv` in frozen/offline mode. No provider or network call is introduced by the
launcher.

## Protected operations

The launcher does not execute:

- `git add`
- `git commit`
- `git push`
- `git merge`
- `git rebase`
- `git reset`
- `git checkout`
- branch deletion
- GitHub metadata writes
- provider/model calls

Successful execution deliberately leaves N5 changes **unstaged** for independent review.

## Acceptance gate

The implementation gate may be claimed only when the runtime audit reports:

`ECOBIOME_N5_CANONICAL_PROJECT_EVENT_SEAM_V1_LOCAL_IMPLEMENTATION_VALIDATED`

and all shadow/local validation steps pass with protected boundaries unchanged.

## Candidate artifact identities at design freeze

- canonical module SHA-256: `7cbc765cd9428450c3f11a033c1690fc8bfa9752698b8ff7102eaef2aa0e2151`
- journal API replacement SHA-256: `9876c22ee4c233fb2a24d4a7d7cd3270d82d012c964b91962d442c894bf20597`
- targeted test SHA-256 (runtime Ruff-compatible revision): `bdc0d0fff02be4ede1a0cb76df9af3a77309ab3a5b32cc80a243d9c28e4f00d1`
- original design-freeze targeted test SHA-256: `289987796b96cd7c8f2bcc13c41040ac29c45ead6fa2e1a36bfb0f2eca857246`

Runtime audit correction note: the targeted test was revised only to satisfy Ruff `TRY004` and `DTZ001`; test intent, production code, scientific contracts, and N5 scope are unchanged.

Do not implement beyond this frozen scope without explicit authorization.
