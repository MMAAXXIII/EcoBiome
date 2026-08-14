# PASSATION — EcoBiome Collector v2 Core Integration v5

Date: 2026-08-11
Status: guarded local integration candidate
Git add/commit/push/merge authorized: NO
Network acquisition authorized: NO

## Delta versus v4

No architecture or runtime behavior change.

The only code correction is in `migration_v2.py`:

- rename the source metadata local variable to `source_metadata`;
- rename the claim metadata local variable to `claim_metadata`;
- keep `claim_metadata` typed as `dict[str, object]`.

Reason:
mypy v4 reported one `no-redef` error because the name `metadata`
was reused in the same migration function after its type had been
explicitly annotated.

## Previously validated in the real repository run

- 39/39 targeted Collector tests PASS
- `git diff --check` PASS
- Ruff PASS
- rollback of repository files PASS
- no Git write
- no network acquisition

## V5 gates

1. 39 targeted Collector tests
2. `git diff --check`
3. Ruff
4. mypy
5. full pytest

Expected final gate:

`COLLECTOR_V2_CORE_INTEGRATION_VALIDATED_LOCAL`

Do not implement Sprint B and do not commit/push until this gate is
reviewed.
