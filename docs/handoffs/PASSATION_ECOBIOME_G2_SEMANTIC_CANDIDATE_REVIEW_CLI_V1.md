# EcoBiome — G2 Semantic Candidate Review CLI V1

**Date:** 2026-08-17
**Gate:** `G2_SEMANTIC_CANDIDATE_REVIEW_OPERATOR_WORKFLOW_V1`

## Goal

Close the operator-facing gap for human review of persisted Semantic Candidates
V2.11 without introducing a second review model or mutating candidate history.

## Canonical base

- `main`: `02539f7854f1cebdcf8b74c75c9abefd157df6b6`
- tree: `9ed11bf4c9f77043881fbf77c7629358ad6d5242`
- starting worktree: clean

## Existing primitives reused

G2 deliberately reuses the already-canonical scientific foundation:

- `SemanticCandidateReviewEventsRow`
- SQLite V6 `semantic_candidate_review_events`
- immutable `add_review_event(...)`
- ordered `list_review_events(...)`
- frozen `semantic_candidate_review_v1` policy
- V2.11 deterministic review text and candidate SHA binding

No SQLite schema or migration is added by G2.

## Operator commands

Under `ecobiome collector`:

- `semantic-candidate-list`
- `semantic-candidate-show`
- `semantic-candidate-review`

The review command uses the frozen decisions:

- `accept`
- `correct`
- `reject`

`correct` requires a distinct, already-persisted replacement candidate.

All commands require explicit paths for:

- scientific SQLite database;
- CAS root;
- repository root used by the persistence safety contract.

## Append-only invariant

Candidate review does not update or delete:

- `semantic_candidates`;
- previous `semantic_candidate_review_events`.

The integration test installs SQLite triggers that abort any UPDATE or DELETE on
both tables, then proves that:

1. list/show are read-only;
2. accept appends review event 1;
3. reject appends review event 2;
4. exact replay of event 2 is idempotent and does not add event 3;
5. the original candidate row is unchanged;
6. history remains ordered and complete.

## Scientific guardrails

- automatic scientific acceptance remains `False`;
- review events remain bound to exact candidate SHA;
- review text remains deterministic;
- policy identity remains frozen;
- correction lineage constraints remain enforced by the existing repository;
- no UI/CLI action rewrites scientific source history.

## Files in the G2 feature

1. `ROADMAP.md`
2. `src/ecobiome/knowledge_persistence/contracts.py`
3. `src/ecobiome/knowledge_persistence/sqlite_store.py`
4. `src/ecobiome/knowledge_acquisition/collector_cli.py`
5. `src/ecobiome/knowledge_acquisition/semantic_candidate_review_cli_v1.py`
6. `tests/test_semantic_candidate_review_cli_g2.py`
7. `docs/handoffs/PASSATION_ECOBIOME_G2_SEMANTIC_CANDIDATE_REVIEW_CLI_V1.md`

## Validation required

- `uv sync --locked`
- `uv run ruff check src tests`
- `uv run mypy src`
- targeted candidate-review/persistence tests
- full `uv run pytest -q`
- exact 7-path commit boundary
- feature branch push only
- remote `main` unchanged

## Roadmap note

The previous roadmap still referenced future V5 persistence work even though the
canonical repository already contains a physical Scientific Foundation V6.
After G2, G3 must first reconcile the roadmap with the canonical V6 code before
authorizing any new schema migration.
