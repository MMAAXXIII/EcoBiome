# Passation EcoBiome — Semantic Candidate V2.11 Phase A v1

## Status

Local implementation candidate only.

This phase implements the provider-neutral V2.11 semantic-candidate boundary
without changing Persistence Schema V4/V5 and without granting automatic
scientific acceptance.

## Frozen basis

- main base SHA: `6373f65a2b540457723fde8a2fe1ec29d9086ee6`
- relation/type basis: V2.10
- Claim/Evidence admission: V2.9
- deterministic grounding: V1.1 semantics with V1.2 role coverage
- scientific canonical serialization: Scientific Foundation V1.1

## Added implementation

`src/ecobiome/knowledge_acquisition/semantic_candidate_v2_11.py`

Provides:

- strict V2.11 candidate validation;
- provider-neutral canonical candidate SHA-256;
- exact numeric conversion from grounded source surfaces;
- no native float in the canonical candidate payload;
- controlled-unit canonicalization;
- opaque source-grounded text preservation without semantic-equivalence credit;
- Evidence-ID ordering and ownership revalidation;
- V2.10 relation/type/signature revalidation;
- canonical batch deduplication after V2.9 admission;
- deterministic, non-generative review-text rendering.

## Identity rule

`canonical_candidate_sha256` includes:

- V2.11 contract identity;
- V2.10 registry identity;
- grounding/provenance policy identities;
- source Claim ID and effective-text SHA-256;
- canonical Evidence-ID set;
- semantic type;
- relation;
- epistemic class;
- canonical typed arguments.

It excludes display-only `source_surface` fields.

Provider run IDs, request IDs, response IDs, timestamps and token usage are not
part of this candidate object or its identity.

## Numeric rule

Provider-native numeric values may arrive as JSON `number` before this boundary.

V2.11 canonical output never retains native `float`.

Resolved numeric values are reconstructed from deterministic source-grounding
records and emitted as:

- integer `{kind, value, source_surface}` for day indexes;
- decimal `{kind, value-as-canonical-string, source_surface}` for measured
  numeric values.

The implementation reuses Scientific Foundation V1.1 decimal normalization.

## Grounding rule

V2.11 is not entity resolution.

Opaque text remains:

`grounded_opaque_unresolved`

and produces:

`promotion_readiness = requires_semantic_resolution`.

Therefore:

`automatic_scientific_acceptance = false`

remains mandatory.

## Review renderer

The renderer is deterministic and non-generative.

Example:

`maintained_at(variable="Temperature", value=26.5, unit="celsius")`

No free LLM paraphrase is introduced at the review boundary.

## Tests

Targeted test file:

`tests/test_collector_semantic_candidate_v2_11.py`

Coverage includes:

- provider float -> exact decimal text;
- no native float in canonical payload;
- unit alias convergence;
- Evidence-order-independent identity;
- canonical post-admission deduplication;
- opaque role remains unresolved;
- deterministic review renderer;
- fail-closed relation rejection;
- argument-signature drift rejection;
- foreign Evidence rejection;
- native-float validator rejection;
- identity-tampering detection.

## Explicit non-scope

This phase does NOT:

- change SQLite Schema V4;
- implement Schema V5;
- create `semantic_candidates` persistence table;
- persist provider audit runs;
- implement scientific-assertion projection;
- implement entity resolution;
- stage files;
- commit;
- push;
- mutate GitHub.

## Next gate

After local validation succeeds:

`ECOBIOME_SEMANTIC_V2_11_PHASE_A_LOCAL_IMPLEMENTATION_COMPLETED`

Then perform a read-only review of:

- exact diff;
- full pytest;
- Ruff;
- mypy;
- dirty-tree preservation.

Staging requires a separate explicit authorization.
