# PASSATION — EcoBiome Collector Sprint B — Acquisition Framework + LocalFileAdapter v1

Date: 2026-08-11\
Status: local integration candidate\
Implementation target: `feature/collector-cli-baseline`\
Committed HEAD expected before integration: `feac99c11e4174178a88e2cba9038310776d0dfa`

## Authorization boundary

This Sprint B package does **not** authorize:

- `git add`;
- commit;
- push;
- merge;
- live HTTP;
- DNS;
- YouTube;
- PDF acquisition;
- OCR/STT/video analysis.

It implements a local-file-only acquisition pipeline above the validated Collector Core v2.

## Baseline

Sprint A reached:

`COLLECTOR_V2_CORE_INTEGRATION_VALIDATED_LOCAL`

Validated in the real EcoBiome repository:

- 39/39 Collector v2 targeted tests;
- `git diff --check`;
- Ruff;
- mypy on 180 source files;
- full pytest: 63 passed;
- no Git write;
- no network acquisition.

## Sprint B objective

Introduce the first real implementation of:

```text
collector acquire <source>
        |
        v
AdapterRegistry
        |
        v
LocalFileAdapter
        |
        v
staging
        |
        v
CollectorStore
        |
        +-- AcquisitionJob
        +-- Retrieval
        +-- RawArtifact
        +-- Representation
        +-- RepresentationDerivation
        +-- Segment
```

The architecture must remain source-agnostic so the next sprint can add a
YouTube adapter without adding YouTube-specific persistence branches.

## New modules

### `acquisition.py`

Defines:

- `AcquisitionRequest`;
- `AdapterMatch`;
- `CanonicalSource`;
- `AcquisitionDiagnostic`;
- `RetrievedPayload`;
- `RepresentationDraft`;
- `AcquisitionResult`;
- `AcquisitionContext`;
- `AcquisitionAdapter` Protocol;
- `AdapterRegistry`;
- staged-result validation.

Adapter priority is deterministic routing metadata, not confidence.

Equal highest priorities are an explicit error.

### `adapters/local_file.py`

The first adapter supports bounded UTF-8 text-like local files:

- `.txt`;
- `.md`;
- `.csv`;
- `.json`;
- `.xml`;
- `.html`;
- `.htm`.

It:

1. canonicalizes the local path to a file URI;
2. copies exact raw bytes into private staging;
3. enforces a maximum input byte limit;
4. decodes UTF-8 / UTF-8 BOM;
5. rejects binary-like NUL-containing files;
6. writes a derived normalized UTF-8 representation into staging;
7. returns provenance metadata.

It never opens SQLite and never writes canonical CAS paths.

### `collector_acquire.py`

Provides the orchestration layer:

1. build request;
2. deterministic adapter selection;
3. canonicalize;
4. create acquisition job;
5. allocate private staging;
6. call adapter;
7. validate staged result;
8. persist through `CollectorStore`;
9. finish job with status/diagnostics;
10. clean staging.

The default registry contains only `LocalFileAdapter`.

Therefore HTTP/YouTube inputs are explicitly unsupported in Sprint B and no
network access can occur through this framework.

## Persistence extension

`CollectorStore` gains source-agnostic methods:

- `begin_acquisition_job`;
- `finish_acquisition_job`;
- `persist_acquisition_result`.

Existing transcript APIs remain compatible.

Persistence guarantees for local acquisition:

- exact raw bytes -> global SHA-256 `RawArtifact`;
- every run -> distinct `AcquisitionJob`;
- every run -> distinct `Retrieval`;
- exact same content/source -> same Representation;
- exact re-acquisition preserves existing Segment review states;
- changed content at the same logical file URI -> new RawArtifact and
  Representation;
- derived representation bytes are stored under a separate `derived/`
  content-addressed namespace;
- derivation edge links the representation back to the raw artifact.

## CLI

New command:

```text
ecobiome collector acquire <source>
    --database <db>
    [--language <code>]
    [--maximum-input-bytes <bytes>]
    [--maximum-passage-characters <chars>]
    [--output <manifest.json>]
```

The manifest includes:

- selected adapter;
- canonical source;
- job;
- raw artifact IDs/hashes/paths;
- representation IDs/hashes/paths;
- duplicate status;
- segment IDs and review states;
- diagnostics.

## Required tests

Sprint B tests must prove:

1. highest-priority adapter selection;
2. equal-priority ambiguity fails;
3. HTTP input is unsupported without creating a DB/network operation;
4. local file persists full v2 provenance;
5. exact re-acquisition deduplicates content;
6. exact re-acquisition creates a new historical Retrieval/job;
7. review state survives exact re-acquisition;
8. changed file content creates a new snapshot under the same source;
9. binary-like text file fails and creates a failed job diagnostic;
10. oversized input fails before canonical persistence;
11. adapter output cannot escape staging;
12. unsupported local extension fails;
13. Windows drive paths route to LocalFileAdapter;
14. UNC/network paths are not routed as local acquisition;
15. CLI writes a complete acquisition manifest.

## Local synthetic pre-validation

Before packaging, the assembled Sprint A + Sprint B synthetic package passed:

`52 passed`

This is not a substitute for the real-repository quality gates.

## Real-repository acceptance gates

The guarded installer must run:

```text
targeted Collector tests
git diff --check
Ruff
mypy
full pytest
```

Expected final gate:

`COLLECTOR_ACQUIRE_LOCALFILE_VALIDATED_LOCAL`

## Next milestone

Only after this gate is reviewed:

Sprint C — YouTubeAdapter v1:

- strict YouTube URL allowlist;
- metadata via yt-dlp without media download;
- transcript/subtitle acquisition;
- manual/generated distinction;
- language selection;
- authoritative timecodes;
- no audio/STT fallback yet.

Do not implement Sprint C without explicit authorization.
## V2 correction after first guarded repository run

The first Sprint B integration attempt validated:

- 52/52 targeted tests;
- `git diff --check`;
- repository rollback after gate failure.

It stopped on one Ruff `I001` import-order finding in
`tests/test_collector_acquisition.py`.

V2 changes only the import ordering required by Ruff. There is no change to:

- acquisition semantics;
- adapter registry;
- LocalFileAdapter behavior;
- persistence/deduplication;
- security policy;
- schema v2;
- CLI behavior.

V2 must still pass the complete gate chain before Sprint B is accepted.
