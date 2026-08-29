# EcoBiome — Replay Manifest + Promotion Engine Candidate V1

Status: candidate pending human review
Gate: RATE-3C

Replay manifest:

```text
26f7a1f7b8cef2a6e7ad7e0f861a65fd12de89bace4270202447fe3b821e801a
```

Revised execution plan:

```text
db36828ab04b423e2ab39efaf59dd3cb45fe0f9a2446b298721c074e8c920997
```

Revised promotion-engine contract:

```text
9718cddf87622e0d1350279d37cbd28e12b19afd7e0c7a717c9816e5c2a7c788
```

## Dependency-closure correction

The exhaustive row manifest contains **32 promoted rows**.

It corrects the previous `knowledge_sources +2` expectation to:

```text
knowledge_sources +3
```

because `entity-identifier-pubchem-cid-946` binds:

```text
authority_source_id = authority-source-pubchem-cid-946
```

and that authority source is absent from the frozen V6 parent.

The correction is persistence dependency closure only; it does not add a new
scientific claim.

## Copyright/restricted-source boundary

The replay manifest stores the canonical SHA-256 of every complete database row
but does **not** commit the Nature paragraph text used by the two `segments`
rows.

Those two protected fields are reconstructed during a future authorized replay
from the exact CAS XML blobs and are checked against the already-frozen
representation/segment/evidence hashes before insertion.

## Derived CAS dependency

The two normalized JATS representations are deterministic derived artifacts.
RATE-3C computes and verifies their expected bytes read-only.

If absent from the canonical CAS, a future snapshot execution must receive
separate authorization to content-addressably materialize exactly those two
derived representation blobs before beginning the scientific SQLite
transaction.

## RATE-3B revisions implemented

1. Exhaustive row-by-row replay manifest with canonical row hashes.
2. Separate scientific-input, contract-commit, engine-commit and engine-code
   identities; exact post-commit values are bound in a second RATE-3C identity
   commit without modifying the candidate files.
3. Complete temporary DB+manifest publication with file/directory fsync and
   atomic directory rename; partial final directories fail closed.
4. Post-replay row-by-row canonical identity verification in addition to exact
   table deltas, `quick_check`, FK validation and full regression.

## Authorization boundary

RATE-3C only freezes candidate code/contracts:

```text
staging DB creation                 = false
scientific snapshot creation       = false
derived representation CAS writes  = false
active pointer update               = false
real V6 write                       = false
remote write                        = false
```

Next:

```text
RATE-3D — Replay Manifest + Promotion Engine Human Review
```
