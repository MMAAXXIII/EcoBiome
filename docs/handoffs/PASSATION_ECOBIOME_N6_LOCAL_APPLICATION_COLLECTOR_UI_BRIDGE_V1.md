# EcoBiome N6 — Local Application / Collector UI Bridge V1

Gate design:
`ECOBIOME_N6_LOCAL_APPLICATION_COLLECTOR_UI_BRIDGE_V1_DESIGN_FROZEN`

Candidate validation gate:
`ECOBIOME_N6_LOCAL_APPLICATION_COLLECTOR_UI_BRIDGE_V1_LOCAL_IMPLEMENTATION_VALIDATED`

## Baseline

- Repository: `MMAAXXIII/EcoBiome`
- Required local branch: `agent/n5-canonical-project-event-seam-v1`
- Required HEAD: `c2aa03cfb4a2707620e6da54b26fba12e795afcb`
- N4 aquarium / pond executable vertical slice: validated
- N5 Canonical Project Event Seam V1: locally validated and published in PR #11
- Scientific Foundation physical Schema V6: unchanged by N6 V1
- Collector compatibility schema: unchanged by N6 V1

## Purpose

N6 V1 turns the existing web dashboard into the first local-first EcoBiome
application slice that can be used without manually seeding Supabase.

The UI talks to a local FastAPI bridge. That bridge reuses the already
validated EcoBiome domain layers instead of creating a second scientific
model.

## V1 user flow

N6 V1 supports five user-visible actions:

1. create one aquarium or pond;
2. append a physical / chemical measurement;
3. view that measurement history from the canonical N5 project journal;
4. acquire one Collector source from a supported local path or YouTube URL;
5. inspect pending Collector review items and accept or reject them.

The existing Collector `propose_source_statement_claims` operation is exposed
for a persisted representation.

## Local-first persistence

Default runtime root:

`~/.ecobiome`

It may be overridden through:

`ECOBIOME_LOCAL_DATA_DIR`

Project layout:

```text
~/.ecobiome/
  projects/
    <project UUID>/
      metadata.json
      profile.json
      journal/
        events.jsonl
  collector/
    collector.sqlite
```

Runtime data is deliberately outside the Git repository.

## Aquarium / pond identity

The project UUID is the stable application identity and is also used as the
N4 `EcosystemProfileV1.id`.

N6 V1 creates the minimum valid N4 topology:

- one physical container structure;
- one `water_column` environment zone named `water`.

Aquaponic creation is not exposed in N6 V1 because N4 V1 admits only
`aquarium` and `pond` profile kinds. N6 must not silently coerce an aquaponic
system into another profile kind.

## Dynamic quantity boundary

N4 explicitly rejects dynamic quantities such as water volume, temperature,
pH, ammonia, nitrite and nitrate from topology.

Therefore N6 V1 stores:

- name and profile kind in the N4 topology;
- initial water volume as an N5 canonical observation;
- every UI measurement as an N5 canonical observation.

The UI projects canonical N5 observations back into display measurements.
The projection to JavaScript `number` is presentation-only; the durable
scientific payload remains the typed-decimal N5 event.

## Status semantics

A newly created aquatic project is returned as:

`status = "unknown"`

N6 V1 does **not** label a project as stable merely because no diagnostic
exists. Automatic ecological status requires a later explicit reasoning /
diagnostic bridge.

## Initial measurement set

N6 V1 admits UI entry for:

- water temperature;
- pH;
- ammonia / ammonium;
- nitrite;
- nitrate;
- dissolved oxygen;
- phosphate;
- iron;
- dissolved CO2.

GH / KH remain visible in the dashboard but are not writable through N6 V1.
Their exact scientific unit contract must be decided before durable entry is
enabled.

## Collector bridge

The FastAPI bridge directly reuses:

- `acquire_source`;
- `CollectorStore.summary`;
- `CollectorStore.list_pending_reviews`;
- `CollectorStore.propose_source_statement_claims`;
- `CollectorStore.record_review_decision`.

N6 V1 does not duplicate Collector persistence.

Local text-like source acquisition remains network-free. YouTube acquisition
may use the network only when the user explicitly submits a YouTube source.

Acquisition does not imply scientific acceptance.

Human review remains append-only through the existing Collector review
contract.

## Supabase boundary

The current UI hooks are moved away from mandatory direct Supabase reads for
the N6 slice.

Supabase remains installed but is not a runtime prerequisite for this local
application slice.

No cloud synchronization is introduced.

## API surface

Read/write project endpoints:

- `GET /api/health`
- `GET /api/water-bodies`
- `POST /api/water-bodies`
- `GET /api/water-bodies/{project_id}/measurements`
- `POST /api/water-bodies/{project_id}/measurements`
- `GET /api/measurements`
- `GET /api/water-bodies/{project_id}/organisms`

Read-only placeholders / projections:

- `GET /api/diagnostics`
- `GET /api/diagnostics/{diagnostic_id}/findings`
- `GET /api/media`
- `GET /api/journal`

Collector endpoints:

- `GET /api/collector/status`
- `POST /api/collector/acquire`
- `GET /api/collector/pending`
- `POST /api/collector/propose-claims`
- `POST /api/collector/review`

The legacy `/dashboard` FastAPI endpoint is preserved.

## UI changes

The web dashboard gains:

- functional `Nouveau milieu` / `Ajouter un milieu`;
- local aquarium / pond creation form;
- `Ajouter une mesure`;
- explicit `Non évalué` status;
- `Collector` navigation entry;
- source acquisition form;
- representation summary;
- `Proposer les claims`;
- pending human-review list;
- accept / reject controls.

## Intentionally out of scope

N6 V1 does not yet implement:

- organism editing;
- GH / KH canonical entry;
- automatic ecological diagnostics;
- simulation controls;
- water-exchange intervention form;
- media persistence;
- file-upload multipart transport;
- semantic provider execution from the UI;
- cloud / Supabase synchronization;
- PR #11 merge;
- any Git staging / commit / push.

## Candidate files

Modified:

- `backend/api.py`
- `bolt-dashboard/src/App.tsx`
- `bolt-dashboard/src/components/StatusBadge.tsx`
- `bolt-dashboard/src/lib/hooks.ts`
- `bolt-dashboard/src/lib/nav.ts`
- `bolt-dashboard/src/lib/types.ts`
- `bolt-dashboard/src/views/WaterBodiesView.tsx`

New:

- `bolt-dashboard/src/lib/api.ts`
- `bolt-dashboard/src/views/CollectorView.tsx`
- `tests/test_n6_local_app_bridge.py`
- `docs/handoffs/PASSATION_ECOBIOME_N6_LOCAL_APPLICATION_COLLECTOR_UI_BRIDGE_V1.md`

## Acceptance

The local implementation gate may be claimed only after:

- exact N5 branch / HEAD preflight;
- staging empty;
- expected tracked baseline hashes match;
- Python compile PASS;
- Ruff PASS for N6 Python files;
- Mypy PASS for `src` and `backend/api.py`;
- targeted N6 tests PASS;
- full pytest PASS;
- frontend `npm run build` PASS;
- frontend `npm run typecheck` PASS;
- `git diff --check` PASS;
- staging remains empty;
- only the expected N6 files differ from HEAD;
- no rollback was required.

Do not stage, commit, push, merge, or expand N6 scope without separate
authorization.
