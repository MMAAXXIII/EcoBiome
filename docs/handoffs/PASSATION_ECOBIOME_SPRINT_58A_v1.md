# PASSATION - EcoBiome Sprint 58A v1

## Status

Collector CLI baseline implemented locally on branch
`feature/collector-cli-baseline`.

No commit, push, pull request or merge has been performed.

## Decisions

- `src/ecobiome/knowledge_acquisition/` is the canonical Collector MVP seed.
- The central CLI and module entry point dispatch `import-transcript` before optional modules.
- The root `tests/` directory is the canonical Python test suite.
- Top-level analyzer and collector prototypes are removed.
- Security hardening tests remain in the canonical root suite.
- Tracked Python backup files are removed.
- Automatic YouTube retrieval, SQLite and human review remain deferred.

## Acceptance evidence

The Sprint 58A logs must contain:

- successful execution of the 13 canonical root tests;
- successful Ruff execution;
- successful mypy execution;
- successful `python -m ecobiome import-transcript` smoke test;
- zero tracked cache or backup artifacts;
- a corrected staged patch ready for review.

## Risks

- Other CLI commands still depend on unfinished simulation and reasoning code.
- Frontend and bolt-dashboard Python duplicates remain tracked.
- The transcript manifest is JSON-only and not persistent.
- Claims are not yet linked to exact evidence spans.

## Next sprint

Sprint 58B must add SQLite migrations and the human
accept/correct/reject workflow.

## Instruction to Codex or another implementation agent

Do not commit, push, merge or expand the scope without explicit authorization.
Do not add fabricated values, arbitrary confidence scores or audio fallback.
